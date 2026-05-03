from __future__ import annotations

from pathlib import Path

import pandas as pd

from healthreport.config import get_paths
from healthreport.io_utils import atomic_write_csv, atomic_write_excel


def export_data(df: pd.DataFrame, data_dir: str | None = None, formats: tuple[str, ...] = ("csv", "xlsx")) -> dict[str, Path]:
    paths = get_paths(data_dir)
    exported: dict[str, Path] = {}
    if "csv" in formats:
        atomic_write_csv(paths.csv_path, df)
        exported["csv"] = paths.csv_path
    if "xlsx" in formats or "excel" in formats:
        atomic_write_excel(paths.excel_path, df)
        exported["xlsx"] = paths.excel_path
    return exported
