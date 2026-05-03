from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd

from healthreport.client import fetch_all_activities
from healthreport.config import AppPaths, ensure_runtime_dirs, get_paths
from healthreport.exceptions import HealthReportError
from healthreport.export import export_data
from healthreport.io_utils import atomic_write_json, read_json_file
from healthreport.storage import SQLiteActivityStore, utc_now_string
from healthreport.transform import transform_activities

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class SyncResult:
    fetched_count: int
    total_count: int
    last_activity_epoch: int | None
    last_activity_date: str | None
    exported_paths: dict[str, Path]


def setup_logging(data_dir: str | None = None) -> None:
    paths = get_paths(data_dir)
    ensure_runtime_dirs(paths)
    if logging.getLogger().handlers:
        return
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s  %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[
            logging.FileHandler(paths.log_dir / "sync.log", encoding="utf-8"),
            logging.StreamHandler(),
        ],
    )


def default_state() -> dict[str, Any]:
    return {
        "last_sync": None,
        "total_rows": 0,
        "last_activity_epoch": None,
        "last_activity_date": None,
    }


def load_state(data_dir: str | None = None) -> dict[str, Any]:
    path = get_paths(data_dir).state_file
    if not path.exists():
        return default_state()
    try:
        state = read_json_file(path)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        log.warning("Ignoring invalid state file %s: %s", path, exc)
        return default_state()
    return {**default_state(), **state}


def save_state(
    total_rows: int,
    last_activity_epoch: int | None = None,
    last_activity_date: str | None = None,
    data_dir: str | None = None,
) -> None:
    atomic_write_json(
        get_paths(data_dir).state_file,
        {
            "last_sync": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "total_rows": total_rows,
            "last_activity_epoch": last_activity_epoch,
            "last_activity_date": last_activity_date,
        },
    )


def _latest_activity_metadata(raw: list[dict[str, Any]], fallback_state: dict[str, Any]) -> tuple[int | None, str | None]:
    epochs: list[int] = []
    dates: list[str] = []
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
    return (
        max(epochs) if epochs else fallback_state.get("last_activity_epoch"),
        max(dates) if dates else fallback_state.get("last_activity_date"),
    )


def _latest_export_date(df: pd.DataFrame) -> str | None:
    if df.empty or "Date" not in df.columns:
        return None
    latest_date = pd.to_datetime(df["Date"], errors="coerce").max()
    if pd.isna(latest_date):
        return None
    return latest_date.strftime("%Y-%m-%d")


def _bootstrap_database_from_csv(store: SQLiteActivityStore, paths: AppPaths) -> None:
    if store.count_activities() > 0 or not paths.csv_path.exists():
        return
    try:
        existing_df = pd.read_csv(paths.csv_path)
    except Exception as exc:
        log.warning("Could not bootstrap database from %s: %s", paths.csv_path, exc)
        return
    imported = store.import_exported_dataframe(existing_df)
    if imported:
        log.info("Imported %s existing CSV rows into SQLite.", imported)


def _infer_after_epoch(store: SQLiteActivityStore, state: dict[str, Any]) -> int | None:
    db_epoch = store.get_metadata("last_activity_epoch")
    if db_epoch:
        return int(db_epoch)
    if state.get("last_activity_epoch"):
        return int(state["last_activity_epoch"])
    return None


def load_activities(source: str = "database", data_dir: str | None = None) -> pd.DataFrame:
    paths = get_paths(data_dir)
    ensure_runtime_dirs(paths)
    if source == "csv":
        if not paths.csv_path.exists():
            return pd.DataFrame()
        return pd.read_csv(paths.csv_path)
    store = SQLiteActivityStore(paths.database_path)
    _bootstrap_database_from_csv(store, paths)
    return store.load_activities()


def export_reports(
    formats: tuple[str, ...] = ("csv", "xlsx"),
    data_dir: str | None = None,
) -> dict[str, Path]:
    df = load_activities(data_dir=data_dir)
    if df.empty:
        raise HealthReportError("No activities are available to export.")
    return export_data(df, data_dir=data_dir, formats=formats)


def sync_activities(
    full_refresh: bool = False,
    data_dir: str | None = None,
    export: bool = True,
) -> SyncResult:
    setup_logging(data_dir)
    paths = get_paths(data_dir)
    ensure_runtime_dirs(paths)
    store = SQLiteActivityStore(paths.database_path)
    _bootstrap_database_from_csv(store, paths)
    state = load_state(data_dir)
    started_at = utc_now_string()
    after_epoch = None if full_refresh else _infer_after_epoch(store, state)

    try:
        raw = fetch_all_activities(after_epoch=after_epoch, data_dir=data_dir)
        transformed_df = transform_activities(raw)
        if full_refresh:
            store.replace_activities(raw, transformed_df)
        else:
            store.upsert_activities(raw, transformed_df)

        all_df = store.load_activities()
        exported_paths = export_data(all_df, data_dir=data_dir) if export and not all_df.empty else {}

        last_epoch, last_date = _latest_activity_metadata(raw, state)
        if last_epoch is None:
            last_epoch = after_epoch
        if last_date is None:
            last_date = _latest_export_date(all_df)

        if last_epoch is not None:
            store.set_metadata("last_activity_epoch", last_epoch)
        if last_date is not None:
            store.set_metadata("last_activity_date", last_date)
        store.set_metadata("last_sync", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        store.set_metadata("total_rows", len(all_df))
        save_state(len(all_df), last_epoch, last_date, data_dir=data_dir)
        store.record_sync_run(started_at, "success", len(raw), len(all_df))

        return SyncResult(
            fetched_count=len(raw),
            total_count=len(all_df),
            last_activity_epoch=last_epoch,
            last_activity_date=last_date,
            exported_paths=exported_paths,
        )
    except Exception as exc:
        store.record_sync_run(started_at, "failed", 0, store.count_activities(), str(exc))
        log.exception("Sync failed.")
        raise


def get_status(data_dir: str | None = None) -> dict[str, Any]:
    paths = get_paths(data_dir)
    ensure_runtime_dirs(paths)
    store = SQLiteActivityStore(paths.database_path)
    _bootstrap_database_from_csv(store, paths)
    state = load_state(data_dir)
    latest_run = store.latest_sync_run()
    return {
        "data_dir": paths.data_dir,
        "database_path": paths.database_path,
        "csv_path": paths.csv_path,
        "excel_path": paths.excel_path,
        "tokens_configured": paths.tokens_file.exists(),
        "database_exists": paths.database_path.exists(),
        "total_rows": store.count_activities(),
        "last_sync": store.get_metadata("last_sync") or state.get("last_sync"),
        "last_activity_date": store.get_metadata("last_activity_date") or state.get("last_activity_date"),
        "latest_run": latest_run,
    }
