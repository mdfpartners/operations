"""OneDrive / Microsoft Graph API client (app-only OAuth)."""

from __future__ import annotations

import os
import time
import urllib.parse
from typing import Any

import msal

from ssl_session import build_session

_GRAPH = "https://graph.microsoft.com/v1.0"
_SCOPES = ["https://graph.microsoft.com/.default"]


class OneDriveClient:
    def __init__(
        self,
        client_id: str | None = None,
        client_secret: str | None = None,
        tenant_id: str | None = None,
    ) -> None:
        client_id     = client_id     or os.environ["AZURE_CLIENT_ID"]
        client_secret = client_secret or os.environ["AZURE_CLIENT_SECRET"]
        tenant_id     = tenant_id     or os.environ["AZURE_TENANT_ID"]

        authority = f"https://login.microsoftonline.com/{tenant_id}"
        for delay in [0, 4, 8, 16]:
            if delay:
                time.sleep(delay)
            try:
                self._app = msal.ConfidentialClientApplication(
                    client_id,
                    authority=authority,
                    client_credential=client_secret,
                )
                break
            except Exception as exc:
                if "503" not in str(exc) or delay == 16:
                    raise

        self._session = build_session()
        self._refresh_token()

    def _refresh_token(self) -> None:
        result = self._app.acquire_token_for_client(scopes=_SCOPES)
        if "access_token" not in result:
            raise RuntimeError(
                f"Failed to acquire Microsoft token: {result.get('error_description')}"
            )
        self._session.headers.update(
            {"Authorization": f"Bearer {result['access_token']}"}
        )

    def _request(self, method: str, url: str, **kwargs: Any):
        fn = getattr(self._session, method)
        for delay in [0, 4, 8, 16, 32, 60]:
            if delay:
                time.sleep(delay)
            resp = fn(url, **kwargs)
            if resp.status_code == 401:
                self._refresh_token()
                resp = fn(url, **kwargs)
            if resp.status_code not in (503, 504):
                break
        return resp

    def _get(self, url: str, **kwargs: Any) -> dict:
        resp = self._request("get", url, **kwargs)
        resp.raise_for_status()
        return resp.json()

    def _post(self, url: str, **kwargs: Any) -> dict:
        resp = self._request("post", url, **kwargs)
        resp.raise_for_status()
        return resp.json()

    def _patch(self, url: str, **kwargs: Any) -> dict:
        resp = self._request("patch", url, **kwargs)
        resp.raise_for_status()
        return resp.json()

    def _delete(self, url: str, **kwargs: Any) -> None:
        resp = self._request("delete", url, **kwargs)
        resp.raise_for_status()

    def resolve_file_id(self, onedrive_path: str, user_id: str = "me") -> str:
        encoded = urllib.parse.quote(onedrive_path)
        prefix = "me" if user_id == "me" else f"users/{urllib.parse.quote(user_id)}"
        url = f"{_GRAPH}/{prefix}/drive/root:/{encoded}"
        data = self._get(url)
        return data["id"]

    def open_workbook_session(self, user_id: str, item_id: str) -> None:
        """Create a persistent workbook session to improve write reliability."""
        url = self._wb_url(user_id, item_id, "createSession")
        try:
            result = self._post(url, json={"persistChanges": True})
            session_id = result.get("id", "")
            if session_id:
                self._session.headers.update({"workbook-session-id": session_id})
        except Exception:
            pass  # session creation is optional; fall back to sessionless writes

    def close_workbook_session(self, user_id: str, item_id: str) -> None:
        session_id = self._session.headers.get("workbook-session-id")
        if not session_id:
            return
        try:
            url = self._wb_url(user_id, item_id, "closeSession")
            self._post(url, json={})
        except Exception:
            pass
        self._session.headers.pop("workbook-session-id", None)

    def _wb_url(self, user_id: str, item_id: str, *parts: str) -> str:
        prefix = "me" if user_id == "me" else f"users/{urllib.parse.quote(user_id)}"
        base = f"{_GRAPH}/{prefix}/drive/items/{item_id}/workbook"
        if parts:
            base += "/" + "/".join(parts)
        return base

    def get_worksheets(self, user_id: str, item_id: str) -> list[str]:
        data = self._get(self._wb_url(user_id, item_id, "worksheets"))
        return [ws["name"] for ws in data.get("value", [])]

    def ensure_worksheet(self, user_id: str, item_id: str, sheet_name: str) -> None:
        existing = self.get_worksheets(user_id, item_id)
        if sheet_name not in existing:
            self._post(
                self._wb_url(user_id, item_id, "worksheets"),
                json={"name": sheet_name},
            )

    def get_used_range(self, user_id: str, item_id: str, sheet_name: str) -> dict:
        url = self._wb_url(user_id, item_id, f"worksheets('{sheet_name}')", "usedRange")
        return self._get(url)

    def update_range(
        self,
        user_id: str,
        item_id: str,
        sheet_name: str,
        start_cell: str,
        values: list[list[Any]],
    ) -> None:
        if not values:
            return
        num_rows = len(values)
        num_cols = max(len(row) for row in values)
        padded = [r + [""] * (num_cols - len(r)) for r in values]
        end_cell = _offset_cell(start_cell, num_rows - 1, num_cols - 1)
        range_addr = f"{start_cell}:{end_cell}"
        url = self._wb_url(
            user_id, item_id, f"worksheets('{sheet_name}')", f"range(address='{range_addr}')"
        )
        self._patch(url, json={"values": padded})

    def append_rows(
        self,
        user_id: str,
        item_id: str,
        sheet_name: str,
        rows: list[list[Any]],
        header: list[str] | None = None,
    ) -> int:
        if not rows:
            return 1
        used = self.get_used_range(user_id, item_id, sheet_name)
        existing_values: list[list] = used.get("values", [])
        if not existing_values or existing_values == [[]]:
            next_row = 1
            if header:
                self.update_range(user_id, item_id, sheet_name, "A1", [header])
                next_row = 2
        else:
            next_row = len(existing_values) + 1
        start_cell = f"A{next_row}"
        self.update_range(user_id, item_id, sheet_name, start_cell, rows)
        return next_row

    def rewrite_sheet(
        self,
        user_id: str,
        item_id: str,
        sheet_name: str,
        values: list[list],
    ) -> None:
        clear_url = self._wb_url(
            user_id, item_id, f"worksheets('{sheet_name}')", "usedRange/clear",
        )
        try:
            self._post(clear_url, json={"applyTo": "Contents"})
        except Exception:
            pass

        if not values:
            return

        n_cols = len(values[0])
        end_header_cell = _offset_cell("A1", 0, n_cols - 1)
        header_url = self._wb_url(
            user_id, item_id,
            f"worksheets('{sheet_name}')",
            f"range(address='A1:{end_header_cell}')",
        )
        self._patch(header_url, json={
            "values":       [values[0]],
            "numberFormat": [["@"] * n_cols],
        })

        if len(values) > 1:
            self.update_range(user_id, item_id, sheet_name, "A2", values[1:])

    def find_rows_by_date(
        self,
        user_id: str,
        item_id: str,
        sheet_name: str,
        date_str: str,
        date_col_index: int = 0,
    ) -> list[int]:
        used = self.get_used_range(user_id, item_id, sheet_name)
        all_values: list[list] = used.get("values", [])
        matches = []
        for i, row in enumerate(all_values, start=1):
            if row and str(row[date_col_index]) == date_str:
                matches.append(i)
        return matches


def _offset_cell(start: str, row_offset: int, col_offset: int) -> str:
    col_str = ""
    col_num = 0
    i = 0
    while i < len(start) and start[i].isalpha():
        col_str += start[i]
        i += 1
    row_num = int(start[i:])

    for ch in col_str.upper():
        col_num = col_num * 26 + (ord(ch) - ord("A") + 1)

    new_col = col_num + col_offset
    new_row = row_num + row_offset

    letters = ""
    while new_col > 0:
        new_col, rem = divmod(new_col - 1, 26)
        letters = chr(ord("A") + rem) + letters

    return f"{letters}{new_row}"
