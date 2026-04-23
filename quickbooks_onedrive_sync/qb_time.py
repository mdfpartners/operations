"""QuickBooks Time (TSheets) API client.

Pulls daily timesheets, resolves user names and job code labels.
API docs: https://tsheets.intuit.com/api/v1/

Authentication: bearer token generated in QuickBooks Time →
Settings → App Management → (your app) → Add Token.
Set QBT_ACCESS_TOKEN in .env with the full token value.
"""

from __future__ import annotations

import os
import time
from datetime import date, timedelta
from typing import Any

from ssl_session import build_session

_BASE = "https://rest.tsheets.com/api/v1"


class QBTimeClient:
    def __init__(self, access_token: str | None = None) -> None:
        token = access_token or os.environ["QBT_ACCESS_TOKEN"]
        self._session = build_session({"Authorization": f"Bearer {token}"})

    # ── low-level ──────────────────────────────────────────────────────────

    def _get(self, endpoint: str, params: dict[str, Any] | None = None) -> dict:
        url = f"{_BASE}/{endpoint}"
        for attempt, delay in enumerate([0, 4, 8, 16]):
            if delay:
                time.sleep(delay)
            resp = self._session.get(url, params=params)
            if resp.status_code != 503:
                break
        resp.raise_for_status()
        return resp.json()

    # ── helpers ────────────────────────────────────────────────────────────

    def _fetch_users(self, user_ids: list[int]) -> dict[int, str]:
        """Return {user_id: full_name}."""
        if not user_ids:
            return {}
        data = self._get("users", {"ids": ",".join(str(i) for i in user_ids)})
        return {
            int(uid): f"{u['first_name']} {u['last_name']}".strip()
            for uid, u in data.get("results", {}).get("users", {}).items()
        }

    def _fetch_jobcodes(self, jobcode_ids: list[int]) -> dict[int, str]:
        """Return {jobcode_id: name}."""
        if not jobcode_ids:
            return {}
        data = self._get("jobcodes", {"ids": ",".join(str(i) for i in jobcode_ids)})
        return {
            int(jid): j["name"]
            for jid, j in data.get("results", {}).get("jobcodes", {}).items()
        }

    # ── public ─────────────────────────────────────────────────────────────

    def get_timesheets(
        self,
        start: date,
        end: date,
    ) -> list[dict[str, Any]]:
        """Return a flat list of timesheet rows for the given date range.

        Each row has:
            date        – YYYY-MM-DD
            user        – full name
            jobcode     – job code name
            hours       – decimal hours (float)
            notes       – any notes on the entry
        """
        params: dict[str, Any] = {
            "start_date": start.isoformat(),
            "end_date": end.isoformat(),
            "on_the_clock": "both",
            "per_page": 200,
        }

        raw_sheets: list[dict] = []
        page = 1
        while True:
            params["page"] = page
            data = self._get("timesheets", params)
            results = data.get("results", {}).get("timesheets", {})
            if not results:
                break
            raw_sheets.extend(results.values())
            if not data.get("more"):
                break
            page += 1

        if not raw_sheets:
            return []

        user_ids = list({s["user_id"] for s in raw_sheets})
        jobcode_ids = list({s["jobcode_id"] for s in raw_sheets if s.get("jobcode_id")})

        users = self._fetch_users(user_ids)
        jobcodes = self._fetch_jobcodes(jobcode_ids)

        rows: list[dict[str, Any]] = []
        for sheet in raw_sheets:
            # duration is in seconds; convert to hours
            duration_secs = sheet.get("duration") or 0
            hours = round(duration_secs / 3600, 2)

            # date comes as "YYYY-MM-DD" in the `date` field for regular entries
            entry_date = sheet.get("date") or sheet.get("start", "")[:10]

            rows.append(
                {
                    "date": entry_date,
                    "user": users.get(sheet["user_id"], str(sheet["user_id"])),
                    "jobcode": jobcodes.get(sheet.get("jobcode_id", 0), ""),
                    "hours": hours,
                    "notes": sheet.get("notes", ""),
                }
            )

        rows.sort(key=lambda r: (r["date"], r["user"]))
        return rows


def yesterday_range() -> tuple[date, date]:
    d = date.today() - timedelta(days=1)
    return d, d


def date_range_for_days_back(days: int) -> tuple[date, date]:
    end = date.today() - timedelta(days=1)
    start = end - timedelta(days=days - 1)
    return start, end
