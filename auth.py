import os
import json
import time
import logging
import requests
from dotenv import load_dotenv
from config import ENV_FILE, TOKENS_FILE, STRAVA_TOKEN_URL

load_dotenv(ENV_FILE)

log = logging.getLogger(__name__)

# The same function exists in the tokens.py script, but we want to avoid circular imports
#  so we duplicate it here.
def get_required_env(name):
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def load_tokens():
    """Load tokens from tokens.json"""

    # Checks the TOKENS_FILE existance before trying to read it,
    # and provides a helpful error message if it doesn't exist.
    if not TOKENS_FILE.exists():
        raise FileNotFoundError(
            f"{TOKENS_FILE} does not exist. Run `python tokens.py auth-url`, "
            "authorize Strava, then run `python tokens.py exchange <code>`."
        )
    # Read the file content and parse it as JSON, returning the tokens dictionary.
    with open(TOKENS_FILE, "r") as f:
        return json.load(f)

# This is the function responsible for saving the updated tokens back to the tokens.json file after refreshing.
def save_tokens(tokens):
    """Save updated tokens back to tokens.json"""

    # Write the updated tokens dictionary to the TOKENS_FILE in JSON format, with indentation for readability.
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

        # Storing the new tokens and the expiration time into new_tokens dictionary.
        new_tokens = response.json()

        tokens["access_token"] = new_tokens["access_token"]
        tokens["refresh_token"] = new_tokens["refresh_token"]
        tokens["expires_at"]   = new_tokens["expires_at"]

        # Saving the new tokens back to the tokens.json file using the save_tokens function.
        save_tokens(tokens)
        log.info("[auth] Token refreshed and saved.")
    else:
        # In case the token is still valid, we log that no refresh is needed.
        log.info("[auth] Token is valid. No refresh needed.")

    return tokens["access_token"]
