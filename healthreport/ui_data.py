from __future__ import annotations

from io import StringIO

import pandas as pd

REQUIRED_COLUMNS = [
    "Date",
    "Distance (km)",
    "Duration (min)",
    "Elapsed Time (min)",
    "Avg Pace (min/km)",
    "Avg Heart Rate",
    "Max Heart Rate",
    "Elevation Gain (m)",
]


def clean_activity_data(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = df.columns.str.strip().str.replace("\ufeff", "", regex=False)

    missing = [column for column in REQUIRED_COLUMNS if column not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {', '.join(missing)}")

    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df = df.dropna(subset=["Date"])

    numeric_columns = [
        "Distance (km)",
        "Duration (min)",
        "Elapsed Time (min)",
        "Avg Pace (min/km)",
        "Avg Heart Rate",
        "Max Heart Rate",
        "Elevation Gain (m)",
    ]
    for column in numeric_columns:
        df[column] = pd.to_numeric(df[column], errors="coerce")

    df["Avg Heart Rate"] = df["Avg Heart Rate"].mask(df["Avg Heart Rate"].eq(0))
    df["Max Heart Rate"] = df["Max Heart Rate"].mask(df["Max Heart Rate"].eq(0))
    return df.sort_values(by="Date", ascending=True).reset_index(drop=True)


def load_uploaded_data(uploaded_file) -> pd.DataFrame:
    stringio = StringIO(uploaded_file.getvalue().decode("utf-8-sig"))
    return clean_activity_data(pd.read_csv(stringio))
