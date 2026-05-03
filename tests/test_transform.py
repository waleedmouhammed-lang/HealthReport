import pandas as pd

from healthreport.transform import transform_activities


def test_transform_converts_units_and_handles_zero_speed():
    df = transform_activities(
        [
            {
                "id": 123,
                "name": "Morning Walk",
                "sport_type": "Walk",
                "start_date_local": "2026-05-01T08:00:00",
                "distance": 2500,
                "moving_time": 1800,
                "elapsed_time": 2100,
                "average_speed": 0,
                "average_heartrate": None,
                "max_heartrate": 140,
                "total_elevation_gain": 12.5,
            }
        ]
    )

    assert df.loc[0, "Activity ID"] == 123
    assert df.loc[0, "Distance (km)"] == 2.5
    assert df.loc[0, "Duration (min)"] == 30
    assert df.loc[0, "Elapsed Time (min)"] == 35
    assert df.loc[0, "Avg Pace (min/km)"] == 0
    assert df.loc[0, "Avg Heart Rate"] == 0
    assert df.loc[0, "Date"] == "2026-05-01"


def test_transform_empty_returns_expected_columns():
    df = transform_activities([])

    assert df.empty
    assert "Activity ID" in df.columns
    assert "Date" in df.columns
