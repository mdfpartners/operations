#!/usr/bin/env python3
"""QuickBooks Time → OneDrive Excel daily sync.

Usage
-----
python sync.py                        # pull yesterday
python sync.py --days 7               # pull last 7 days ending yesterday
python sync.py --days 7 --include-today  # pull last 7 days through today
python sync.py --dry-run              # preview without writing

Scheduling (cron – every day at 06:00)
---------------------------------------
0 6 * * * cd /path/to/quickbooks_onedrive_sync && python sync.py >> sync.log 2>&1
"""

from __future__ import annotations

import argparse
import os
import sys
from datetime import date

from dotenv import load_dotenv

from qb_time import QBTimeClient, date_range_for_days_back
from onedrive import OneDriveClient
from summaries import rebuild_summaries, _d

HEADER     = ["Date", "Customer", "Employee", "Hours"]
SHEET_NAME = "Raw Data"

EXPECTED_WEEKLY: dict[str, float] = {
    "Accel Entertainment":                       11,
    "Bethel Lutheran Church and School":         42,
    "Blunier Builders":                           4,
    "CTI":                                        6,
    "Contech Engineered Solutions":               6,
    "Convergint Technologies":                    2.5,
    "Emcor Facility Services":                    0.75,
    "IDNR Region V Office":                       2.5,
    "IUOE 649":                                   4,
    "Metamora Christian Union Church":            5.5,
    "Metamora Industries":                       13,
    "Midwest Multicare":                          3,
    "Morton Industries":                          8,
    "Office/Management Time":                    15,
    "Peoria County Veteran Assistance Commission": 1.8,
    "Peoria Park District":                       7.5,
    "Thermosystem, LLC":                          1.5,
    "Troxell Ins. / Summer & Associates":         4,
    "Winpak Heat Seal Corporation":              38,
    "Woodford County Health Department":         13,
    "Woodford County Sheriff's Office":          86.75,
}

EXPECTED_MONTHLY: dict[str, float] = {
    k: round(v * 52 / 12, 2) for k, v in EXPECTED_WEEKLY.items()
}

EXCLUDE_CUSTOMERS: set[str] = {"Unknown", "Logan Correctional Center", "Johnson Controls"}

# Expected hours per day of week per customer (0=Mon … 6=Sun).
# Accounts with alternating weekend days or irregular schedules are omitted
# (the tab will show actuals only for those).
EXPECTED_DAILY: dict[str, dict[int, float]] = {
    # User-specified schedule:
    "Bethel Lutheran Church and School": {0: 6,    1: 12,   2: 6,    3: 6,    4: 12  },
    # Derived from historical data:
    "Accel Entertainment":             {0: 2.8,  2: 3.7,  4: 3.3                   },
    "Blunier Builders":                {5: 4.0                                       },
    "Contech Engineered Solutions":    {0: 3.0,  3: 3.2                             },
    "CTI":                             {1: 1.5                                       },
    "IUOE 649":                        {1: 1.7,  6: 1.7                             },
    "Metamora Christian Union Church": {3: 5.6                                       },
    "Metamora Industries":             {1: 5.5,  3: 5.5                             },
    "Midwest Multicare":               {6: 2.7                                       },
    "Morton Industries":               {1: 3.75, 4: 3.75                            },
    "Peoria Park District":            {1: 4.25, 4: 4.0                             },
    "Thermosystem, LLC":               {0: 1.4                                       },
    "Winpak Heat Seal Corporation":    {0: 7.6,  1: 4.5,  2: 5.3,  3: 6.4, 4: 5.0 },
    "Woodford County Health Department":  {0: 2.5, 1: 2.5, 2: 2.5, 3: 2.5         },
    "Woodford County Sheriff's Office":   {0: 11.2, 1: 11.7, 2: 11.0, 3: 7.9,
                                           4: 6.6, 5: 2.7, 6: 3.2                  },
}


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Sync QuickBooks Time → OneDrive Excel")
    p.add_argument("--days", type=int,
                   default=int(os.environ.get("DEFAULT_DAYS_BACK", "1")))
    p.add_argument("--include-today", action="store_true")
    p.add_argument("--file", default=None)
    p.add_argument("--user-id", default=os.environ.get("ONEDRIVE_USER", "me"))
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--skip-duplicates", action="store_true", default=True)
    p.add_argument("--no-skip-duplicates", dest="skip_duplicates", action="store_false")
    return p.parse_args()


def _parse_for_summaries(raw_rows: list[list]) -> list[dict]:
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
    return [[ts["date"], ts["jobcode"], ts["user"], ts["hours"]] for ts in timesheets]


def main() -> None:
    load_dotenv()
    args = parse_args()

    start, end = date_range_for_days_back(args.days)
    if args.include_today:
        end = date.today()
    print(f"[sync] Pulling QuickBooks Time from {start} to {end} …")

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

    print("[sync] Connecting to OneDrive …")
    od = OneDriveClient()

    file_path = args.file or os.environ.get("ONEDRIVE_FILE_PATH")
    if not file_path:
        print("[error] No OneDrive file path set.", file=sys.stderr)
        sys.exit(1)

    user_id = args.user_id
    print(f"[sync] Resolving '{file_path}' in OneDrive ({user_id}) …")
    item_id = od.resolve_file_id(file_path, user_id=user_id)
    print(f"[sync] Found file (item ID: {item_id})")

    od.ensure_worksheet(user_id, item_id, SHEET_NAME)

    # Read sheet once — used for dedup check and in-memory summary rebuild
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
            print(f"[sync] Skipping {skipped} rows for dates already in spreadsheet: "
                  + ", ".join(already_present))
        rows = new_rows

    if not rows:
        print("[sync] All entries already present. Nothing new to write.")
        parsed = _parse_for_summaries(existing_data)
        od.open_workbook_session(user_id, item_id)
        try:
            rebuild_summaries(od, user_id, item_id, rows=parsed,
                              exp_weekly_override=EXPECTED_WEEKLY,
                              exp_monthly_override=EXPECTED_MONTHLY,
                              exclude_customers=EXCLUDE_CUSTOMERS,
                              expected_daily=EXPECTED_DAILY)
        finally:
            od.close_workbook_session(user_id, item_id)
        return

    print(f"[sync] Appending {len(rows)} rows to '{SHEET_NAME}' …")
    next_row = len(existing_data) + 2 if existing_data else 2
    if not existing_data:
        od.update_range(user_id, item_id, SHEET_NAME, "A1", [HEADER])
    od.update_range(user_id, item_id, SHEET_NAME, f"A{next_row}", rows)
    print(f"[sync] Done. Wrote rows starting at row {next_row}.")

    all_data = existing_data + rows
    parsed = _parse_for_summaries(all_data)
    od.open_workbook_session(user_id, item_id)
    try:
        rebuild_summaries(od, user_id, item_id, rows=parsed,
                          exp_weekly_override=EXPECTED_WEEKLY,
                          exp_monthly_override=EXPECTED_MONTHLY,
                          exclude_customers=EXCLUDE_CUSTOMERS)
    finally:
        od.close_workbook_session(user_id, item_id)


if __name__ == "__main__":
    main()
