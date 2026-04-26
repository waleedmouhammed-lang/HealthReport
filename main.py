import json
import logging
from datetime import datetime

import pandas as pd

from config import CSV_PATH, LOG_DIR, STATE_FILE
from export import export_data
from fetch import fetch_all_activities
from transform import transform_activities


def setup_logging():
    LOG_DIR.mkdir(exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s  %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[
            logging.FileHandler(LOG_DIR / "sync.log", encoding="utf-8"),
            logging.StreamHandler(),
        ],
    )


setup_logging()
log = logging.getLogger(__name__)


def load_state():
    default_state = {
        "last_sync": None,
        "total_rows": 0,
        "last_activity_epoch": None,
        "last_activity_date": None,
    }

    if STATE_FILE.exists():
        with open(STATE_FILE, "r") as f:
            saved_state = json.load(f)
        return {**default_state, **saved_state}

    return default_state


def save_state(total_rows, last_activity_epoch=None, last_activity_date=None):
    with open(STATE_FILE, "w") as f:
        json.dump({
            "last_sync": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "total_rows": total_rows,
            "last_activity_epoch": last_activity_epoch,
            "last_activity_date": last_activity_date,
        }, f, indent=2)


def load_existing_export():
    if not CSV_PATH.exists():
        return pd.DataFrame()

    return pd.read_csv(CSV_PATH)


def infer_after_epoch(state, existing_df):
    if state.get("last_activity_epoch"):
        return int(state["last_activity_epoch"])

    if existing_df.empty or "Date" not in existing_df.columns:
        return None

    latest_date = pd.to_datetime(existing_df["Date"], errors="coerce").max()
    if pd.isna(latest_date):
        return None

    return int(latest_date.to_pydatetime().timestamp())


def latest_activity_metadata(raw, fallback_state):
    epochs = []
    dates = []

    for activity in raw:
        start_date = activity.get("start_date")
        start_date_local = activity.get("start_date_local")

        if start_date:
            parsed = pd.to_datetime(start_date, utc=True, errors="coerce")
            if not pd.isna(parsed):
                epochs.append(int(parsed.timestamp()))

        if start_date_local:
            parsed_local = pd.to_datetime(start_date_local, errors="coerce")
            if not pd.isna(parsed_local):
                dates.append(parsed_local.strftime("%Y-%m-%d %H:%M:%S"))

    last_epoch = max(epochs) if epochs else fallback_state.get("last_activity_epoch")
    last_date = max(dates) if dates else fallback_state.get("last_activity_date")
    return last_epoch, last_date


def latest_export_date(df):
    if df.empty or "Date" not in df.columns:
        return None

    latest_date = pd.to_datetime(df["Date"], errors="coerce").max()
    if pd.isna(latest_date):
        return None

    return latest_date.strftime("%Y-%m-%d")


def merge_activity_rows(existing_df, new_df):
    if existing_df.empty:
        merged = new_df.copy()
    elif new_df.empty:
        merged = existing_df.copy()
    else:
        merged = pd.concat([new_df, existing_df], ignore_index=True)

    if "Activity ID" in merged.columns:
        merged = merged.drop_duplicates(subset=["Activity ID"], keep="first")

    if "Date" in merged.columns:
        merged = merged.sort_values("Date", ascending=False)

    return merged.reset_index(drop=True)


def run():
    log.info("=" * 55)
    log.info("Strava Sync Pipeline - Starting")
    log.info("=" * 55)

    state = load_state()
    existing_df = load_existing_export()

    if state["last_sync"]:
        log.info("Last sync : %s", state["last_sync"])
        log.info("Rows then : %s", state["total_rows"])
    else:
        log.info("First run - fetching full activity history.")

    try:
        after_epoch = infer_after_epoch(state, existing_df)

        # Step 1 - Fetch
        log.info("--- FETCH ---")
        raw = fetch_all_activities(after_epoch=after_epoch)

        # Step 2 - Transform
        log.info("--- TRANSFORM ---")
        new_df = transform_activities(raw)
        merged_df = merge_activity_rows(existing_df, new_df)

        if merged_df.empty:
            log.info("No activities available to export. Exiting.")
            save_state(0)
            return

        # Step 3 - Export
        log.info("--- EXPORT ---")
        export_data(merged_df)

        # Step 4 - Save state
        last_epoch, last_date = latest_activity_metadata(raw, state)
        if not last_epoch:
            last_epoch = after_epoch
        if not last_date:
            last_date = latest_export_date(merged_df)
        save_state(len(merged_df), last_epoch, last_date)

        log.info("=" * 55)
        log.info(
            "Sync complete - %s total rows exported (%s new fetched).",
            len(merged_df),
            len(new_df),
        )
        log.info("=" * 55)

    except Exception as e:
        log.error("Pipeline failed: %s", e)
        raise


def main():
    run()


if __name__ == "__main__":
    main()
