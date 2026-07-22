"""Rebuild all summary tabs from Raw Data."""

from __future__ import annotations

import time
from collections import defaultdict
from datetime import date, timedelta
from typing import Any

from onedrive import OneDriveClient


def _d(val: Any) -> date:
    if isinstance(val, (int, float)) and val > 40000:
        return date(1899, 12, 30) + timedelta(days=int(val))
    return date.fromisoformat(str(val))


def _month_key(d: date) -> int:
    return d.year * 12 + d.month - 1


def _month_key_to_date(key: int) -> date:
    return date(key // 12, key % 12 + 1, 1)


def _week_start(d: date) -> date:
    return d - timedelta(days=(d.weekday() - 5) % 7)


def _daily_label(d: date) -> str:
    return f"{d.month}/{d.day}"


def _week_label(ws: date) -> str:
    we = ws + timedelta(days=6)
    return f"{ws.month}/{ws.day} - {we.month}/{we.day}"


def _month_label(d: date) -> str:
    return d.strftime("%b %Y")


def _r(val: float) -> Any:
    v = round(val, 2)
    return v if v else ""


def read_raw_data(od: OneDriveClient, user_id: str, item_id: str) -> list[dict]:
    used = od.get_used_range(user_id, item_id, "Raw Data")
    all_rows = used.get("values", [])
    rows: list[dict] = []
    for row in all_rows[1:]:
        if not row or not row[0]:
            continue
        rows.append({
            "date":    _d(row[0]).isoformat(),
            "jobcode": str(row[1]).strip() if len(row) > 1 and row[1] else "",
            "user":    str(row[2]).strip() if len(row) > 2 and row[2] else "",
            "hours":   float(row[3]) if len(row) > 3 and row[3] != "" else 0.0,
        })
    return rows


def read_expected(
    od: OneDriveClient,
    user_id: str,
    item_id: str,
    sheet_name: str,
) -> dict[str, float]:
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


def build_daily(rows: list[dict], exclude: set[str] | None = None) -> list[list]:
    excl      = exclude or set()
    dates     = sorted({r["date"] for r in rows})
    customers = sorted({r["jobcode"] for r in rows if r["jobcode"] and r["jobcode"] not in excl})

    data: dict[tuple, float] = defaultdict(float)
    for r in rows:
        if r["jobcode"] and r["jobcode"] not in excl:
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


def build_weekly(rows: list[dict], exclude: set[str] | None = None) -> list[list]:
    excl        = exclude or set()
    customers   = sorted({r["jobcode"] for r in rows if r["jobcode"] and r["jobcode"] not in excl})
    week_starts = sorted({_week_start(_d(r["date"])) for r in rows})

    data: dict[tuple, float] = defaultdict(float)
    for r in rows:
        if r["jobcode"] and r["jobcode"] not in excl:
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


def build_monthly(rows: list[dict], exclude: set[str] | None = None) -> list[list]:
    excl      = exclude or set()
    customers = sorted({r["jobcode"] for r in rows if r["jobcode"] and r["jobcode"] not in excl})
    months    = sorted({_month_key(_d(r["date"])) for r in rows})

    data: dict[tuple, float] = defaultdict(float)
    for r in rows:
        if r["jobcode"] and r["jobcode"] not in excl:
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


def build_by_employee(rows: list[dict], exclude: set[str] | None = None) -> list[list]:
    excl   = exclude or set()
    months = sorted({_month_key(_d(r["date"])) for r in rows})

    emp_data: dict[tuple, dict[int, float]] = defaultdict(lambda: defaultdict(float))
    emps_by_customer: dict[str, set[str]]   = defaultdict(set)

    for r in rows:
        if not r["jobcode"] or r["jobcode"] in excl:
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


def build_recent(rows: list[dict], window_days: int = 14, exclude: set[str] | None = None) -> list[list]:
    excl   = exclude or set()
    cutoff = date.today() - timedelta(days=window_days)
    recent = [r for r in rows if _d(r["date"]) > cutoff]
    if not recent:
        return []

    dates     = sorted({r["date"] for r in recent})
    customers = sorted({r["jobcode"] for r in recent if r["jobcode"] and r["jobcode"] not in excl})

    data: dict[tuple, float] = defaultdict(float)
    for r in recent:
        if r["jobcode"] and r["jobcode"] not in excl:
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


def build_daily_variance(
    rows: list[dict],
    expected_daily: dict[str, dict[int, float]],
    expected_weekly: dict[str, float] | None = None,
    exclude: set[str] | None = None,
    window_days: int = 14,
) -> list[list]:
    excl   = exclude or set()
    exp_wk = expected_weekly or {}
    cutoff = date.today() - timedelta(days=window_days)
    recent = [r for r in rows if _d(r["date"]) > cutoff]
    if not recent:
        return []

    dates   = sorted({r["date"] for r in recent})
    d_dates = [_d(d) for d in dates]

    customers_in_data = {r["jobcode"] for r in recent if r["jobcode"] and r["jobcode"] not in excl}
    customers_with_exp = {c for c, exp in expected_daily.items() if exp and c not in excl}
    customers = sorted(customers_in_data | customers_with_exp)

    data: dict[tuple, float] = defaultdict(float)
    for r in recent:
        if r["jobcode"] and r["jobcode"] not in excl:
            data[(r["jobcode"], r["date"])] += r["hours"]

    # Header: Customer | Exp Hrs/Wk | [date Exp | date Act] × 14
    header: list[Any] = ["Customer", "Expected Hrs/Wk"]
    for d in d_dates:
        lbl = _daily_label(d)
        header += [f"{lbl} Exp", f"{lbl} Act"]
    out = [header]

    totals_exp = [0.0] * len(dates)
    totals_act = [0.0] * len(dates)

    for c in customers:
        exp = expected_daily.get(c, {})
        row: list[Any] = [c, exp_wk.get(c, "")]
        for i, (date_str, d) in enumerate(zip(dates, d_dates)):
            dow     = d.weekday()
            exp_day = exp.get(dow)
            actual  = round(data.get((c, date_str), 0.0), 2)
            row.append(exp_day if exp_day is not None else "")
            row.append(actual if actual else "")
            if exp_day is not None:
                totals_exp[i] += exp_day
            totals_act[i] += actual
        out.append(row)

    total_row: list[Any] = ["TOTAL", _r(sum(exp_wk.values()))]
    for i in range(len(dates)):
        total_row.append(_r(totals_exp[i]) if totals_exp[i] else "")
        total_row.append(_r(totals_act[i]) if totals_act[i] else "")
    out.append(total_row)
    return out


def build_weekly_variance(
    rows: list[dict],
    expected_weekly: dict[str, float],
    exclude: set[str] | None = None,
) -> list[list]:
    excl = exclude or set()
    customers   = sorted({r["jobcode"] for r in rows if r["jobcode"] and r["jobcode"] not in excl})
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

    out.append(["TOTAL", _r(total_exp)] + [_r(t) for t in col_totals])
    return out


def build_monthly_variance(
    rows: list[dict],
    expected_monthly: dict[str, float],
    exclude: set[str] | None = None,
) -> list[list]:
    excl = exclude or set()
    customers = sorted({r["jobcode"] for r in rows if r["jobcode"] and r["jobcode"] not in excl})
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

    out.append(["TOTAL", _r(total_exp)] + [_r(t) for t in col_totals])
    return out


def rebuild_summaries(
    od: OneDriveClient,
    user_id: str,
    item_id: str,
    rows: list[dict] | None = None,
    exp_weekly_override: dict[str, float] | None = None,
    exp_monthly_override: dict[str, float] | None = None,
    exclude_customers: set[str] | None = None,
    expected_daily: dict[str, dict[int, float]] | None = None,
) -> None:
    if rows is None:
        print("[summaries] Reading Raw Data …")
        rows = read_raw_data(od, user_id, item_id)
    else:
        print(f"[summaries] Using {len(rows)} in-memory rows.")
    if not rows:
        print("[summaries] Raw Data is empty – skipping summary rebuild.")
        return
    print(f"[summaries] {len(rows)} rows loaded.")

    if exp_weekly_override is not None:
        exp_weekly = exp_weekly_override
    else:
        print("[summaries] Reading expected hours …")
        exp_weekly = read_expected(od, user_id, item_id, "Weekly Variance")

    if exp_monthly_override is not None:
        exp_monthly = exp_monthly_override
    else:
        if exp_weekly_override is None:
            print("[summaries] Reading expected monthly hours …")
        exp_monthly = read_expected(od, user_id, item_id, "Monthly Variance")

    excl = exclude_customers or set()
    exp_daily = expected_daily or {}

    tables: dict[str, list[list]] = {
        "Daily":            build_daily(rows, exclude=excl),
        "Weekly":           build_weekly(rows, exclude=excl),
        "Monthly":          build_monthly(rows, exclude=excl),
        "By Employee":      build_by_employee(rows, exclude=excl),
        "Recent (2 Weeks)": build_recent(rows, exclude=excl),
        "Weekly Variance":  build_weekly_variance(rows, exp_weekly, exclude=excl),
        "Monthly Variance": build_monthly_variance(rows, exp_monthly, exclude=excl),
        "Daily Variance":   build_daily_variance(rows, exp_daily, expected_weekly=exp_weekly, exclude=excl),
    }

    od.ensure_worksheet(user_id, item_id, "Daily Variance")

    for sheet, table in tables.items():
        if not table:
            print(f"[summaries] Skipping '{sheet}' (no data).")
            continue
        nrows = len(table)
        ncols = len(table[0]) if table else 0
        print(f"[summaries] Writing '{sheet}' ({nrows} rows × {ncols} cols) …")
        for attempt in range(5):
            try:
                od.rewrite_sheet(user_id, item_id, sheet, table)
                break
            except Exception as exc:
                if attempt == 4:
                    raise
                wait = 2 ** (attempt + 1)
                print(f"[summaries] Retrying '{sheet}' in {wait}s ({exc}) …")
                time.sleep(wait)

    print("[summaries] All summary tabs updated.")
