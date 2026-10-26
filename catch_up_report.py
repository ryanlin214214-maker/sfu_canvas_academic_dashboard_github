from datetime import datetime, timedelta
from pathlib import Path
import subprocess
import sys

BASE = Path(__file__).resolve().parent
REPORTS = BASE / "reports"
now = datetime.now().astimezone()

# Find the most recent Friday at 3:00 PM local time.
days_since_friday = (now.weekday() - 4) % 7
scheduled = (now - timedelta(days=days_since_friday)).replace(
    hour=15, minute=0, second=0, microsecond=0
)
if scheduled > now:
    scheduled -= timedelta(days=7)

reports = list(REPORTS.glob("weekly_report_*.md"))
if any(datetime.fromtimestamp(p.stat().st_mtime, now.tzinfo) >= scheduled
       for p in reports):
    print("A report already exists for this scheduled week; skipping.")
    sys.exit(0)

print("Generating the missed weekly report...")
subprocess.run(
    [sys.executable, str(BASE / "weekly_report.py")],
    cwd=BASE,
    check=True,
)
