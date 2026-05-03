from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from healthreport.config import get_paths
from healthreport.exceptions import StorageError
from healthreport.transform import TARGET_COLUMNS


def utc_now_string() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


class SQLiteActivityStore:
    def __init__(self, database_path: Path | None = None, data_dir: str | None = None) -> None:
        self.database_path = database_path or get_paths(data_dir).database_path
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.database_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _initialize(self) -> None:
        try:
            with self.connect() as conn:
                conn.executescript(
                    """
                    CREATE TABLE IF NOT EXISTS activities (
                        activity_id INTEGER PRIMARY KEY,
                        activity_json TEXT NOT NULL,
                        exported_json TEXT NOT NULL,
                        start_date TEXT,
                        start_date_local TEXT,
                        updated_at TEXT NOT NULL
                    );

                    CREATE TABLE IF NOT EXISTS sync_runs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        started_at TEXT NOT NULL,
                        completed_at TEXT,
                        status TEXT NOT NULL,
                        fetched_count INTEGER NOT NULL DEFAULT 0,
                        total_count INTEGER NOT NULL DEFAULT 0,
                        error TEXT
                    );

                    CREATE TABLE IF NOT EXISTS app_metadata (
                        key TEXT PRIMARY KEY,
                        value TEXT NOT NULL,
                        updated_at TEXT NOT NULL
                    );
                    """
                )
        except sqlite3.Error as exc:
            raise StorageError(f"Could not initialize SQLite database {self.database_path}: {exc}") from exc

    def count_activities(self) -> int:
        with self.connect() as conn:
            return int(conn.execute("SELECT COUNT(*) FROM activities").fetchone()[0])

    def get_metadata(self, key: str) -> str | None:
        with self.connect() as conn:
            row = conn.execute("SELECT value FROM app_metadata WHERE key = ?", (key,)).fetchone()
        return str(row["value"]) if row else None

    def set_metadata(self, key: str, value: Any) -> None:
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO app_metadata(key, value, updated_at)
                VALUES (?, ?, ?)
                ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_at = excluded.updated_at
                """,
                (key, str(value), utc_now_string()),
            )

    def record_sync_run(
        self,
        started_at: str,
        status: str,
        fetched_count: int = 0,
        total_count: int = 0,
        error: str | None = None,
    ) -> None:
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO sync_runs(started_at, completed_at, status, fetched_count, total_count, error)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (started_at, utc_now_string(), status, fetched_count, total_count, error),
            )

    def latest_sync_run(self) -> dict[str, Any] | None:
        with self.connect() as conn:
            row = conn.execute("SELECT * FROM sync_runs ORDER BY id DESC LIMIT 1").fetchone()
        return dict(row) if row else None

    def clear_activities(self) -> None:
        with self.connect() as conn:
            conn.execute("DELETE FROM activities")

    def upsert_activities(self, raw: list[dict[str, Any]], transformed_df: pd.DataFrame) -> int:
        if transformed_df.empty or "Activity ID" not in transformed_df.columns:
            return 0

        raw_by_id = {int(item["id"]): item for item in raw if item.get("id") is not None}
        rows = transformed_df.to_dict(orient="records")
        updated_at = utc_now_string()
        with self.connect() as conn:
            for row in rows:
                activity_id = int(row["Activity ID"])
                raw_activity = raw_by_id.get(activity_id, {})
                conn.execute(
                    """
                    INSERT INTO activities(activity_id, activity_json, exported_json, start_date, start_date_local, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                    ON CONFLICT(activity_id) DO UPDATE SET
                        activity_json = excluded.activity_json,
                        exported_json = excluded.exported_json,
                        start_date = excluded.start_date,
                        start_date_local = excluded.start_date_local,
                        updated_at = excluded.updated_at
                    """,
                    (
                        activity_id,
                        json.dumps(raw_activity, default=str),
                        json.dumps(row, default=str),
                        raw_activity.get("start_date") or row.get("Date"),
                        raw_activity.get("start_date_local") or row.get("Date"),
                        updated_at,
                    ),
                )
        return len(rows)

    def replace_activities(self, raw: list[dict[str, Any]], transformed_df: pd.DataFrame) -> int:
        with self.connect() as conn:
            conn.execute("DELETE FROM activities")
        return self.upsert_activities(raw, transformed_df)

    def import_exported_dataframe(self, df: pd.DataFrame) -> int:
        if df.empty or "Activity ID" not in df.columns:
            return 0
        rows = df.to_dict(orient="records")
        updated_at = utc_now_string()
        with self.connect() as conn:
            for row in rows:
                activity_id = int(row["Activity ID"])
                conn.execute(
                    """
                    INSERT OR IGNORE INTO activities(activity_id, activity_json, exported_json, start_date, start_date_local, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        activity_id,
                        "{}",
                        json.dumps(row, default=str),
                        row.get("Date"),
                        row.get("Date"),
                        updated_at,
                    ),
                )
        return len(rows)

    def load_activities(self) -> pd.DataFrame:
        with self.connect() as conn:
            rows = conn.execute("SELECT exported_json FROM activities").fetchall()
        records = [json.loads(row["exported_json"]) for row in rows]
        if not records:
            return pd.DataFrame(columns=TARGET_COLUMNS.values())
        df = pd.DataFrame(records)
        ordered = [column for column in TARGET_COLUMNS.values() if column in df.columns]
        extras = [column for column in df.columns if column not in ordered]
        df = df[ordered + extras]
        if "Date" in df.columns:
            df = df.sort_values("Date", ascending=False)
        return df.reset_index(drop=True)
