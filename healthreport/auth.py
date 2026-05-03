from __future__ import annotations

import os
import time
from typing import Any

import requests
from dotenv import load_dotenv

from healthreport.config import STRAVA_TOKEN_URL, get_paths
from healthreport.exceptions import AuthError, ConfigError
from healthreport.io_utils import atomic_write_json, read_json_file

TOKEN_TIMEOUT_SECONDS = 20


def load_environment(data_dir: str | None = None) -> None:
    load_dotenv(get_paths(data_dir).env_file)


def required_env(name: str, data_dir: str | None = None) -> str:
    load_environment(data_dir)
    value = os.getenv(name)
    if not value:
        raise ConfigError(f"Missing required environment variable: {name}")
    return value


get_required_env = required_env


def load_tokens(data_dir: str | None = None) -> dict[str, Any]:
    tokens_file = get_paths(data_dir).tokens_file
    if not tokens_file.exists():
        raise AuthError(
            f"{tokens_file} does not exist. Run `healthreport-strava-tokens auth-url`, "
            "authorize Strava, then run `healthreport-strava-tokens exchange <code>`."
        )
    try:
        tokens = read_json_file(tokens_file)
    except Exception as exc:
        raise AuthError(f"Could not read {tokens_file}: {exc}") from exc

    missing = [key for key in ("access_token", "refresh_token", "expires_at") if key not in tokens]
    if missing:
        raise AuthError(f"{tokens_file} is missing required token fields: {', '.join(missing)}")
    return tokens


def save_tokens(tokens: dict[str, Any], data_dir: str | None = None) -> None:
    atomic_write_json(get_paths(data_dir).tokens_file, tokens)


def get_valid_token(
    data_dir: str | None = None,
    session: requests.sessions.Session | None = None,
    now: float | None = None,
) -> str:
    tokens = load_tokens(data_dir)
    current_time = time.time() if now is None else now
    if current_time < int(tokens["expires_at"]) - 120:
        return str(tokens["access_token"])

    http = session or requests.Session()
    try:
        response = http.post(
            STRAVA_TOKEN_URL,
            data={
                "client_id": required_env("STRAVA_CLIENT_ID", data_dir),
                "client_secret": required_env("STRAVA_CLIENT_SECRET", data_dir),
                "refresh_token": tokens["refresh_token"],
                "grant_type": "refresh_token",
            },
            timeout=TOKEN_TIMEOUT_SECONDS,
        )
    except requests.RequestException as exc:
        raise AuthError(f"Token refresh request failed: {exc}") from exc

    if response.status_code != 200:
        raise AuthError(f"Token refresh failed ({response.status_code}): {response.text}")

    new_tokens = response.json()
    for key in ("access_token", "refresh_token", "expires_at"):
        if key not in new_tokens:
            raise AuthError(f"Token refresh response is missing `{key}`.")

    tokens.update(
        {
            "access_token": new_tokens["access_token"],
            "refresh_token": new_tokens["refresh_token"],
            "expires_at": new_tokens["expires_at"],
        }
    )
    save_tokens(tokens, data_dir)
    return str(tokens["access_token"])
