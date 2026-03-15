#!/usr/bin/env python3
"""QuickBooks Time → OneDrive Excel daily sync.

Usage
-----
# Pull yesterday (default)
python sync.py

# Pull the last N days
python sync.py --days 7

# Dry-run: print rows without writing to OneDrive
python sync.py --dry-run

# Override the OneDrive file path
python sync.py --file "Reports/My Time Report.xlsx"

# Target a specific OneDrive user (when running with tenant-wide app perms)
python sync.py --user-id me
python sync.py --user-id john@company.com

Scheduling (cron example – runs every day at 06:00)
----------------------------------------------------
0 6 * * * cd /path/to/quickbooks_onedrive_sync && python sync.py >> sync.log 2>&1
"""

from __future__ import annotations

import argparse
import os
import sys
from datetime import date, timedelta

from dotenv import load_dotenv

from qb_time import QBTimeClient, date_range_for_days_back
from onedrive import OneDriveClient
from summaries import rebuild_summaries

# Column layout — must match the Raw Data sheet exactly
HEADER = ["Date", "Customer", "Employee", "Hours"]

# Name of the worksheet to write into
SHEET_NAME = "Raw Data"


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Sync QuickBooks Time → OneDrive Excel")
    p.add_argument(
        "--days",
        type=int,
        default=int(os.environ.get("DEFAULT_DAYS_BACK", "1")),
        help="Number of days back to pull (default: 1 = yesterday)",
    )
    p.add_argument(
        "--file",
        default=None,
        help="OneDrive file path override (default: ONEDRIVE_FILE_PATH env var)",
    )
    p.add_argument(
        "--user-id",
        default=os.environ.get("ONEDRIVE_USER", "me"),
        help="OneDrive user UPN (default: ONEDRIVE_USER env var)",
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="Print rows that would be written without touching OneDrive",
    )
    p.add_argument(
        "--skip-duplicates",
        action="store_true",
        default=True,
        help="Skip dates that already exist in the sheet (default: true)",
    )
    p.add_argument(
        "--no-skip-duplicates",
        dest="skip_duplicates",
        action="store_false",
        help="Write all rows even if the date is already present",
    )
    return p.parse_args()


def rows_to_table(timesheets: list[dict]) -> list[list]:
    # Columns: Date, Customer (jobcode), Employee (user), Hours
    return [
        [ts["date"], ts["jobcode"], ts["user"], ts["hours"]]
        for ts in timesheets
    ]


def main() -> None:
    load_dotenv()
    args = parse_args()

    # ── 1. Build date range ────────────────────────────────────────────────
    start, end = date_range_for_days_back(args.days)
    print(f"[sync] Pulling QuickBooks Time from {start} to {end} …")

    # ── 2. Fetch timesheets ────────────────────────────────────────────────
    qb = QBTimeClient()
    timesheets = qb.get_timesheets(start, end)

    if not timesheets:
        print("[sync] No time entries found for the selected period. Nothing to do.")
        return

    print(f"[sync] Found {len(timesheets)} time entries.")

    if args.dry_run:
        print("\n[dry-run] Rows that would be written:")
        print("  " + " | ".join(HEADER))
        print("  " + "-" * 60)
        for row in rows_to_table(timesheets):
            print("  " + " | ".join(str(c) for c in row))
        return

    # ── 3. Connect to OneDrive ─────────────────────────────────────────────
    print("[sync] Connecting to OneDrive …")
    od = OneDriveClient()

    file_path = args.file or os.environ.get("ONEDRIVE_FILE_PATH")
    if not file_path:
        print(
            "[error] No OneDrive file path set. "
            "Use --file or set ONEDRIVE_FILE_PATH in .env",
            file=sys.stderr,
        )
        sys.exit(1)

    user_id = args.user_id
    print(f"[sync] Resolving '{file_path}' in OneDrive ({user_id}) …")
    item_id = od.resolve_file_id(file_path, user_id=user_id)
    print(f"[sync] Found file (item ID: {item_id})")

    # ── 4. Ensure the worksheet exists ────────────────────────────────────
    od.ensure_worksheet(user_id, item_id, SHEET_NAME)

    # ── 5. Optionally skip dates already in the sheet ─────────────────────
    rows = rows_to_table(timesheets)

    if args.skip_duplicates:
        unique_dates = list({row[0] for row in rows})
        already_present: set[str] = set()
        for d in unique_dates:
            hits = od.find_rows_by_date(user_id, item_id, SHEET_NAME, d)
            if hits:
                already_present.add(d)

        if already_present:
            before = len(rows)
            rows = [r for r in rows if r[0] not in already_present]
            skipped = before - len(rows)
            print(
                f"[sync] Skipping {skipped} rows for dates already in spreadsheet: "
                + ", ".join(sorted(already_present))
            )

    if not rows:
        print("[sync] All entries already present. Nothing new to write.")
        return

    # ── 6. Append rows ────────────────────────────────────────────────────
    print(f"[sync] Appending {len(rows)} rows to '{SHEET_NAME}' …")
    start_row = od.append_rows(user_id, item_id, SHEET_NAME, rows, header=HEADER)
    print(f"[sync] Done. Wrote rows starting at row {start_row}.")

    # ── 7. Rebuild all summary tabs from Raw Data ─────────────────────────
    rebuild_summaries(od, user_id, item_id)


if __name__ == "__main__":
    main()
