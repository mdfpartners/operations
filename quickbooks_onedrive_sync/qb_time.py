"""QuickBooks Time (TSheets) API client.

Pulls daily timesheets, resolves user names and job code labels.
API docs: https://tsheets.intuit.com/api/v1/
"""

from __future__ import annotations

import os
from datetime import date, timedelta
from pathlib import Path
from typing import Any

import requests
from dotenv import set_key

_BASE = "https://rest.tsheets.com/api/v1"
_TOKEN_URL = "https://oauth.platform.intuit.com/oauth2/v1/tokens/bearer"
_ENV_FILE = Path(__file__).parent / ".env"


def _refresh_access_token(client_id: str, client_secret: str, refresh_token: str) -> str:
    """Exchange a refresh token for a new access token and persist it to .env."""
    resp = requests.post(
        _TOKEN_URL,
        data={"grant_type": "refresh_token", "refresh_token": refresh_token},
        auth=(client_id, client_secret),
    )
    resp.raise_for_status()
    tokens = resp.json()
    new_access = tokens["access_token"]
    # Some flows also rotate the refresh token
    new_refresh = tokens.get("refresh_token", refresh_token)
    set_key(str(_ENV_FILE), "QBT_ACCESS_TOKEN", new_access)
    set_key(str(_ENV_FILE), "QBT_REFRESH_TOKEN", new_refresh)
    os.environ["QBT_ACCESS_TOKEN"] = new_access
    os.environ["QBT_REFRESH_TOKEN"] = new_refresh
    return new_access


class QBTimeClient:
    def __init__(self, access_token: str | None = None) -> None:
        self._client_id = os.environ.get("QBT_CLIENT_ID", "")
        self._client_secret = os.environ.get("QBT_CLIENT_SECRET", "")
        self._refresh_token = os.environ.get("QBT_REFRESH_TOKEN", "")
        token = access_token or os.environ["QBT_ACCESS_TOKEN"]
        self._session = requests.Session()
        self._session.headers.update({"Authorization": f"Bearer {token}"})

    def _set_token(self, token: str) -> None:
        self._session.headers.update({"Authorization": f"Bearer {token}"})

    # ── low-level ──────────────────────────────────────────────────────────

    def _get(self, endpoint: str, params: dict[str, Any] | None = None) -> dict:
        resp = self._session.get(f"{_BASE}/{endpoint}", params=params)
        if resp.status_code == 401 and self._refresh_token and self._client_id:
            new_token = _refresh_access_token(
                self._client_id, self._client_secret, self._refresh_token
            )
            self._set_token(new_token)
            resp = self._session.get(f"{_BASE}/{endpoint}", params=params)
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
