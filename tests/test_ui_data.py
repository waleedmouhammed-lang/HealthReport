import pandas as pd
import pytest

from healthreport.ui_data import clean_activity_data


def test_clean_activity_data_requires_expected_columns():
    with pytest.raises(ValueError):
        clean_activity_data(pd.DataFrame({"Date": ["2026-05-01"]}))


def test_clean_activity_data_parses_numbers_and_masks_zero_hr():
    df = pd.DataFrame(
        {
            "Date": ["2026-05-01"],
            "Distance (km)": ["2.5"],
            "Duration (min)": ["30"],
            "Elapsed Time (min)": ["32"],
            "Avg Pace (min/km)": ["12"],
            "Avg Heart Rate": ["0"],
            "Max Heart Rate": ["140"],
            "Elevation Gain (m)": ["10"],
        }
    )

    cleaned = clean_activity_data(df)

    assert cleaned.loc[0, "Distance (km)"] == 2.5
    assert pd.isna(cleaned.loc[0, "Avg Heart Rate"])
    assert cleaned.loc[0, "Max Heart Rate"] == 140
