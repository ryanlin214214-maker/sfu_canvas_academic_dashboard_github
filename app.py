import os
from datetime import datetime, timedelta
from pathlib import Path
import requests
import pandas as pd
import streamlit as st
from dotenv import load_dotenv

load_dotenv()
BASE_DIR = Path(__file__).parent
REPORTS = BASE_DIR / "reports"
NOTES_DIR = BASE_DIR / "notes"
REPORTS.mkdir(exist_ok=True)
NOTES_DIR.mkdir(exist_ok=True)

st.set_page_config(page_title="SFU Canvas Academic Dashboard", page_icon="🎓", layout="wide")
st.title("🎓 SFU Canvas Academic Dashboard")
st.caption("Local-first dashboard · Read-only Canvas API access")

canvas_url = os.getenv("CANVAS_BASE_URL", "").strip().rstrip("/")
token = os.getenv("CANVAS_API_TOKEN", "").strip()

if not canvas_url or not token:
    st.warning("Set CANVAS_BASE_URL and CANVAS_API_TOKEN in your local .env file, then restart the app.")
    st.code("CANVAS_BASE_URL=https://canvas.sfu.ca\nCANVAS_API_TOKEN=your_token_here", language="text")
    st.info("Never paste your token into ChatGPT, commit it to Git, or put it in a URL.")
    st.stop()

session = requests.Session()
session.headers.update({"Authorization": f"Bearer {token}", "Accept": "application/json"})

def get_all(path, params=None):
    url = f"{canvas_url}/api/v1/{path.lstrip('/')}"
    out = []
    while url:
        r = session.get(url, params=params, timeout=30)
        if r.status_code == 401:
            raise RuntimeError("Canvas returned 401: token invalid/expired or wrong Canvas domain.")
        r.raise_for_status()
        data = r.json()
        if isinstance(data, list):
            out.extend(data)
        else:
            return data
        url = r.links.get("next", {}).get("url")
        params = None
    return out

@st.cache_data(ttl=300, show_spinner=False)
def load_data(_base_url, _token):
    courses = get_all("courses", {"enrollment_state": "active", "per_page": 100})
    courses = [c for c in courses if c.get("name") and c.get("id")]
    assignments, grades, modules = [], [], []
    for c in courses:
        cid = c["id"]
        course_name = c.get("name", f"Course {cid}")
        try:
            aa = get_all(f"courses/{cid}/assignments", {"per_page": 100, "order_by": "due_at"})
            for a in aa:
                a["course_name"] = course_name
                a["course_id"] = cid
                assignments.append(a)
        except requests.HTTPError:
            pass
        try:
            enrollments = get_all(f"courses/{cid}/enrollments", {"user_id": "self", "type[]": ["StudentEnrollment"], "per_page": 100})
            for e in enrollments:
                grades.append({
                    "course_name": course_name,
                    "current_score": (e.get("grades") or {}).get("current_score"),
                    "current_grade": (e.get("grades") or {}).get("current_grade"),
                    "final_score": (e.get("grades") or {}).get("final_score"),
                    "final_grade": (e.get("grades") or {}).get("final_grade"),
                })
        except requests.HTTPError:
            pass
        try:
            mm = get_all(f"courses/{cid}/modules", {"per_page": 100})
            for m in mm:
                modules.append({"course_name": course_name, "module_name": m.get("name"), "items_count": m.get("items_count", 0)})
        except requests.HTTPError:
            pass
    return courses, assignments, grades, modules

if st.button("🔄 Refresh Canvas data"):
    st.cache_data.clear()
    st.rerun()

try:
    with st.spinner("Reading your Canvas courses..."):
        courses, assignments, grades, modules = load_data(canvas_url, token)
except Exception as e:
    st.error(f"Could not load Canvas data: {e}")
    st.caption("Check the Canvas domain and token permissions. Do not share the token to debug this.")
    st.stop()

now = datetime.now().astimezone()
today = now.date()
week_end = today + timedelta(days=7)
def due_dt(a):
    val = a.get("due_at")
    if not val: return None
    try: return datetime.fromisoformat(val.replace("Z", "+00:00")).astimezone()
    except ValueError: return None

rows = []
for a in assignments:
    due = due_dt(a)
    sub = a.get("submission") or {}
    submitted = sub.get("submitted_at") is not None
    rows.append({
        "Course": a.get("course_name"),
        "Assignment": a.get("name"),
        "Due": due.strftime("%a %b %d, %I:%M %p %Z") if due else ("No due date" if not a.get("due_at") else a.get("due_at")),
        "Due date": due.date().isoformat() if due else "",
        "Points": a.get("points_possible"),
        "Submitted": "Yes" if submitted else "No/unknown",
        "URL": a.get("html_url", ""),
        "_due": due,
        "_submitted": submitted,
    })
df = pd.DataFrame(rows)
if not df.empty:
    df_with_due_dates = df.dropna(subset=["_due"])
    upcoming = df_with_due_dates[
        df_with_due_dates["_due"].apply(
            lambda d: today <= d.date() <= week_end
        )
    ].sort_values("_due")
    overdue = df_with_due_dates[
        df_with_due_dates.apply(
            lambda row: row["_due"].date() < today and not row["_submitted"],
            axis=1,
        )
    ].sort_values("_due")
else:
    upcoming, overdue = pd.DataFrame(), pd.DataFrame()

c1, c2, c3, c4 = st.columns(4)
c1.metric("Active courses", len(courses))
c2.metric("Assignments listed", len(assignments))
c3.metric("Due in 7 days", len(upcoming))
c4.metric("Overdue / check", len(overdue))

tab1, tab2, tab3, tab4 = st.tabs(["Deadlines", "Grades", "Course modules", "Notes & study plan"])
with tab1:
    st.subheader("Due in the next 7 days")
    if upcoming.empty:
        st.success("No dated assignments found due in the next 7 days.")
    else:
        st.dataframe(upcoming.drop(columns=["_due", "_submitted", "Due date"], errors="ignore"), use_container_width=True, hide_index=True)
    st.subheader("Past-due items to check")
    if overdue.empty:
        st.info("No past-due items identified from the data retrieved. Check Canvas for items without due dates or special submission rules.")
    else:
        st.dataframe(overdue.drop(columns=["_due", "_submitted", "Due date"], errors="ignore"), use_container_width=True, hide_index=True)
    st.caption("Submission status may be unavailable on some course/assignment endpoints; verify uncertain items in Canvas.")
with tab2:
    st.subheader("Current grades reported by Canvas")
    gdf = pd.DataFrame(grades)
    if gdf.empty:
        st.info("No enrollment grades returned. Some courses may not publish grades through this endpoint.")
    else:
        st.dataframe(gdf, use_container_width=True, hide_index=True)
    st.caption("These are Canvas-reported grades, not a recalculation of final course grades.")
with tab3:
    st.subheader("Published course modules")
    mdf = pd.DataFrame(modules)
    if mdf.empty:
        st.info("No module data returned.")
    else:
        st.dataframe(mdf, use_container_width=True, hide_index=True)
with tab4:
    st.subheader("Add study notes")
    st.write("Write a plain-text or Markdown file in the `notes/` folder for each course. Use filenames like `CMPT_120.md`.")
    note_files = sorted(NOTES_DIR.glob("*.md"))
    if note_files:
        for p in note_files:
            with st.expander(p.name):
                st.markdown(p.read_text(encoding="utf-8"))
    else:
        st.info("No notes added yet. Lecture PDFs and slides are not automatically summarized by this starter version.")
    st.subheader("Suggested priorities")
    priorities = []
    if not overdue.empty:
        priorities.append(f"Check {len(overdue)} past-due item(s) in Canvas and confirm whether they are missing, submitted, or exempt.")
    if not upcoming.empty:
        first = upcoming.iloc[0]
        priorities.append(f"Start with the nearest deadline: {first['Assignment']} ({first['Course']}) due {first['Due']}.")
        priorities.append("Block study time for each upcoming assessment before starting optional review.")
    if not priorities:
        priorities.append("Review each course's next module, confirm upcoming dates, and add notes for difficult concepts.")
    for p in priorities:
        st.markdown(f"- {p}")

st.divider()
st.caption(f"Last loaded in this session: {now.strftime('%Y-%m-%d %H:%M %Z')}. Data is fetched from Canvas when refreshed.")
