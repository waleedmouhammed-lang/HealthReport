from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]

STRAVA_AUTHORIZE_URL = "https://www.strava.com/oauth/authorize"
STRAVA_TOKEN_URL = "https://www.strava.com/oauth/token"
STRAVA_API_BASE_URL = "https://www.strava.com/api/v3"


@dataclass(frozen=True)
class AppPaths:
    project_root: Path
    data_dir: Path
    env_file: Path
    tokens_file: Path
    state_file: Path
    log_dir: Path
    output_dir: Path
    database_path: Path
    csv_path: Path
    excel_path: Path


def resolve_data_dir(data_dir: str | Path | None = None) -> Path:
    configured = data_dir or os.getenv("HEALTHREPORT_HOME")
    if configured:
        return Path(configured).expanduser().resolve()
    return PROJECT_ROOT


def get_paths(data_dir: str | Path | None = None) -> AppPaths:
    root = resolve_data_dir(data_dir)
    output_dir = root / "output"
    return AppPaths(
        project_root=PROJECT_ROOT,
        data_dir=root,
        env_file=root / ".env",
        tokens_file=root / "tokens.json",
        state_file=root / "state.json",
        log_dir=root / "logs",
        output_dir=output_dir,
        database_path=root / "healthreport.sqlite3",
        csv_path=output_dir / "strava_activities.csv",
        excel_path=output_dir / "strava_activities.xlsx",
    )


def ensure_runtime_dirs(paths: AppPaths) -> None:
    paths.data_dir.mkdir(parents=True, exist_ok=True)
    paths.log_dir.mkdir(parents=True, exist_ok=True)
    paths.output_dir.mkdir(parents=True, exist_ok=True)


# Compatibility constants for legacy imports.
_DEFAULT_PATHS = get_paths()
BASE_DIR = _DEFAULT_PATHS.data_dir
ENV_FILE = _DEFAULT_PATHS.env_file
TOKENS_FILE = _DEFAULT_PATHS.tokens_file
STATE_FILE = _DEFAULT_PATHS.state_file
LOG_DIR = _DEFAULT_PATHS.log_dir
OUTPUT_DIR = _DEFAULT_PATHS.output_dir
DB_PATH = _DEFAULT_PATHS.database_path
CSV_PATH = _DEFAULT_PATHS.csv_path
EXCEL_PATH = _DEFAULT_PATHS.excel_path
