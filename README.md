# SFU Canvas Academic Dashboard

A local-first starter project for a Canvas deadline/grade dashboard and Friday Markdown report. It uses read-only GET requests and does not send data to an AI provider.

## Requirements
- Python 3.10+
- Your SFU Canvas base URL (default shown below; confirm it matches the URL you use to sign in)
- A Canvas API token created and stored locally by you

## Setup (macOS)
1. Download and unzip this project. Keep the included hidden `.gitignore` and `.env.example` files.
2. Open Terminal and move into the project folder:
   `cd ~/Downloads/sfu_canvas_academic_dashboard`
3. Create a virtual environment and install dependencies:
   `python3 -m venv .venv`
   `source .venv/bin/activate`
   `pip install -r requirements.txt`
4. Copy `.env.example` to `.env`:
   `cp .env.example .env`
5. Open `.env` in a text editor on your computer. Set `CANVAS_BASE_URL` to the exact Canvas site you use and set `CANVAS_API_TOKEN` to your token. Do not paste the token into ChatGPT, email, GitHub, or a URL. Do not commit `.env`.
6. Test the report:
   `python weekly_report.py`
7. Start the dashboard:
   `streamlit run app.py`

## Token safety
A Canvas access token is similar to a password. Store it only on your own computer, keep `.env` private, and revoke the token in Canvas if it is exposed. The script uses the Authorization header over HTTPS and only calls GET endpoints. Use this only in accordance with SFU/Canvas policy. If API token creation is unavailable or prohibited, use Canvas exports instead.

### Before uploading changes
- The root `.gitignore` excludes local credentials, Streamlit secrets, private reports, logs, and Python environments. `.env.example` contains a placeholder only and is safe to share.
- Check `git status --short` before committing. Keep your real token in your local `.env` file.
- GitHub browser uploads and manually created ZIP files do not apply `.gitignore` automatically. Inspect every selected file and archive before uploading; exclude `.env`, secrets, private reports, and local environments.
- `.gitignore` does not remove files already committed or erase history. If a real token is ever exposed, revoke it in Canvas before cleaning up the repository.

## Friday automatic report (macOS)
The project includes `schedule_friday_macos.sh`. Review the paths in the script before running it. It installs a per-user `launchd` job to run the Markdown report each Friday at 3:00 PM in your Mac's local timezone. Your Mac must be awake and logged in; if you want it to run when your laptop is off, use a trusted always-on computer instead. To disable it, run:
`launchctl unload ~/Library/LaunchAgents/ca.sfu.canvas-weekly-report.plist`

## Notes and limitations
- Dashboard grades are Canvas-reported values and may not be final grades.
- Due-date overrides, external tools, unpublished grades, and special submission states may not be represented completely; verify important details in Canvas.
- Add lecture summaries to `notes/*.md`. This starter version does not download/parse every lecture file automatically.
- Reports are written to `reports/`. Keep this folder private if it contains grades or other personal information.
