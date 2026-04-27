# In case of importing the pathlib module, then we should utilize pl instance.
# import pathlib as pl

from pathlib import Path

# This in case we imported the pathlib module as pl.
# BASE_DIR = pl.Path.cwd()

# This is the starting point for the following directories and files.
BASE_DIR = Path.cwd()

# These files exist in the root directory of the project.
ENV_FILE = BASE_DIR / ".env"
TOKENS_FILE = BASE_DIR / "tokens.json"
STATE_FILE = BASE_DIR / "state.json"

# This is the directory where logs and output files will be stored.
LOG_DIR = BASE_DIR / "logs"
OUTPUT_DIR = BASE_DIR / "output"

# These are the paths for the output files CSV and EXCEL.
CSV_PATH = OUTPUT_DIR / "strava_activities.csv"
EXCEL_PATH = OUTPUT_DIR / "strava_activities.xlsx"

# These are the Strava API endpoints for authorization, token exchange, and API access.
STRAVA_AUTHORIZE_URL = "https://www.strava.com/oauth/authorize"
STRAVA_TOKEN_URL = "https://www.strava.com/oauth/token"
STRAVA_API_BASE_URL = "https://www.strava.com/api/v3"
