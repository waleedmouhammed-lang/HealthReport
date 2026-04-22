import os
import json
import time
import requests
from dotenv import load_dotenv

load_dotenv()

TOKENS_FILE = "tokens.json"
TOKEN_URL   = "https://www.strava.com/oauth/token"

def load_tokens():
    """Load tokens from tokens.json"""
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
        print("[auth] Access token expired. Refreshing...")

        response = requests.post(TOKEN_URL, data={
            "client_id":     os.getenv("STRAVA_CLIENT_ID"),
            "client_secret": os.getenv("STRAVA_CLIENT_SECRET"),
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
        print("[auth] Token refreshed and saved.")
    else:
        print("[auth] Token is valid. No refresh needed.")

    return tokens["access_token"]