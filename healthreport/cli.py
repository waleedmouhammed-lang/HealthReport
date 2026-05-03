from __future__ import annotations

import argparse
import os

from healthreport.service import sync_activities


def main() -> None:
    parser = argparse.ArgumentParser(description="Sync Strava activities into HealthReport storage.")
    parser.add_argument("--full-refresh", action="store_true", help="Fetch all Strava activities and replace local activity storage.")
    parser.add_argument("--data-dir", help="Override the HealthReport data directory.")
    parser.add_argument("--no-export", action="store_true", help="Skip CSV/XLSX export after syncing.")
    args = parser.parse_args()

    if args.data_dir:
        os.environ["HEALTHREPORT_HOME"] = args.data_dir

    result = sync_activities(full_refresh=args.full_refresh, data_dir=args.data_dir, export=not args.no_export)
    print(f"Sync complete: {result.fetched_count} fetched, {result.total_count} total activities.")
    if result.exported_paths:
        for file_format, path in result.exported_paths.items():
            print(f"{file_format}: {path}")


if __name__ == "__main__":
    main()
