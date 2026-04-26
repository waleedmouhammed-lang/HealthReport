import time
import logging
import requests
from auth import get_valid_token
from config import STRAVA_API_BASE_URL

PER_PAGE   = 200
SLEEP_SEC  = 1  # Pause between pages to respect rate limits
log = logging.getLogger(__name__)


def fetch_all_activities(after_epoch=None):
    """Fetch Strava activities with pagination, optionally after a Unix timestamp."""
    token      = get_valid_token()
    headers    = {"Authorization": f"Bearer {token}"}
    activities = []
    page       = 1
    params     = {"per_page": PER_PAGE}

    if after_epoch:
        params["after"] = int(after_epoch)
        log.info("[fetch] Starting incremental activity fetch after %s.", after_epoch)
    else:
        log.info("[fetch] Starting full activity fetch...")

    while True:
        params["page"] = page
        response = requests.get(
            f"{STRAVA_API_BASE_URL}/athlete/activities",
            headers=headers,
            params=params
        )

        if response.status_code == 429:
            log.warning("[fetch] Rate limit hit. Waiting 15 minutes...")
            time.sleep(900)
            continue

        if response.status_code != 200:
            raise Exception(f"[fetch] API error: {response.text}")

        batch = response.json()

        if not batch:
            log.info("[fetch] No more activities. Done at page %s.", page - 1)
            break

        activities.extend(batch)
        log.info(
            "[fetch] Page %s - %s activities fetched (total so far: %s)",
            page,
            len(batch),
            len(activities),
        )

        page += 1
        time.sleep(SLEEP_SEC)

    log.info("[fetch] Total activities fetched: %s", len(activities))
    return activities
