"""OneDrive / Microsoft Graph API client.

Uses client-credentials (app-only) OAuth flow via MSAL so no browser
interaction is needed — suitable for scheduled/automated runs.

Required Azure app permissions (Application, not Delegated):
    Files.ReadWrite.All   – to read/write the user's OneDrive

Graph API docs: https://learn.microsoft.com/en-us/graph/api/resources/excel
"""

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
        client_id = client_id or os.environ["AZURE_CLIENT_ID"]
        client_secret = client_secret or os.environ["AZURE_CLIENT_SECRET"]
        tenant_id = tenant_id or os.environ["AZURE_TENANT_ID"]

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

    # ── auth ───────────────────────────────────────────────────────────────

    def _refresh_token(self) -> None:
        result = self._app.acquire_token_for_client(scopes=_SCOPES)
        if "access_token" not in result:
            raise RuntimeError(
                f"Failed to acquire Microsoft token: {result.get('error_description')}"
            )
        self._session.headers.update(
            {"Authorization": f"Bearer {result['access_token']}"}
        )

    # ── low-level helpers ──────────────────────────────────────────────────

    def _request(self, method: str, url: str, **kwargs: Any):
        fn = getattr(self._session, method)
        for delay in [0, 4, 8, 16]:
            if delay:
                time.sleep(delay)
            resp = fn(url, **kwargs)
            if resp.status_code == 401:
                self._refresh_token()
                resp = fn(url, **kwargs)
            if resp.status_code != 503:
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

    # ── file lookup ────────────────────────────────────────────────────────

    def resolve_file_id(self, onedrive_path: str, user_id: str = "me") -> str:
        """Return the Graph item ID for a file path like 'Reports/Time Report.xlsx'."""
        encoded = urllib.parse.quote(onedrive_path)
        prefix = "me" if user_id == "me" else f"users/{urllib.parse.quote(user_id)}"
        url = f"{_GRAPH}/{prefix}/drive/root:/{encoded}"
        data = self._get(url)
        return data["id"]

    def list_drive_users(self) -> list[dict]:
        """List all users' drives (useful when running as app with tenant access)."""
        data = self._get(f"{_GRAPH}/users", params={"$select": "id,displayName,mail"})
        return data.get("value", [])

    # ── workbook / worksheet helpers ───────────────────────────────────────

    def _wb_url(self, user_id: str, item_id: str, *parts: str) -> str:
        prefix = "me" if user_id == "me" else f"users/{urllib.parse.quote(user_id)}"
        base = f"{_GRAPH}/{prefix}/drive/items/{item_id}/workbook"
        if parts:
            base += "/" + "/".join(parts)
        return base

    def get_worksheets(self, user_id: str, item_id: str) -> list[str]:
        """Return list of worksheet names in the workbook."""
        data = self._get(self._wb_url(user_id, item_id, "worksheets"))
        return [ws["name"] for ws in data.get("value", [])]

    def ensure_worksheet(
        self, user_id: str, item_id: str, sheet_name: str
    ) -> None:
        """Create the worksheet if it doesn't already exist."""
        existing = self.get_worksheets(user_id, item_id)
        if sheet_name not in existing:
            self._post(
                self._wb_url(user_id, item_id, "worksheets"),
                json={"name": sheet_name},
            )

    def get_used_range(self, user_id: str, item_id: str, sheet_name: str) -> dict:
        url = self._wb_url(
            user_id, item_id, f"worksheets('{sheet_name}')", "usedRange"
        )
        return self._get(url)

    def get_cell_value(
        self, user_id: str, item_id: str, sheet_name: str, row: int, col: int
    ) -> Any:
        """Get a single cell value (0-indexed row/col)."""
        url = self._wb_url(
            user_id, item_id, f"worksheets('{sheet_name}')", f"cell(row={row},column={col})"
        )
        data = self._get(url)
        values = data.get("values", [[None]])
        return values[0][0] if values and values[0] else None

    def update_range(
        self,
        user_id: str,
        item_id: str,
        sheet_name: str,
        start_cell: str,
        values: list[list[Any]],
    ) -> None:
        """Write a 2-D list of values starting at start_cell (e.g. 'A1').

        Automatically calculates the range address from the data dimensions.
        """
        if not values:
            return
        num_rows = len(values)
        num_cols = max(len(row) for row in values)

        # Pad rows that are shorter than num_cols
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
        """Append rows below existing data.  Returns the 1-based row where writing started.

        If the sheet is empty and header is provided, the header is written first.
        """
        if not rows:
            return 1

        used = self.get_used_range(user_id, item_id, sheet_name)
        existing_values: list[list] = used.get("values", [])

        if not existing_values or existing_values == [[]]:
            # Empty sheet — optionally write header first
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
        """Clear a worksheet's contents and write new values starting at A1.

        The header row (row 1) is written with text number-format ("@") so that
        strings such as "3/14" or "Jan 2026" are not auto-converted by Excel to
        date serial numbers.
        """
        # Clear existing content so stale columns/rows don't linger
        clear_url = self._wb_url(
            user_id, item_id,
            f"worksheets('{sheet_name}')", "usedRange/clear",
        )
        try:
            self._post(clear_url, json={"applyTo": "Contents"})
        except Exception:
            pass  # sheet may already be empty

        if not values:
            return

        # Write header row with explicit text format to prevent date auto-conversion
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

        # Write data rows (row 2 onwards) as plain values
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
        """Return 1-based row indices where the date column matches date_str."""
        used = self.get_used_range(user_id, item_id, sheet_name)
        all_values: list[list] = used.get("values", [])
        matches = []
        for i, row in enumerate(all_values, start=1):
            if row and str(row[date_col_index]) == date_str:
                matches.append(i)
        return matches


# ── utilities ──────────────────────────────────────────────────────────────

def _offset_cell(start: str, row_offset: int, col_offset: int) -> str:
    """Return the cell address offset from start by (row_offset, col_offset).

    E.g. _offset_cell('A1', 2, 3) → 'D3'
    """
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

    # Convert back to column letter(s)
    letters = ""
    while new_col > 0:
        new_col, rem = divmod(new_col - 1, 26)
        letters = chr(ord("A") + rem) + letters

    return f"{letters}{new_row}"
