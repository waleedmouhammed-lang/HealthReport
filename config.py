from pathlib import Path


BASE_DIR = Path.cwd()
ENV_FILE = BASE_DIR / ".env"
TOKENS_FILE = BASE_DIR / "tokens.json"
STATE_FILE = BASE_DIR / "state.json"
LOG_DIR = BASE_DIR / "logs"
OUTPUT_DIR = BASE_DIR / "output"
CSV_PATH = OUTPUT_DIR / "strava_activities.csv"
EXCEL_PATH = OUTPUT_DIR / "strava_activities.xlsx"

STRAVA_AUTHORIZE_URL = "https://www.strava.com/oauth/authorize"
STRAVA_TOKEN_URL = "https://www.strava.com/oauth/token"
STRAVA_API_BASE_URL = "https://www.strava.com/api/v3"
