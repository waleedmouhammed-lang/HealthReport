from __future__ import annotations

from typing import Any

import pandas as pd

TARGET_COLUMNS = {
    "id": "Activity ID",
    "name": "Activity Name",
    "sport_type": "Sport Type",
    "start_date_local": "Date",
    "distance": "Distance (km)",
    "moving_time": "Duration (min)",
    "elapsed_time": "Elapsed Time (min)",
    "average_speed": "Avg Pace (min/km)",
    "average_heartrate": "Avg Heart Rate",
    "max_heartrate": "Max Heart Rate",
    "total_elevation_gain": "Elevation Gain (m)",
    "calories": "Calories",
    "average_cadence": "Avg Cadence",
    "kudos_count": "Kudos Count",
}


def transform_activities(raw: list[dict[str, Any]]) -> pd.DataFrame:
    if not raw:
        return pd.DataFrame(columns=TARGET_COLUMNS.values())

    df = pd.json_normalize(raw)
    available = {k: v for k, v in TARGET_COLUMNS.items() if k in df.columns}
    df = df[list(available.keys())].rename(columns=available)

    if "Distance (km)" in df.columns:
        df["Distance (km)"] = (pd.to_numeric(df["Distance (km)"], errors="coerce") / 1000).round(2)
    if "Duration (min)" in df.columns:
        df["Duration (min)"] = (pd.to_numeric(df["Duration (min)"], errors="coerce") / 60).round(2)
    if "Elapsed Time (min)" in df.columns:
        df["Elapsed Time (min)"] = (pd.to_numeric(df["Elapsed Time (min)"], errors="coerce") / 60).round(2)

    if "Avg Pace (min/km)" in df.columns:
        speed = pd.to_numeric(df["Avg Pace (min/km)"], errors="coerce")
        pace = (1000 / speed.where(speed > 0) / 60).round(2)
        df["Avg Pace (min/km)"] = pace.fillna(0)

    if "Date" in df.columns:
        df["Date"] = pd.to_datetime(df["Date"], errors="coerce").dt.strftime("%Y-%m-%d")

    for col in ["Avg Heart Rate", "Max Heart Rate", "Calories", "Avg Cadence"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)

    if "Date" in df.columns:
        df = df.sort_values("Date", ascending=False).reset_index(drop=True)

    return df
