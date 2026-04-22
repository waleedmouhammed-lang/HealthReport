import time
import requests
from auth import get_valid_token

BASE_URL   = "https://www.strava.com/api/v3"
PER_PAGE   = 200
SLEEP_SEC  = 1  # Pause between pages to respect rate limits

def fetch_all_activities():
    """Fetch all activities from Strava with pagination"""
    token      = get_valid_token()
    headers    = {"Authorization": f"Bearer {token}"}
    activities = []
    page       = 1

    print("[fetch] Starting activity fetch...")

    while True:
        response = requests.get(
            f"{BASE_URL}/athlete/activities",
            headers=headers,
            params={"per_page": PER_PAGE, "page": page}
        )

        if response.status_code == 429:
            print("[fetch] Rate limit hit. Waiting 15 minutes...")
            time.sleep(900)
            continue

        if response.status_code != 200:
            raise Exception(f"[fetch] API error: {response.text}")

        batch = response.json()

        if not batch:
            print(f"[fetch] No more activities. Done at page {page - 1}.")
            break

        activities.extend(batch)
        print(f"[fetch] Page {page} — {len(batch)} activities fetched "
              f"(total so far: {len(activities)})")

        page += 1
        time.sleep(SLEEP_SEC)

    print(f"[fetch] Total activities fetched: {len(activities)}")
    return activities