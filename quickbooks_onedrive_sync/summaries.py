"""Rebuild all summary tabs from Raw Data.

Called automatically by sync.py after each Raw Data update.  All summary tabs
are fully recomputed from scratch so they stay in sync with Raw Data with no
manual intervention needed.

Tab layout
----------
Daily           – Customer × calendar-date grid (M/D column headers)
Weekly          – Customer × Saturday-to-Friday week
Monthly         – Customer × month (Jan 2026, …)
By Employee     – (Customer, Employee) × month, with "— All —" rollup rows
Recent (2 Weeks)– Customer × last-14-days daily grid
Weekly Variance – Customer × week, showing actual − expected_per_week
Monthly Variance– Customer × month, showing actual − expected_per_month
"""

from __future__ import annotations

from collections import defaultdict
from datetime import date, timedelta
from typing import Any

from onedrive import OneDriveClient

# ── date helpers ──────────────────────────────────────────────────────────────

def _d(val: Any) -> date:
    """Parse a date value that may be an ISO string or an Excel serial number."""
    if isinstance(val, (int, float)) and val > 40000:
        return date(1899, 12, 30) + timedelta(days=int(val))
    return date.fromisoformat(str(val))


def _month_key(d: date) -> int:
    """Ordinal month index (unique per year-month)."""
    return d.year * 12 + d.month - 1


def _month_key_to_date(key: int) -> date:
    return date(key // 12, key % 12 + 1, 1)


def _week_start(d: date) -> date:
    """Saturday that opens the Saturday-to-Friday week containing d."""
    return d - timedelta(days=(d.weekday() - 5) % 7)


def _daily_label(d: date) -> str:
    return f"{d.month}/{d.day}"


def _week_label(ws: date) -> str:
    we = ws + timedelta(days=6)
    return f"{ws.month}/{ws.day} - {we.month}/{we.day}"


def _month_label(d: date) -> str:
    return d.strftime("%b %Y")


# ── Raw Data reader ───────────────────────────────────────────────────────────

def read_raw_data(od: OneDriveClient, user_id: str, item_id: str) -> list[dict]:
    """Return all rows from the Raw Data sheet as a list of dicts."""
    used = od.get_used_range(user_id, item_id, "Raw Data")
    all_rows = used.get("values", [])

    rows: list[dict] = []
    for row in all_rows[1:]:   # row 0 is the header
        if not row or not row[0]:
            continue
        rows.append({
            "date":    _d(row[0]).isoformat(),
            "jobcode": str(row[1]).strip() if len(row) > 1 and row[1] else "",
            "user":    str(row[2]).strip() if len(row) > 2 and row[2] else "",
            "hours":   float(row[3]) if len(row) > 3 and row[3] != "" else 0.0,
        })
    return rows


# ── expected-hours reader (preserves col-B values on variance tabs) ───────────

def read_expected(
    od: OneDriveClient,
    user_id: str,
    item_id: str,
    sheet_name: str,
) -> dict[str, float]:
    """Return {customer: expected_value} from column B of a variance sheet."""
    used = od.get_used_range(user_id, item_id, sheet_name)
    result: dict[str, float] = {}
    for row in used.get("values", [])[1:]:
        if not row or not row[0] or str(row[0]) == "TOTAL":
            continue
        if len(row) > 1 and row[1] != "":
            try:
                result[str(row[0]).strip()] = float(row[1])
            except (ValueError, TypeError):
                pass
    return result


# ── table builders ────────────────────────────────────────────────────────────

def _r(val: float) -> Any:
    """Round to 2 dp; return '' for zero so cells stay clean."""
    v = round(val, 2)
    return v if v else ""


def build_daily(rows: list[dict]) -> list[list]:
    dates     = sorted({r["date"] for r in rows})
    customers = sorted({r["jobcode"] for r in rows if r["jobcode"]})

    data: dict[tuple, float] = defaultdict(float)
    for r in rows:
        if r["jobcode"]:
            data[(r["jobcode"], r["date"])] += r["hours"]

    header = ["Customer"] + [_daily_label(_d(d)) for d in dates]
    out    = [header]
    totals = [0.0] * len(dates)

    for c in customers:
        row: list[Any] = [c]
        for i, d in enumerate(dates):
            h = round(data[(c, d)], 2)
            row.append(h if h else "")
            totals[i] += h
        out.append(row)

    out.append(["TOTAL"] + [_r(t) for t in totals])
    return out


def build_weekly(rows: list[dict]) -> list[list]:
    customers   = sorted({r["jobcode"] for r in rows if r["jobcode"]})
    week_starts = sorted({_week_start(_d(r["date"])) for r in rows})

    data: dict[tuple, float] = defaultdict(float)
    for r in rows:
        if r["jobcode"]:
            data[(r["jobcode"], _week_start(_d(r["date"])))] += r["hours"]

    header = ["Customer"] + [_week_label(ws) for ws in week_starts]
    out    = [header]
    totals = [0.0] * len(week_starts)

    for c in customers:
        row: list[Any] = [c]
        for i, ws in enumerate(week_starts):
            h = round(data[(c, ws)], 2)
            row.append(h if h else "")
            totals[i] += h
        out.append(row)

    out.append(["TOTAL"] + [_r(t) for t in totals])
    return out


def build_monthly(rows: list[dict]) -> list[list]:
    customers = sorted({r["jobcode"] for r in rows if r["jobcode"]})
    months    = sorted({_month_key(_d(r["date"])) for r in rows})

    data: dict[tuple, float] = defaultdict(float)
    for r in rows:
        if r["jobcode"]:
            data[(r["jobcode"], _month_key(_d(r["date"])))] += r["hours"]

    header = ["Customer"] + [_month_label(_month_key_to_date(m)) for m in months]
    out    = [header]
    totals = [0.0] * len(months)

    for c in customers:
        row: list[Any] = [c]
        for i, m in enumerate(months):
            h = round(data[(c, m)], 2)
            row.append(h if h else "")
            totals[i] += h
        out.append(row)

    out.append(["TOTAL"] + [_r(t) for t in totals])
    return out


def build_by_employee(rows: list[dict]) -> list[list]:
    months = sorted({_month_key(_d(r["date"])) for r in rows})

    emp_data: dict[tuple, dict[int, float]] = defaultdict(lambda: defaultdict(float))
    emps_by_customer: dict[str, set[str]]   = defaultdict(set)

    for r in rows:
        if not r["jobcode"]:
            continue
        m = _month_key(_d(r["date"]))
        emp_data[(r["jobcode"], r["user"])][m] += r["hours"]
        emps_by_customer[r["jobcode"]].add(r["user"])

    header = (["Customer", "Employee"]
              + [_month_label(_month_key_to_date(m)) for m in months]
              + ["Total"])
    out = [header]

    for customer in sorted(emps_by_customer):
        employees = sorted(emps_by_customer[customer])

        all_row: list[Any] = [customer, "— All —"]
        all_total = 0.0
        for m in months:
            h = round(sum(emp_data[(customer, e)].get(m, 0) for e in employees), 2)
            all_row.append(h if h else "")
            all_total += h
        all_row.append(_r(all_total))
        out.append(all_row)

        for emp in employees:
            emp_row: list[Any] = ["", emp]
            emp_total = 0.0
            for m in months:
                h = round(emp_data[(customer, emp)].get(m, 0), 2)
                emp_row.append(h if h else "")
                emp_total += h
            emp_row.append(_r(emp_total))
            out.append(emp_row)

    return out


def build_recent(rows: list[dict], window_days: int = 14) -> list[list]:
    cutoff = date.today() - timedelta(days=window_days)
    recent = [r for r in rows if _d(r["date"]) > cutoff]
    if not recent:
        return []

    dates     = sorted({r["date"] for r in recent})
    customers = sorted({r["jobcode"] for r in recent if r["jobcode"]})

    data: dict[tuple, float] = defaultdict(float)
    for r in recent:
        if r["jobcode"]:
            data[(r["jobcode"], r["date"])] += r["hours"]

    header = ["Customer"] + [_daily_label(_d(d)) for d in dates]
    out    = [header]
    totals = [0.0] * len(dates)

    for c in customers:
        row: list[Any] = [c]
        for i, d in enumerate(dates):
            h = round(data[(c, d)], 2)
            row.append(h if h else "")
            totals[i] += h
        out.append(row)

    out.append(["TOTAL"] + [_r(t) for t in totals])
    return out


def build_weekly_variance(
    rows: list[dict],
    expected_weekly: dict[str, float],
) -> list[list]:
    customers   = sorted({r["jobcode"] for r in rows if r["jobcode"]})
    week_starts = sorted({_week_start(_d(r["date"])) for r in rows})

    data: dict[tuple, float] = defaultdict(float)
    for r in rows:
        if r["jobcode"]:
            data[(r["jobcode"], _week_start(_d(r["date"])))] += r["hours"]

    header = ["Customer", "Expected Hrs/Wk"] + [_week_label(ws) for ws in week_starts]
    out    = [header]
    col_totals = [0.0] * len(week_starts)
    total_exp  = sum(expected_weekly.values())

    for c in customers:
        exp = expected_weekly.get(c)
        row: list[Any] = [c, exp if exp else ""]
        for i, ws in enumerate(week_starts):
            actual = round(data[(c, ws)], 2)
            if exp:
                v = round(actual - exp, 2)
                row.append(v)
                col_totals[i] += v
            else:
                row.append(actual if actual else "")
                col_totals[i] += actual
        out.append(row)

    out.append(
        ["TOTAL", _r(total_exp)]
        + [_r(t) for t in col_totals]
    )
    return out


def build_monthly_variance(
    rows: list[dict],
    expected_monthly: dict[str, float],
) -> list[list]:
    customers = sorted({r["jobcode"] for r in rows if r["jobcode"]})
    months    = sorted({_month_key(_d(r["date"])) for r in rows})

    data: dict[tuple, float] = defaultdict(float)
    for r in rows:
        if r["jobcode"]:
            data[(r["jobcode"], _month_key(_d(r["date"])))] += r["hours"]

    header = (["Customer", "Expected Hrs/Month"]
              + [_month_label(_month_key_to_date(m)) for m in months])
    out    = [header]
    col_totals = [0.0] * len(months)
    total_exp  = sum(expected_monthly.values())

    for c in customers:
        exp = expected_monthly.get(c)
        row: list[Any] = [c, exp if exp else ""]
        for i, m in enumerate(months):
            actual = round(data[(c, m)], 2)
            if exp:
                v = round(actual - exp, 2)
                row.append(v)
                col_totals[i] += v
            else:
                row.append(actual if actual else "")
                col_totals[i] += actual
        out.append(row)

    out.append(
        ["TOTAL", _r(total_exp)]
        + [_r(t) for t in col_totals]
    )
    return out


# ── main entry point ──────────────────────────────────────────────────────────

def rebuild_summaries(od: OneDriveClient, user_id: str, item_id: str) -> None:
    """Recompute and overwrite every summary tab from Raw Data."""

    print("[summaries] Reading Raw Data …")
    rows = read_raw_data(od, user_id, item_id)
    if not rows:
        print("[summaries] Raw Data is empty – skipping summary rebuild.")
        return
    print(f"[summaries] {len(rows)} rows loaded.")

    # Preserve expected-hours columns before overwriting variance tabs
    print("[summaries] Reading expected hours …")
    exp_weekly  = read_expected(od, user_id, item_id, "Weekly Variance")
    exp_monthly = read_expected(od, user_id, item_id, "Monthly Variance")

    tables: dict[str, list[list]] = {
        "Daily":            build_daily(rows),
        "Weekly":           build_weekly(rows),
        "Monthly":          build_monthly(rows),
        "By Employee":      build_by_employee(rows),
        "Recent (2 Weeks)": build_recent(rows),
        "Weekly Variance":  build_weekly_variance(rows, exp_weekly),
        "Monthly Variance": build_monthly_variance(rows, exp_monthly),
    }

    for sheet, table in tables.items():
        if not table:
            print(f"[summaries] Skipping '{sheet}' (no data).")
            continue
        nrows = len(table)
        ncols = len(table[0]) if table else 0
        print(f"[summaries] Writing '{sheet}' ({nrows} rows × {ncols} cols) …")
        od.rewrite_sheet(user_id, item_id, sheet, table)

    print("[summaries] All summary tabs updated.")
