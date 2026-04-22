import os
import json
import logging
from datetime import datetime
from fetch import fetch_all_activities
from transform import transform_activities
from export import export_data

# ─── Logger Setup ─────────────────────────────────────────────────────────────
os.makedirs("logs", exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.FileHandler("logs/sync.log"),
        logging.StreamHandler()
    ]
)
log = logging.getLogger()

# ─── State File (for incremental sync) ────────────────────────────────────────
STATE_FILE = "state.json"

def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    return {"last_sync": None, "total_rows": 0}

def save_state(total_rows):
    with open(STATE_FILE, "w") as f:
        json.dump({
            "last_sync":  datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "total_rows": total_rows
        }, f, indent=2)

# ─── Main Pipeline ─────────────────────────────────────────────────────────────
def run():
    log.info("=" * 55)
    log.info("Strava Sync Pipeline — Starting")
    log.info("=" * 55)

    state = load_state()
    if state["last_sync"]:
        log.info(f"Last sync : {state['last_sync']}")
        log.info(f"Rows then : {state['total_rows']}")
    else:
        log.info("First run — fetching full activity history.")

    try:
        # Step 1 — Fetch
        log.info("--- FETCH ---")
        raw = fetch_all_activities()

        if not raw:
            log.info("No activities returned. Exiting.")
            return

        # Step 2 — Transform
        log.info("--- TRANSFORM ---")
        df = transform_activities(raw)

        # Step 3 — Export
        log.info("--- EXPORT ---")
        export_data(df)

        # Step 4 — Save state
        save_state(len(df))

        log.info("=" * 55)
        log.info(f"Sync complete — {len(df)} total rows exported.")
        log.info("=" * 55)

    except Exception as e:
        log.error(f"Pipeline failed: {e}")
        raise

if __name__ == "__main__":
    run()