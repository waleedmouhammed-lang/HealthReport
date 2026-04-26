import logging

import pandas as pd

log = logging.getLogger(__name__)

TARGET_COLUMNS = {
    "id":                   "Activity ID",
    "name":                 "Activity Name",
    "sport_type":           "Sport Type",
    "start_date_local":     "Date",
    "distance":             "Distance (km)",
    "moving_time":          "Duration (min)",
    "elapsed_time":         "Elapsed Time (min)",
    "average_speed":        "Avg Pace (min/km)",
    "average_heartrate":    "Avg Heart Rate",
    "max_heartrate":        "Max Heart Rate",
    "total_elevation_gain": "Elevation Gain (m)",
    "calories":             "Calories",
    "average_cadence":      "Avg Cadence",
    "kudos_count":          "Kudos Count",
}


def transform_activities(raw):
    """Transform raw Strava JSON into a clean analysis-ready DataFrame"""
    if not raw:
        return pd.DataFrame(columns=TARGET_COLUMNS.values())

    df = pd.json_normalize(raw)

    # Keep only columns that exist in this dataset
    available = {k: v for k, v in TARGET_COLUMNS.items() if k in df.columns}
    df = df[list(available.keys())].rename(columns=available)

    # Unit conversions
    if "Distance (km)" in df.columns:
        df["Distance (km)"] = (df["Distance (km)"] / 1000).round(2)
    if "Duration (min)" in df.columns:
        df["Duration (min)"] = (df["Duration (min)"] / 60).round(2)
    if "Elapsed Time (min)" in df.columns:
        df["Elapsed Time (min)"] = (df["Elapsed Time (min)"] / 60).round(2)

    # Pace: convert speed (m/s) to min/km
    if "Avg Pace (min/km)" in df.columns:
        speed = pd.to_numeric(df["Avg Pace (min/km)"], errors="coerce")
        pace = (1000 / speed.where(speed > 0) / 60).round(2)
        df["Avg Pace (min/km)"] = pace.fillna(0)

    # Parse date
    if "Date" in df.columns:
        df["Date"] = pd.to_datetime(df["Date"]).dt.strftime("%Y-%m-%d")

    # Fill missing values
    for col in ["Avg Heart Rate", "Max Heart Rate", "Calories", "Avg Cadence"]:
        if col in df.columns:
            df[col] = df[col].fillna(0).astype(int)

    # Sort newest first
    if "Date" in df.columns:
        df = df.sort_values("Date", ascending=False).reset_index(drop=True)

    log.info(
        "[transform] Transformed %s activities into %s columns.",
        len(df),
        len(df.columns),
    )
    return df
