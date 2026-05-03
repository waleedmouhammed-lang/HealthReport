import pandas as pd

from healthreport.storage import SQLiteActivityStore


def test_sqlite_store_upserts_and_loads_activities(tmp_path):
    store = SQLiteActivityStore(tmp_path / "healthreport.sqlite3")
    raw = [
        {
            "id": 1,
            "start_date": "2026-05-01T06:00:00Z",
            "start_date_local": "2026-05-01T08:00:00",
        }
    ]
    df = pd.DataFrame(
        [
            {
                "Activity ID": 1,
                "Activity Name": "Walk",
                "Sport Type": "Walk",
                "Date": "2026-05-01",
                "Distance (km)": 3.2,
            }
        ]
    )

    assert store.upsert_activities(raw, df) == 1
    assert store.count_activities() == 1

    updated = df.copy()
    updated.loc[0, "Distance (km)"] = 4.1
    store.upsert_activities(raw, updated)

    loaded = store.load_activities()
    assert len(loaded) == 1
    assert loaded.loc[0, "Distance (km)"] == 4.1


def test_sqlite_store_records_metadata_and_sync_runs(tmp_path):
    store = SQLiteActivityStore(tmp_path / "healthreport.sqlite3")

    store.set_metadata("last_sync", "2026-05-03 11:00:00")
    store.record_sync_run("2026-05-03T09:00:00Z", "success", fetched_count=2, total_count=10)

    assert store.get_metadata("last_sync") == "2026-05-03 11:00:00"
    latest = store.latest_sync_run()
    assert latest["status"] == "success"
    assert latest["fetched_count"] == 2
    assert latest["total_count"] == 10
