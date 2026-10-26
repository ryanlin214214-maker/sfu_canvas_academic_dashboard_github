import os
from datetime import datetime, timedelta
from pathlib import Path
import requests
from dotenv import load_dotenv

load_dotenv()
BASE = Path(__file__).parent
REPORTS = BASE / "reports"
NOTES = BASE / "notes"
REPORTS.mkdir(exist_ok=True)
NOTES.mkdir(exist_ok=True)

base_url = os.getenv("CANVAS_BASE_URL", "").strip().rstrip("/")
token = os.getenv("CANVAS_API_TOKEN", "").strip()
if not base_url or not token:
    raise SystemExit("Set CANVAS_BASE_URL and CANVAS_API_TOKEN in .env first.")

s = requests.Session()
s.headers.update({"Authorization": f"Bearer {token}", "Accept": "application/json"})

def get_all(path, params=None):
    url = f"{base_url}/api/v1/{path.lstrip('/')}"
    items = []
    while url:
        r = s.get(url, params=params, timeout=30)
        if r.status_code == 401:
            raise SystemExit("Canvas returned 401. Check token/domain and permissions.")
        r.raise_for_status()
        data = r.json()
        if not isinstance(data, list):
            return data
        items.extend(data)
        url = r.links.get("next", {}).get("url")
        params = None
    return items

now = datetime.now().astimezone()
end = now + timedelta(days=7)
courses = get_all("courses", {"enrollment_state": "active", "per_page": 100})
courses = [c for c in courses if c.get("name") and c.get("id")]
lines = [
    f"# SFU Weekly Academic Report — {now.strftime('%A, %B %d, %Y')}",
    "",
    f"Generated: {now.strftime('%Y-%m-%d %H:%M %Z')}",
    "",
    "## Executive summary",
    f"- Active courses returned by Canvas: **{len(courses)}**",
    "- This report is based on data available through the Canvas API. Verify special deadlines, accommodations, and submission states in Canvas.",
    "",
    "## Upcoming deadlines (next 7 days)",
]
deadline_count = 0
for c in courses:
    try:
        assignments = get_all(f"courses/{c['id']}/assignments", {"per_page": 100, "order_by": "due_at"})
    except requests.HTTPError:
        continue
    for a in assignments:
        due_raw = a.get("due_at")
        if not due_raw:
            continue
        try:
            due = datetime.fromisoformat(due_raw.replace("Z", "+00:00")).astimezone()
        except ValueError:
            continue
        if now.date() <= due.date() <= end.date():
            deadline_count += 1
            lines.append(f"- **{due.strftime('%a %b %d, %I:%M %p %Z')}** — {c.get('name')}: [{a.get('name','Untitled assignment')}]({a.get('html_url','')})")
if deadline_count == 0:
    lines.append("- No dated assignments found in the next seven days.")
lines += ["", "## Grades reported by Canvas", ""]
grade_count = 0
for c in courses:
    try:
        enrollments = get_all(f"courses/{c['id']}/enrollments", {"user_id": "self", "type[]": ["StudentEnrollment"], "per_page": 100})
    except requests.HTTPError:
        continue
    for e in enrollments:
        g = e.get("grades") or {}
        current = g.get("current_score")
        letter = g.get("current_grade")
        if current is not None or letter:
            lines.append(f"- **{c.get('name')}**: {current if current is not None else 'N/A'}% ({letter or 'letter grade unavailable'})")
            grade_count += 1
if grade_count == 0:
    lines.append("- No current grades were returned by Canvas for these courses.")
lines += ["", "## Lecture notes and concepts to review", ""]
note_files = sorted(NOTES.glob("*.md"))
if note_files:
    for p in note_files:
        lines += [f"### {p.stem.replace('_', ' ')}", p.read_text(encoding="utf-8").strip(), ""]
else:
    lines.append("No local notes found yet. Add course notes as Markdown files inside the `notes/` folder.")
lines += [
    "## Study plan for the next 7 days",
    "",
    "1. Confirm each deadline and submission status in Canvas.",
    "2. Complete the nearest due assignment first; split larger tasks into 30–60 minute blocks.",
    "3. Review lecture notes for the two least-confident topics in each course.",
    "4. Do practice problems without looking at solutions, then correct mistakes.",
    "5. On Friday, update notes and check the next week's deadlines.",
    "",
    "## Data limitations",
    "",
    "- Canvas may not expose all external-tool deadlines, unpublished grades, lecture videos, or special due-date overrides through the endpoints used here.",
    "- Grade values are displayed as Canvas reports them; they are not independently recalculated.",
    "- This starter script does not send your data to an AI service or email the report.",
]
out = REPORTS / f"weekly_report_{now.strftime('%Y-%m-%d')}.md"
out.write_text("\n".join(lines) + "\n", encoding="utf-8")
print(f"Saved report: {out}")
