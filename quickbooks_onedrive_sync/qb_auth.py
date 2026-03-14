#!/usr/bin/env python3
"""One-time QuickBooks Time OAuth 2.0 authorization flow.

Run this ONCE to get your access + refresh tokens, then the main
sync script will automatically refresh them on each run.

Usage:
    python qb_auth.py

It will:
  1. Open the QuickBooks authorization URL in your browser
  2. Start a local server at http://localhost:8080/callback
  3. Exchange the auth code for tokens
  4. Save QBT_ACCESS_TOKEN and QBT_REFRESH_TOKEN into your .env file
"""

from __future__ import annotations

import os
import re
import secrets
import urllib.parse
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

import requests
from dotenv import load_dotenv, set_key

_AUTH_URL = "https://appcenter.intuit.com/connect/oauth2"
_TOKEN_URL = "https://oauth.platform.intuit.com/oauth2/v1/tokens/bearer"
_SCOPE = "com.intuit.quickbooks.timetracking"
_REDIRECT = "http://localhost:8080/callback"
_ENV_FILE = Path(__file__).parent / ".env"

_received_code: str | None = None
_received_state: str | None = None


class _CallbackHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        global _received_code, _received_state
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)
        _received_code = params.get("code", [None])[0]
        _received_state = params.get("state", [None])[0]

        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        self.wfile.write(
            b"<h2>Authorization complete! You can close this tab.</h2>"
        )

    def log_message(self, *args: object) -> None:
        pass  # suppress server logs


def authorize() -> tuple[str, str]:
    """Run the OAuth flow and return (access_token, refresh_token)."""
    load_dotenv(_ENV_FILE)

    client_id = os.environ.get("QBT_CLIENT_ID")
    client_secret = os.environ.get("QBT_CLIENT_SECRET")
    if not client_id or not client_secret:
        raise RuntimeError(
            "QBT_CLIENT_ID and QBT_CLIENT_SECRET must be set in .env before running this script."
        )

    state = secrets.token_urlsafe(16)
    params = {
        "client_id": client_id,
        "response_type": "code",
        "scope": _SCOPE,
        "redirect_uri": _REDIRECT,
        "state": state,
    }
    auth_url = f"{_AUTH_URL}?{urllib.parse.urlencode(params)}"

    print(f"\nOpening browser for QuickBooks authorization…\n{auth_url}\n")
    webbrowser.open(auth_url)

    # Wait for the callback
    server = HTTPServer(("localhost", 8080), _CallbackHandler)
    print("Waiting for authorization callback on http://localhost:8080/callback …")
    server.handle_request()
    server.server_close()

    if not _received_code:
        raise RuntimeError("No authorization code received. Did you approve access?")
    if _received_state != state:
        raise RuntimeError("State mismatch — possible CSRF. Please try again.")

    # Exchange code for tokens
    resp = requests.post(
        _TOKEN_URL,
        data={
            "grant_type": "authorization_code",
            "code": _received_code,
            "redirect_uri": _REDIRECT,
        },
        auth=(client_id, client_secret),
    )
    resp.raise_for_status()
    tokens = resp.json()

    access_token = tokens["access_token"]
    refresh_token = tokens["refresh_token"]

    # Persist into .env
    set_key(str(_ENV_FILE), "QBT_ACCESS_TOKEN", access_token)
    set_key(str(_ENV_FILE), "QBT_REFRESH_TOKEN", refresh_token)

    print("\nTokens saved to .env:")
    print(f"  QBT_ACCESS_TOKEN  = {access_token[:12]}…")
    print(f"  QBT_REFRESH_TOKEN = {refresh_token[:12]}…")
    return access_token, refresh_token


if __name__ == "__main__":
    authorize()
    print("\nSetup complete. You can now run:  python sync.py")
