import argparse
import json
import os
from urllib.parse import urlencode

import requests
from dotenv import load_dotenv

from config import ENV_FILE, STRAVA_AUTHORIZE_URL, STRAVA_TOKEN_URL, TOKENS_FILE


load_dotenv(ENV_FILE)


def required_env(name):
    """
        Helper function to get required environment variables,
        raising an error if missing.
        When I need to get an environment variable,
        I call this function to ensure that the python script fails
        with clear error message if the variable is not set.
    """
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def build_auth_url():
    params = {
        "client_id": required_env("STRAVA_CLIENT_ID"),
        "redirect_uri": required_env("STRAVA_REDIRECT_URI"),
        "response_type": "code",
        "approval_prompt": "auto",
        # The scope is stored in the .env file but default to "read,activity:read_all" if not set.
        "scope": os.getenv("STRAVA_SCOPE", "read,activity:read_all"),
    }
    # This replicates the manual step we did using the authorization URL in the browser.
    return f"{STRAVA_AUTHORIZE_URL}?{urlencode(params)}"


def exchange_code(code):
    response = requests.post(STRAVA_TOKEN_URL, data={
        "client_id": required_env("STRAVA_CLIENT_ID"),
        "client_secret": required_env("STRAVA_CLIENT_SECRET"),
        "code": code,
        "grant_type": "authorization_code",
    })

    if response.status_code != 200:
        raise RuntimeError(f"Token exchange failed: {response.text}")

    tokens = response.json()
    # Save the tokens to the local tokens.json file for use by other scripts.
    with open(TOKENS_FILE, "w") as f:
        json.dump(tokens, f, indent=2)

    return tokens


def main():
    """
        This script serves two main purposes:
        1. Generate the Strava authorization URL that the user can visit to authorize
          the app and obtain an authorization code.
        2. Exchange the obtained authorization code for access and refresh tokens,
        which are then saved to a local tokens.json file for use by other scripts in the project.
        --------------------------
        First, the user runs this script with the "auth-url" command to get the authorization URL.
        They visit that URL, authorize the app, and receive an authorization code from Strava.
        Then, they run this script again with the "exchange" command, providing the authorization code
        as an argument. The script exchanges the code for tokens and saves them locally.
    """
    parser = argparse.ArgumentParser(
        description="Create or refresh the local Strava tokens.json file."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("auth-url", help="Print the Strava authorization URL.")

    exchange_parser = subparsers.add_parser(
        "exchange",
        help="Exchange a Strava authorization code for tokens.json.",
    )
    exchange_parser.add_argument("code", help="Authorization code from Strava.")

    args = parser.parse_args()

    if args.command == "auth-url":
        print(build_auth_url())
        return

    if args.command == "exchange":
        tokens = exchange_code(args.code)
        expires_at = tokens.get("expires_at")
        print(f"Saved Strava tokens to {TOKENS_FILE}")
        if expires_at:
            print(f"Access token expires_at: {expires_at}")


if __name__ == "__main__":
    main()
