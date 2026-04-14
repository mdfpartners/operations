"""
Gmail API client for Jenny.

Sends two types of emails:
  1. First-round interview invitations to candidates who pass form review.
  2. Daily pipeline reports to the recruiting manager.

Authentication uses OAuth2 with a stored token file. Run setup_auth.py
once before scheduling Jenny as a cron job to create the initial token.
"""

import base64
import logging
import os
import pickle
from datetime import date
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

logger = logging.getLogger(__name__)

_SCOPES = ["https://www.googleapis.com/auth/gmail.send"]


class GmailClient:
    """Sends emails via the Gmail API from the recruiting account."""

    def __init__(self, config: dict):
        self.recruiting_address: str = config["recruiting_address"]
        self.report_recipient: str = config.get("report_recipient", config["recruiting_address"])
        self.credentials_file: str = config["credentials_file"]
        self.token_file: str = config.get("token_file", "credentials/token_gmail.pickle")
        self._service = None

    # ── Auth ─────────────────────────────────────────────────────────────────

    def _get_service(self):
        if self._service:
            return self._service

        creds = None
        if os.path.exists(self.token_file):
            with open(self.token_file, "rb") as f:
                creds = pickle.load(f)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_file, _SCOPES
                )
                creds = flow.run_local_server(port=0)
            with open(self.token_file, "wb") as f:
                pickle.dump(creds, f)

        self._service = build("gmail", "v1", credentials=creds, cache_discovery=False)
        return self._service

    # ── Internal helpers ─────────────────────────────────────────────────────

    def _encode_message(self, to: str, subject: str, html: str, plain: str = "") -> dict:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = self.recruiting_address
        msg["To"] = to
        if plain:
            msg.attach(MIMEText(plain, "plain"))
        msg.attach(MIMEText(html, "html"))
        raw = base64.urlsafe_b64encode(msg.as_bytes()).decode("utf-8")
        return {"raw": raw}

    def _send(self, to: str, subject: str, html: str, plain: str = "") -> bool:
        try:
            service = self._get_service()
            body = self._encode_message(to, subject, html, plain)
            service.users().messages().send(userId="me", body=body).execute()
            logger.info(f"Email sent → {to} | {subject}")
            return True
        except Exception as exc:
            logger.error(f"Failed to send email to {to}: {exc}")
            return False

    # ── Public API ───────────────────────────────────────────────────────────

    def send_interview_invite(
        self,
        candidate: dict,
        company_name: str = "Mad Dog Facility Partners",
    ) -> bool:
        """Send a first-round interview invitation to a candidate."""
        name = candidate.get("full_name") or "there"
        role = candidate.get("position") or "the open position"
        to_email = candidate.get("email", "")

        if not to_email:
            logger.error(f"No email address available for candidate '{name}' – skipping invite.")
            return False

        subject = f"You're Invited to Interview – {role} | {company_name}"

        html = f"""<!DOCTYPE html>
<html>
<body style="font-family: Arial, sans-serif; max-width: 580px; color: #222; line-height: 1.6;">
  <p>Hi {name},</p>

  <p>Thank you for applying and taking the time to complete our application form for the
  <strong>{role}</strong> position at <strong>{company_name}</strong>.</p>

  <p>We reviewed your responses and we're excited to invite you to a
  <strong>first-round interview</strong>! We'd love to learn more about you and tell you
  more about what makes {company_name} a great place to work.</p>

  <p>As a <strong>veteran-owned business</strong>, we hold ourselves to a high standard of
  discipline, reliability, and genuine service to our clients. We look for teammates who
  share those values — and your background caught our attention.</p>

  <p>To schedule your interview, simply <strong>reply to this email</strong> with your
  availability over the next 5 business days and we'll confirm a time right away.</p>

  <p>We look forward to connecting with you!</p>

  <p style="margin-top: 24px;">
    Best regards,<br>
    <strong>Recruiting Team</strong><br>
    {company_name}
  </p>
</body>
</html>"""

        plain = f"""Hi {name},

Thank you for applying and completing our form for the {role} position at {company_name}.

We're pleased to invite you to a first-round interview!

As a veteran-owned business, we pride ourselves on discipline, reliability, and genuine service excellence.

Please reply to this email with your availability over the next 5 business days and we'll get something on the calendar.

Best regards,
Recruiting Team
{company_name}"""

        return self._send(to_email, subject, html, plain)

    def send_daily_report(self, report_html: str, report_text: str = "") -> bool:
        """Email the daily pipeline report to the report recipient."""
        subject = (
            f"Jenny Daily Recruiting Report \u2013 "
            f"{date.today().strftime('%B %d, %Y')}"
        )
        return self._send(self.report_recipient, subject, report_html, report_text)
