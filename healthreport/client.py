from __future__ import annotations

import time
from collections.abc import Callable
from typing import Any

import requests

from healthreport.auth import get_valid_token
from healthreport.config import STRAVA_API_BASE_URL
from healthreport.exceptions import StravaAPIError

PER_PAGE = 200
REQUEST_TIMEOUT_SECONDS = 30
PAGE_SLEEP_SECONDS = 1
RATE_LIMIT_SLEEP_SECONDS = 900
MAX_RETRIES = 3


def _request_page(
    session: requests.sessions.Session,
    headers: dict[str, str],
    params: dict[str, Any],
    sleep_func: Callable[[float], None],
) -> list[dict[str, Any]]:
    url = f"{STRAVA_API_BASE_URL}/athlete/activities"
    for attempt in range(MAX_RETRIES + 1):
        try:
            response = session.get(url, headers=headers, params=params, timeout=REQUEST_TIMEOUT_SECONDS)
        except requests.RequestException as exc:
            if attempt >= MAX_RETRIES:
                raise StravaAPIError(f"Strava request failed after retries: {exc}") from exc
            sleep_func(2**attempt)
            continue

        if response.status_code == 429:
            if attempt >= MAX_RETRIES:
                raise StravaAPIError("Strava rate limit persisted after retries.")
            retry_after = response.headers.get("Retry-After")
            sleep_func(float(retry_after) if retry_after else RATE_LIMIT_SLEEP_SECONDS)
            continue

        if 500 <= response.status_code < 600 and attempt < MAX_RETRIES:
            sleep_func(2**attempt)
            continue

        if response.status_code != 200:
            raise StravaAPIError(f"Strava API error ({response.status_code}): {response.text}")

        try:
            data = response.json()
        except ValueError as exc:
            raise StravaAPIError("Strava returned invalid JSON.") from exc
        if not isinstance(data, list):
            raise StravaAPIError("Strava activity response was not a list.")
        return data

    raise StravaAPIError("Strava request failed unexpectedly.")


def fetch_all_activities(
    after_epoch: int | None = None,
    data_dir: str | None = None,
    session: requests.sessions.Session | None = None,
    sleep_func: Callable[[float], None] = time.sleep,
    page_sleep_seconds: float = PAGE_SLEEP_SECONDS,
) -> list[dict[str, Any]]:
    token = get_valid_token(data_dir=data_dir, session=session)
    http = session or requests.Session()
    headers = {"Authorization": f"Bearer {token}"}
    params: dict[str, Any] = {"per_page": PER_PAGE}
    if after_epoch:
        params["after"] = int(after_epoch)

    activities: list[dict[str, Any]] = []
    page = 1
    while True:
        params["page"] = page
        batch = _request_page(http, headers, params, sleep_func)
        if not batch:
            break
        activities.extend(batch)
        page += 1
        sleep_func(page_sleep_seconds)
    return activities
