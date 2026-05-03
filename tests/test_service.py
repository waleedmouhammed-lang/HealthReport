from pathlib import Path

import pandas as pd

from healthreport import service


def test_sync_activities_writes_database_state_and_exports(tmp_path, monkeypatch):
    raw = [
        {
            "id": 10,
            "name": "Walk",
            "sport_type": "Walk",
            "start_date": "2026-05-01T06:00:00Z",
            "start_date_local": "2026-05-01T08:00:00",
            "distance": 1000,
            "moving_time": 600,
            "elapsed_time": 700,
            "average_speed": 1.5,
            "total_elevation_gain": 4,
        }
    ]
    monkeypatch.setattr(service, "fetch_all_activities", lambda after_epoch=None, data_dir=None: raw)

    result = service.sync_activities(data_dir=str(tmp_path))

    assert result.fetched_count == 1
    assert result.total_count == 1
    assert (tmp_path / "healthreport.sqlite3").exists()
    assert (tmp_path / "state.json").exists()
    assert (tmp_path / "output" / "strava_activities.csv").exists()
    assert (tmp_path / "output" / "strava_activities.xlsx").exists()

    loaded = service.load_activities(data_dir=str(tmp_path))
    assert len(loaded) == 1
    assert loaded.loc[0, "Activity ID"] == 10


def test_load_activities_bootstraps_database_from_existing_csv(tmp_path):
    output = tmp_path / "output"
    output.mkdir()
    pd.DataFrame(
        [
            {
                "Activity ID": 99,
                "Date": "2026-05-02",
                "Distance (km)": 2.0,
            }
        ]
    ).to_csv(output / "strava_activities.csv", index=False)

    loaded = service.load_activities(data_dir=str(tmp_path))

    assert len(loaded) == 1
    assert loaded.loc[0, "Activity ID"] == 99
    assert Path(tmp_path / "healthreport.sqlite3").exists()
