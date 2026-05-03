# HealthReport Strava App

Sync Strava activities into local SQLite storage, export CSV/XLSX reports, and inspect walking metrics in a Streamlit UI.

## Setup

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
cp .env.example .env
```

Fill `.env` with your Strava app values.

## First Strava Authorization

```bash
.venv/bin/python tokens.py auth-url
.venv/bin/python tokens.py exchange YOUR_CODE
```

This writes `tokens.json`, which is local runtime state and ignored by git.

## Run the App UI

```bash
scripts/run_dashboard.sh
```

The Streamlit UI lets you:

- Run `Sync Now` without manually running Python scripts.
- Refresh dashboard data.
- Export `output/strava_activities.csv` and `output/strava_activities.xlsx`.
- Upload a temporary CSV override for inspection.

## Manual CLI Sync

The UI is the normal way to run the app, but the CLI remains available:

```bash
.venv/bin/python main.py
.venv/bin/python main.py --full-refresh
.venv/bin/python main.py --no-export
```

Package entrypoints are also available after installation:

```bash
healthreport-sync
healthreport-strava-tokens auth-url
healthreport-strava-tokens exchange YOUR_CODE
```

## Daily 11 AM Sync on macOS

Install the LaunchAgent:

```bash
scripts/install_launchd.sh
```

The scheduled job runs `scripts/sync_only.sh` at 11:00 AM local time. It only pulls Strava data, updates SQLite, and writes exports. It does not open the browser or start/restart Streamlit.

To open the dashboard, run:

```bash
scripts/run_dashboard.sh
```

## Runtime Files

By default, runtime data lives in the project directory:

- `.env`
- `tokens.json`
- `state.json`
- `healthreport.sqlite3`
- `logs/`
- `output/`

Set `HEALTHREPORT_HOME=/path/to/data` to store runtime data elsewhere.

## Python API

The package-oriented API is available for future reuse:

```python
from healthreport import export_reports, load_activities, sync_activities

sync_activities()
df = load_activities()
export_reports()
```

## Verification

```bash
python3 -m py_compile main.py tokens.py walking_dashboard.py healthreport/*.py
pytest
```
