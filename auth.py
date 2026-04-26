import os
import json
import time
import logging
import requests
from dotenv import load_dotenv
from config import ENV_FILE, TOKENS_FILE, STRAVA_TOKEN_URL

load_dotenv(ENV_FILE)

log = logging.getLogger(__name__)


def get_required_env(name):
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def load_tokens():
    """Load tokens from tokens.json"""
    if not TOKENS_FILE.exists():
        raise FileNotFoundError(
            f"{TOKENS_FILE} does not exist. Run `python tokens.py auth-url`, "
            "authorize Strava, then run `python tokens.py exchange <code>`."
        )
    with open(TOKENS_FILE, "r") as f:
        return json.load(f)


def save_tokens(tokens):
    """Save updated tokens back to tokens.json"""
    with open(TOKENS_FILE, "w") as f:
        json.dump(tokens, f, indent=2)


def get_valid_token():
    """Return a valid access token, refreshing it if expired"""
    tokens = load_tokens()

    # Check if token is expired (with 60s buffer)
    if time.time() >= tokens["expires_at"] - 60:
        log.info("[auth] Access token expired. Refreshing...")

        response = requests.post(STRAVA_TOKEN_URL, data={
            "client_id":     get_required_env("STRAVA_CLIENT_ID"),
            "client_secret": get_required_env("STRAVA_CLIENT_SECRET"),
            "refresh_token": tokens["refresh_token"],
            "grant_type":    "refresh_token"
        })

        if response.status_code != 200:
            raise Exception(f"[auth] Token refresh failed: {response.text}")

        new_tokens = response.json()
        tokens["access_token"] = new_tokens["access_token"]
        tokens["refresh_token"] = new_tokens["refresh_token"]
        tokens["expires_at"]   = new_tokens["expires_at"]
        save_tokens(tokens)
        log.info("[auth] Token refreshed and saved.")
    else:
        log.info("[auth] Token is valid. No refresh needed.")

    return tokens["access_token"]
