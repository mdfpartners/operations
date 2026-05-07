#!/usr/bin/env python3
"""QuickBooks Time → OneDrive Excel daily sync.

Usage
-----
# Pull yesterday (default)
python sync.py

# Pull the last N days
python sync.py --days 7

# Pull the last N days through today (inclusive)
python sync.py --days 7 --include-today

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
from summaries import rebuild_summaries, _d

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
        "--include-today",
        action="store_true",
        help="Extend the date range through today (default: end at yesterday)",
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


def _parse_for_summaries(raw_rows: list[list]) -> list[dict]:
    """Convert raw sheet rows [[date, customer, employee, hours], …] to summary dicts."""
    result = []
    for row in raw_rows:
        if not row or not row[0]:
            continue
        result.append({
            "date":    _d(row[0]).isoformat(),
            "jobcode": str(row[1]).strip() if len(row) > 1 and row[1] else "",
            "user":    str(row[2]).strip() if len(row) > 2 and row[2] else "",
            "hours":   float(row[3]) if len(row) > 3 and row[3] != "" else 0.0,
        })
    return result


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
    if args.include_today:
        end = date.today()
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

    # ── 5. Read existing sheet once (used for dedup check AND summaries) ──
    used = od.get_used_range(user_id, item_id, SHEET_NAME)
    existing_sheet = used.get("values", [])
    existing_data  = existing_sheet[1:] if len(existing_sheet) > 1 else []

    rows = rows_to_table(timesheets)

    if args.skip_duplicates:
        existing_dates: set[str] = set()
        for r in existing_data:
            if r and r[0]:
                try:
                    existing_dates.add(_d(r[0]).isoformat())
                except (ValueError, TypeError):
                    pass
        before = len(rows)
        new_rows = [r for r in rows if r[0] not in existing_dates]
        skipped = before - len(new_rows)
        if skipped:
            already_present = sorted({r[0] for r in rows if r[0] in existing_dates})
            print(
                f"[sync] Skipping {skipped} rows for dates already in spreadsheet: "
                + ", ".join(already_present)
            )
        rows = new_rows

    if not rows:
        print("[sync] All entries already present. Nothing new to write.")
        # Still rebuild summaries in case a previous run left them stale
        parsed = _parse_for_summaries(existing_data)
        rebuild_summaries(od, user_id, item_id, rows=parsed)
        return

    # ── 6. Append rows ────────────────────────────────────────────────────
    print(f"[sync] Appending {len(rows)} rows to '{SHEET_NAME}' …")
    next_row = len(existing_data) + 2 if existing_data else 2  # +1 for header, +1 for 1-based
    if not existing_data:
        od.update_range(user_id, item_id, SHEET_NAME, "A1", [HEADER])
    od.update_range(user_id, item_id, SHEET_NAME, f"A{next_row}", rows)
    print(f"[sync] Done. Wrote rows starting at row {next_row}.")

    # ── 7. Rebuild summaries from in-memory data (no second Graph read) ───
    all_data = existing_data + rows
    parsed = _parse_for_summaries(all_data)
    rebuild_summaries(od, user_id, item_id, rows=parsed)


if __name__ == "__main__":
    main()
