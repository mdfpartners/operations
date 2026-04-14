#!/usr/bin/env python3
"""
One-time Google API authorization setup for Jenny.

Run this script ONCE on a machine with a browser before you schedule Jenny
as a headless cron job. It will open a browser window to complete OAuth2
authorization and save the resulting access tokens so that Jenny can run
non-interactively from then on.

Usage:
    python setup_auth.py [--config path/to/config.json]
"""

import argparse
import json
import os
import pickle
import sys
from pathlib import Path


def load_config(path: str = "config.json") -> dict:
    p = Path(path)
    if not p.exists():
        print(f"ERROR: config file '{path}' not found.")
        print("Copy config.example.json → config.json and fill in your credentials first.")
        sys.exit(1)
    with open(p) as f:
        return json.load(f)


def setup_gmail(config: dict) -> None:
    """Authorize Gmail (send scope) and persist the OAuth2 token."""
    from google_auth_oauthlib.flow import InstalledAppFlow

    creds_file = config["gmail"]["credentials_file"]
    token_file = config["gmail"].get("token_file", "credentials/token_gmail.pickle")

    if not Path(creds_file).exists():
        print(f"\nERROR: Gmail credentials file not found: {creds_file}")
        print("Download your OAuth2 Desktop App credentials from Google Cloud Console")
        print("and save them to that path. See docs/gmail_setup.md for instructions.")
        return

    print(f"\n{'─'*56}")
    print("STEP 1 of 2 – Authorizing Gmail API")
    print(f"{'─'*56}")
    print("A browser window will open. Sign in with your recruiting Gmail")
    print(f"account ({config['gmail']['recruiting_address']}) and click Allow.\n")
    input("Press ENTER when you're ready to open the browser…")

    scopes = ["https://www.googleapis.com/auth/gmail.send"]
    flow = InstalledAppFlow.from_client_secrets_file(creds_file, scopes)
    creds = flow.run_local_server(port=0)

    Path(token_file).parent.mkdir(parents=True, exist_ok=True)
    with open(token_file, "wb") as f:
        pickle.dump(creds, f)

    print(f"\n✓ Gmail token saved to: {token_file}")


def setup_sheets(config: dict) -> None:
    """Authorize Google Sheets (read-only scope) and persist the token.
    If a service account is configured, just confirm the share requirement.
    """
    creds_file = config["google"]["credentials_file"]
    token_file = config["google"].get("token_file", "credentials/token_sheets.pickle")

    if not Path(creds_file).exists():
        print(f"\nERROR: Google credentials file not found: {creds_file}")
        print("See docs/google_sheets_setup.md for setup instructions.")
        return

    # Detect credential type
    try:
        with open(creds_file) as f:
            cred_data = json.load(f)
    except Exception as exc:
        print(f"\nERROR: Could not read credentials file: {exc}")
        return

    print(f"\n{'─'*56}")
    print("STEP 2 of 2 – Authorizing Google Sheets API")
    print(f"{'─'*56}")

    if cred_data.get("type") == "service_account":
        sa_email = cred_data.get("client_email", "(unknown)")
        print("Service account credentials detected – no interactive auth needed.")
        print(f"\nIMPORTANT: You must share your Google Sheet with the service account:")
        print(f"\n  {sa_email}\n")
        print("Open your Google Sheet → Share → paste that email → set Viewer access → Done.")
        return

    # OAuth2 flow
    from google_auth_oauthlib.flow import InstalledAppFlow

    print("A browser window will open. Sign in with the Google account that")
    print("owns the sheet and click Allow.\n")
    input("Press ENTER when you're ready to open the browser…")

    scopes = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
    flow = InstalledAppFlow.from_client_secrets_file(creds_file, scopes)
    creds = flow.run_local_server(port=0)

    Path(token_file).parent.mkdir(parents=True, exist_ok=True)
    with open(token_file, "wb") as f:
        pickle.dump(creds, f)

    print(f"\n✓ Sheets token saved to: {token_file}")


def verify_config(config: dict) -> None:
    """Spot-check the config for obviously missing values."""
    issues = []
    placeholders = {"YOUR_", "your-", "sk-ant-YOUR", "example.com", "YOUR_GOOGLE"}

    def check(path: str, value: str) -> None:
        if not value:
            issues.append(f"  {path} is empty")
        elif any(p in str(value) for p in placeholders):
            issues.append(f"  {path} still contains a placeholder value")

    check("indeed.email", config["indeed"].get("email", ""))
    check("indeed.password", config["indeed"].get("password", ""))
    check("google.form_link", config["google"].get("form_link", ""))
    check("google.sheet_id", config["google"].get("sheet_id", ""))
    check("gmail.recruiting_address", config["gmail"].get("recruiting_address", ""))
    check("gmail.report_recipient", config["gmail"].get("report_recipient", ""))
    check("anthropic.api_key", config["anthropic"].get("api_key", ""))

    if issues:
        print("\nWARNING: The following config values look incomplete:")
        for issue in issues:
            print(issue)
        print("\nEdit config.json before running Jenny in production.\n")
    else:
        print("\n✓ Config values look complete.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Jenny – one-time Google API setup")
    parser.add_argument("--config", default="config.json", help="Path to config.json")
    args = parser.parse_args()

    config = load_config(args.config)

    print("=" * 56)
    print("Jenny – Google API Authorization Setup")
    print(f"Company: {config['company']['name']}")
    print("=" * 56)

    verify_config(config)
    setup_gmail(config)
    setup_sheets(config)

    print(f"\n{'='*56}")
    print("Setup complete!")
    print(f"{'='*56}")
    print("\nYou can now schedule Jenny as a cron job.")
    print("See README.md → 'Scheduling with cron' for the exact command.")


if __name__ == "__main__":
    main()
