import pandas as pd

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
    df = pd.json_normalize(raw)

    # Keep only columns that exist in this dataset
    available = {k: v for k, v in TARGET_COLUMNS.items() if k in df.columns}
    df = df[list(available.keys())].rename(columns=available)

    # Unit conversions
    df["Distance (km)"]      = (df["Distance (km)"] / 1000).round(2)
    df["Duration (min)"]     = (df["Duration (min)"] / 60).round(2)
    df["Elapsed Time (min)"] = (df["Elapsed Time (min)"] / 60).round(2)

    # Pace: convert speed (m/s) to min/km
    df["Avg Pace (min/km)"] = (1000 / df["Avg Pace (min/km)"] / 60).round(2)

    # Parse date
    df["Date"] = pd.to_datetime(df["Date"]).dt.strftime("%Y-%m-%d")

    # Fill missing values
    for col in ["Avg Heart Rate", "Max Heart Rate", "Calories", "Avg Cadence"]:
        if col in df.columns:
            df[col] = df[col].fillna(0).astype(int)

    # Sort newest first
    df = df.sort_values("Date", ascending=False).reset_index(drop=True)

    print(f"[transform] Transformed {len(df)} activities into {len(df.columns)} columns.")
    return df