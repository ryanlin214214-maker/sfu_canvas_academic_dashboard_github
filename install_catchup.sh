#!/bin/bash
set -e

BASE="$HOME/Downloads/sfu_canvas_academic_dashboard"
PLIST="$HOME/Library/LaunchAgents/ca.sfu.canvas-weekly-report.plist"

# Back up the existing schedule.
cp "$PLIST" "$PLIST.backup"

# Build a LaunchAgent that checks at login and every Friday at 3 PM.
cat > "$PLIST" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>ca.sfu.canvas-weekly-report</string>
  <key>ProgramArguments</key>
  <array>
    <string>$BASE/.venv/bin/python</string>
    <string>$BASE/catch_up_report.py</string>
  </array>
  <key>WorkingDirectory</key>
  <string>$BASE</string>
  <key>RunAtLoad</key>
  <true/>
  <key>StartCalendarInterval</key>
  <dict>
    <key>Weekday</key>
    <integer>5</integer>
    <key>Hour</key>
    <integer>15</integer>
    <key>Minute</key>
    <integer>0</integer>
  </dict>
  <key>StandardOutPath</key>
  <string>$BASE/reports/scheduler.log</string>
  <key>StandardErrorPath</key>
  <string>$BASE/reports/scheduler-error.log</string>
</dict>
</plist>
EOF

plutil -lint "$PLIST"
launchctl bootout "gui/$(id -u)" "$PLIST" 2>/dev/null || true
launchctl bootstrap "gui/$(id -u)" "$PLIST"
echo "Catch-up schedule installed."
