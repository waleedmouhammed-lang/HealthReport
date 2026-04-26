# HealthReport Strava Sync

Sync Strava activities into local CSV and Excel reports.

## Setup

1. Create a virtual environment and install dependencies:

   ```bash
   python3 -m venv .venv
   .venv/bin/pip install -r requirements.txt
   ```

2. Copy `.env.example` to `.env` and fill in your Strava app values:

   ```bash
   cp .env.example .env
   ```

3. Generate a Strava authorization URL:

   ```bash
   .venv/bin/python tokens.py auth-url
   ```

4. Open the printed URL, authorize the app, then exchange the returned `code`:

   ```bash
   .venv/bin/python tokens.py exchange YOUR_CODE
   ```

This writes `tokens.json`, which is ignored by git.

## Manual Sync

Run:

```bash
.venv/bin/python main.py
```

The sync overwrites:

- `output/strava_activities.csv`
- `output/strava_activities.xlsx`
- `state.json`

New rows are merged with the existing export by `Activity ID`.

## Daily 10 AM Sync on macOS

Install the LaunchAgent:

```bash
scripts/install_launchd.sh
```

The scheduled run uses the same output files and state as manual runs, so there are no duplicate report files.
