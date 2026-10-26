#!/bin/bash
set -e
PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
PYTHON_PATH="$PROJECT_DIR/.venv/bin/python"
PLIST_DIR="$HOME/Library/LaunchAgents"
PLIST_PATH="$PLIST_DIR/ca.sfu.canvas-weekly-report.plist"
mkdir -p "$PLIST_DIR" "$PROJECT_DIR/reports"
if [ ! -x "$PYTHON_PATH" ]; then
  echo "Python venv not found. Follow README setup first."
  exit 1
fi
cat > "$PLIST_PATH" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key><string>ca.sfu.canvas-weekly-report</string>
  <key>ProgramArguments</key>
  <array>
    <string>$PYTHON_PATH</string>
    <string>$PROJECT_DIR/weekly_report.py</string>
  </array>
  <key>WorkingDirectory</key><string>$PROJECT_DIR</string>
  <key>StartCalendarInterval</key>
  <dict><key>Weekday</key><integer>5</integer><key>Hour</key><integer>15</integer><key>Minute</key><integer>0</integer></dict>
  <key>StandardOutPath</key><string>$PROJECT_DIR/reports/scheduler.log</string>
  <key>StandardErrorPath</key><string>$PROJECT_DIR/reports/scheduler-error.log</string>
</dict>
</plist>
EOF
launchctl unload "$PLIST_PATH" >/dev/null 2>&1 || true
launchctl load "$PLIST_PATH"
echo "Installed Friday 3:00 PM local-time report job: $PLIST_PATH"
