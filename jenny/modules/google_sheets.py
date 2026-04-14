"""
Google Sheets reader for Jenny.

Reads Google Form responses from the linked Google Sheet.
Supports two credential types:
  - Service account JSON  (preferred for cron jobs – no interactive auth)
  - OAuth2 desktop client JSON (requires running setup_auth.py first)

The sheet is expected to have headers in row 1 and responses starting at row 2,
which is the default layout Google Forms uses for its linked spreadsheet.
"""

import json
import logging
import os
import pickle
from typing import Optional

from google.auth.transport.requests import Request
from google.oauth2 import service_account
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

logger = logging.getLogger(__name__)

_SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]

# Keywords used for fuzzy column matching when no exact name is configured
_COLUMN_KEYWORDS: dict = {
    "timestamp": ["timestamp", "time", "date submitted"],
    "email": ["email", "e-mail", "email address"],
    "full_name": ["full name", "name", "your name", "applicant name"],
    "phone": ["phone", "mobile", "cell", "telephone", "contact number"],
    "position": ["position", "role", "job", "applying for", "apply for"],
    "experience": ["experience", "background", "history", "describe your", "relevant"],
    "felony_question": ["felony", "conviction", "criminal", "convicted"],
    "felony_details": ["felony detail", "conviction detail", "if yes", "explain", "describe"],
}


class GoogleSheetsReader:
    """Reads Google Form responses from a linked Google Sheet."""

    def __init__(self, config: dict):
        self.sheet_id: str = config["sheet_id"]
        self.credentials_file: str = config["credentials_file"]
        self.token_file: str = config.get("token_file", "credentials/token_sheets.pickle")
        self.form_columns: dict = config.get("form_columns", {})
        self._service = None

    # ── Auth ─────────────────────────────────────────────────────────────────

    def _get_service(self):
        if self._service:
            return self._service

        creds = None

        # Detect credential type
        try:
            with open(self.credentials_file) as f:
                cred_data = json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            raise RuntimeError(
                f"Cannot read Google credentials from {self.credentials_file}: {exc}"
            )

        if cred_data.get("type") == "service_account":
            # ── Service account (best for cron jobs) ──
            creds = service_account.Credentials.from_service_account_file(
                self.credentials_file, scopes=_SCOPES
            )
            logger.info("Google Sheets: using service account credentials.")
        else:
            # ── OAuth2 (requires prior run of setup_auth.py) ──
            if os.path.exists(self.token_file):
                with open(self.token_file, "rb") as f:
                    creds = pickle.load(f)

            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                    with open(self.token_file, "wb") as f:
                        pickle.dump(creds, f)
                else:
                    flow = InstalledAppFlow.from_client_secrets_file(
                        self.credentials_file, _SCOPES
                    )
                    creds = flow.run_local_server(port=0)
                    with open(self.token_file, "wb") as f:
                        pickle.dump(creds, f)
            logger.info("Google Sheets: using OAuth2 credentials.")

        self._service = build("sheets", "v4", credentials=creds, cache_discovery=False)
        return self._service

    # ── Column mapping ───────────────────────────────────────────────────────

    def _build_column_map(self, headers: list) -> dict:
        """
        Build a mapping of canonical field names → column index.
        Uses exact names from config first; falls back to fuzzy keyword matching.
        """
        result: dict = {}
        headers_lower = [h.lower() for h in headers]

        for field, keywords in _COLUMN_KEYWORDS.items():
            # 1. Exact match via config
            configured_name = self.form_columns.get(field, "")
            if configured_name and configured_name in headers:
                result[field] = headers.index(configured_name)
                continue

            # 2. Fuzzy keyword match
            for i, h in enumerate(headers_lower):
                for kw in keywords:
                    if kw in h:
                        result[field] = i
                        break
                if field in result:
                    break

        return result

    # ── Public API ───────────────────────────────────────────────────────────

    def get_responses(self) -> list:
        """
        Return all form responses from the linked Google Sheet as a list of dicts.
        Each dict has canonical field names plus a 'raw' key with the full row.
        """
        logger.info("Fetching Google Form responses from Sheet…")
        try:
            service = self._get_service()
            result = (
                service.spreadsheets()
                .values()
                .get(spreadsheetId=self.sheet_id, range="Sheet1")
                .execute()
            )
            rows = result.get("values", [])

            if not rows:
                logger.info("Google Sheet is empty – no responses yet.")
                return []

            headers = rows[0]
            col_map = self._build_column_map(headers)
            logger.debug(f"Column map: {col_map}")

            def get_val(row: list, field: str) -> str:
                idx = col_map.get(field)
                if idx is not None and idx < len(row):
                    return str(row[idx]).strip()
                return ""

            responses = []
            for row in rows[1:]:
                if not any(cell.strip() for cell in row):
                    continue  # Skip blank rows

                response = {
                    "timestamp": get_val(row, "timestamp"),
                    "email": get_val(row, "email"),
                    "full_name": get_val(row, "full_name"),
                    "phone": get_val(row, "phone"),
                    "position": get_val(row, "position"),
                    "experience": get_val(row, "experience"),
                    "felony_question": get_val(row, "felony_question"),
                    "felony_details": get_val(row, "felony_details"),
                    "raw": {h: (row[i] if i < len(row) else "") for i, h in enumerate(headers)},
                }
                responses.append(response)

            logger.info(f"Loaded {len(responses)} form response(s).")
            return responses

        except Exception as exc:
            logger.error(f"Error reading Google Sheet: {exc}")
            return []

    def has_recent_felony(self, response: dict) -> bool:
        """
        Return True if the form response discloses a recent felony conviction.

        Logic:
          - If the felony_question answer contains a clear "no" indicator → False
          - If it contains a clear "yes" indicator AND felony_details is non-trivial → True
          - If ambiguous or empty → False (err on the side of not blocking candidates)
        """
        answer = response.get("felony_question", "").strip().lower()
        details = response.get("felony_details", "").strip()

        if not answer:
            return False

        _NO = {"no", "n", "false", "0", "have not", "never", "none", "did not", "not convicted"}
        _YES = {"yes", "y", "true", "1", "have been", "i have", "convicted", "guilty"}

        for no_token in _NO:
            if no_token in answer:
                return False

        for yes_token in _YES:
            if yes_token in answer:
                # Require some non-trivial detail text to confirm
                if details and len(details) > 5:
                    return True
                # "Yes" without details is still a disclosure
                if yes_token in ("yes", "y", "true", "1"):
                    return True

        return False
