from __future__ import annotations

import argparse
import os
from urllib.parse import urlencode

import requests

from healthreport.auth import required_env
from healthreport.config import STRAVA_AUTHORIZE_URL, STRAVA_TOKEN_URL
from healthreport.exceptions import AuthError
from healthreport.io_utils import atomic_write_json
from healthreport.config import get_paths


def build_auth_url(data_dir: str | None = None) -> str:
    params = {
        "client_id": required_env("STRAVA_CLIENT_ID", data_dir),
        "redirect_uri": required_env("STRAVA_REDIRECT_URI", data_dir),
        "response_type": "code",
        "approval_prompt": "auto",
        "scope": os.getenv("STRAVA_SCOPE", "read,activity:read_all"),
    }
    return f"{STRAVA_AUTHORIZE_URL}?{urlencode(params)}"


def exchange_code(code: str, data_dir: str | None = None) -> dict:
    response = requests.post(
        STRAVA_TOKEN_URL,
        data={
            "client_id": required_env("STRAVA_CLIENT_ID", data_dir),
            "client_secret": required_env("STRAVA_CLIENT_SECRET", data_dir),
            "code": code,
            "grant_type": "authorization_code",
        },
        timeout=20,
    )
    if response.status_code != 200:
        raise AuthError(f"Token exchange failed ({response.status_code}): {response.text}")

    tokens = response.json()
    atomic_write_json(get_paths(data_dir).tokens_file, tokens)
    return tokens


def main() -> None:
    parser = argparse.ArgumentParser(description="Create the local Strava tokens.json file.")
    parser.add_argument("--data-dir", help="Override the HealthReport data directory.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("auth-url", help="Print the Strava authorization URL.")
    exchange_parser = subparsers.add_parser("exchange", help="Exchange a Strava authorization code.")
    exchange_parser.add_argument("code", help="Authorization code from Strava.")
    args = parser.parse_args()

    if args.data_dir:
        os.environ["HEALTHREPORT_HOME"] = args.data_dir

    if args.command == "auth-url":
        print(build_auth_url(args.data_dir))
        return

    tokens = exchange_code(args.code, args.data_dir)
    print(f"Saved Strava tokens to {get_paths(args.data_dir).tokens_file}")
    if tokens.get("expires_at"):
        print(f"Access token expires_at: {tokens['expires_at']}")


if __name__ == "__main__":
    main()
