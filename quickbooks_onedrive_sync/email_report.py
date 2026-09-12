"""Send daily variance email via Microsoft Graph API (app-only auth).

Requires the Azure app to have Mail.Send application permission granted.
"""

from __future__ import annotations

import os
from collections import defaultdict
from datetime import date
from typing import Any

import msal

from ssl_session import build_session

_GRAPH  = "https://graph.microsoft.com/v1.0"
_SCOPES = ["https://graph.microsoft.com/.default"]

DAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


def _get_token() -> str:
    client_id     = os.environ["AZURE_CLIENT_ID"]
    client_secret = os.environ["AZURE_CLIENT_SECRET"]
    tenant_id     = os.environ["AZURE_TENANT_ID"]
    app = msal.ConfidentialClientApplication(
        client_id,
        authority=f"https://login.microsoftonline.com/{tenant_id}",
        client_credential=client_secret,
    )
    result = app.acquire_token_for_client(scopes=_SCOPES)
    if "access_token" not in result:
        raise RuntimeError(
            f"Failed to acquire token for email: {result.get('error_description')}"
        )
    return result["access_token"]


def send_variance_email(
    rows: list[dict],
    target_date: date,
    expected_daily: dict[str, dict[int, float]],
    exclude_customers: set[str] | None = None,
    from_user: str | None = None,
    to_address: str = "office@maddogcleaning.com",
    threshold: float = 0.5,
) -> None:
    """Compute daily variance for target_date and send an HTML email.

    Args:
        rows:              Parsed rows from Raw Data (date, jobcode, user, hours).
        target_date:       The date to report on.
        expected_daily:    EXPECTED_DAILY dict from sync.py.
        exclude_customers: Customers to omit from the report.
        from_user:         UPN of the mailbox to send from (defaults to ONEDRIVE_USER env var).
        to_address:        Recipient email address.
        threshold:         |delta| must exceed this to be flagged (default 0.5 hrs).
    """
    excl      = exclude_customers or set()
    from_user = from_user or os.environ.get("ONEDRIVE_USER", "me")
    date_str  = target_date.isoformat()
    dow       = target_date.weekday()
    day_name  = DAY_NAMES[dow]

    # Sum actuals for target date
    actuals: dict[str, float] = defaultdict(float)
    for r in rows:
        if r.get("date") != date_str:
            continue
        customer = r.get("jobcode", "")
        if not customer or customer in excl:
            continue
        actuals[customer] += r.get("hours", 0.0)

    # All customers that either have actuals or have an expected for this DOW
    all_customers = sorted(
        {c for c in actuals if c not in excl}
        | {c for c, exp in expected_daily.items() if dow in exp and c not in excl}
    )

    flagged: list[dict[str, Any]] = []
    within:  list[dict[str, Any]] = []
    no_exp:  list[dict[str, Any]] = []

    for c in all_customers:
        exp_hrs = expected_daily.get(c, {}).get(dow)
        act_hrs = round(actuals.get(c, 0.0), 2)
        if exp_hrs is None:
            if act_hrs:
                no_exp.append({"account": c, "actual": act_hrs})
            continue
        delta = round(act_hrs - exp_hrs, 2)
        entry = {"account": c, "expected": exp_hrs, "actual": act_hrs, "delta": delta}
        if abs(delta) > threshold:
            flagged.append(entry)
        else:
            within.append(entry)

    # Sort flagged by abs(delta) descending
    flagged.sort(key=lambda x: abs(x["delta"]), reverse=True)

    subject = f"Daily Variance Snapshot – {day_name} {target_date.month}/{target_date.day}/{target_date.year}"
    body    = _build_html(target_date, day_name, flagged, within, no_exp, threshold)

    token   = _get_token()
    session = build_session()
    session.headers.update({"Authorization": f"Bearer {token}"})

    payload = {
        "message": {
            "subject": subject,
            "body":    {"contentType": "HTML", "content": body},
            "toRecipients": [{"emailAddress": {"address": to_address}}],
        },
        "saveToSentItems": True,
    }

    resp = session.post(
        f"{_GRAPH}/users/{from_user}/sendMail",
        json=payload,
    )
    if resp.status_code not in (200, 202):
        raise RuntimeError(
            f"sendMail failed ({resp.status_code}): {resp.text[:400]}"
        )
    print(f"[email] Variance email for {date_str} sent to {to_address}.")


def _delta_color(delta: float) -> str:
    return "#c0392b" if delta < 0 else "#27ae60"


def _fmt_delta(delta: float) -> str:
    return f"+{delta:.2f}" if delta >= 0 else f"{delta:.2f}"


def _build_html(
    target_date: date,
    day_name: str,
    flagged: list[dict],
    within:  list[dict],
    no_exp:  list[dict],
    threshold: float,
) -> str:
    date_label = f"{day_name}, {target_date.strftime('%B %-d, %Y')}"

    rows_html = ""
    for e in flagged:
        color = _delta_color(e["delta"])
        rows_html += (
            f"<tr style='background:#fff3f3;'>"
            f"<td>{e['account']}</td>"
            f"<td style='text-align:center;'>{e['expected']:.2f}</td>"
            f"<td style='text-align:center;'>{e['actual']:.2f}</td>"
            f"<td style='text-align:center;color:{color};font-weight:bold;'>{_fmt_delta(e['delta'])}</td>"
            f"</tr>"
        )

    table_html = ""
    if flagged:
        table_html = f"""
<table border="1" cellpadding="7" cellspacing="0"
       style="border-collapse:collapse;font-family:Arial,sans-serif;font-size:14px;min-width:500px;">
  <thead style="background:#f2f2f2;">
    <tr>
      <th style="text-align:left;">Account</th>
      <th>Expected (hrs)</th>
      <th>Actual (hrs)</th>
      <th>Delta (hrs)</th>
    </tr>
  </thead>
  <tbody>
    {rows_html}
  </tbody>
</table>"""
    else:
        table_html = "<p style='color:#27ae60;'>✅ All accounts within tolerance.</p>"

    notes = []
    if within:
        names = ", ".join(e["account"] for e in within)
        notes.append(f"Within ±{threshold} hrs: {names}.")
    if no_exp:
        names = ", ".join(f"{e['account']} ({e['actual']} hrs)" for e in no_exp)
        notes.append(f"No daily expected set (actuals only): {names}.")

    notes_html = ""
    if notes:
        notes_html = "<ul style='color:#555;font-size:13px;'>" \
                     + "".join(f"<li>{n}</li>" for n in notes) \
                     + "</ul>"

    return f"""
<div style="font-family:Arial,sans-serif;font-size:14px;color:#222;">
  <h2 style="margin-bottom:4px;">Daily Variance – {date_label}</h2>
  <p style="color:#666;margin-top:0;">Accounts with |delta| &gt; {threshold} hrs flagged below.</p>
  {table_html}
  {notes_html}
</div>
"""
