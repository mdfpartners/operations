"""
Log manager for Jenny.

Tracks all candidate interactions in a local JSON file so the agent can pick
up where it left off on every run without re-contacting people or re-sending
messages.

Log file structure:
{
  "candidates": {
    "<indeed_id>": {
      "name": "...",
      "role": "...",
      "indeed_id": "...",
      "email": null,
      "initial_message_sent_at": "<iso8601>",
      "initial_message_status": "sent|failed",
      "reminder_sent_at": null,
      "reminder_status": null,
      "form_submitted_at": null,
      "form_submission": null,
      "interview_invite_sent_at": null,
      "interview_invite_status": null,
      "flagged": false,
      "flag_reason": null,
      "proactive_questions": [],
      "first_seen_at": "<iso8601>"
    }
  },
  "runs": [
    { "run_at": "<iso8601>", "actions_count": 5, "flagged_count": 1 }
  ]
}
"""

import json
import logging
import os
from datetime import datetime, timedelta
from typing import Optional

import pytz

logger = logging.getLogger(__name__)


class LogManager:
    """Manages the persistent JSON log of all candidate interactions."""

    def __init__(self, log_file: str, timezone_str: str = "America/Phoenix"):
        self.log_file = log_file
        self.tz = pytz.timezone(timezone_str)
        self._data = self._load()

    # ------------------------------------------------------------------ #
    # Persistence
    # ------------------------------------------------------------------ #

    def _load(self) -> dict:
        if os.path.exists(self.log_file):
            try:
                with open(self.log_file, "r") as f:
                    return json.load(f)
            except (json.JSONDecodeError, OSError) as e:
                logger.error(f"Could not read log file {self.log_file}: {e}. Starting fresh.")
        return {"candidates": {}, "runs": []}

    def save(self) -> None:
        with open(self.log_file, "w") as f:
            json.dump(self._data, f, indent=2, default=str)
        logger.debug(f"Log saved to {self.log_file}")

    def _now(self) -> str:
        return datetime.now(self.tz).isoformat()

    # ------------------------------------------------------------------ #
    # Candidate tracking – Indeed messages
    # ------------------------------------------------------------------ #

    def has_been_contacted(self, indeed_id: str) -> bool:
        """Return True if this Indeed applicant ID is already in the log."""
        return indeed_id in self._data["candidates"]

    def record_initial_message(
        self,
        indeed_id: str,
        name: str,
        role: str,
        status: str = "sent",
    ) -> None:
        """Create a new candidate record after sending the initial Indeed message."""
        self._data["candidates"][indeed_id] = {
            "name": name,
            "role": role,
            "indeed_id": indeed_id,
            "email": None,
            "initial_message_sent_at": self._now(),
            "initial_message_status": status,
            "reminder_sent_at": None,
            "reminder_status": None,
            "form_submitted_at": None,
            "form_submission": None,
            "interview_invite_sent_at": None,
            "interview_invite_status": None,
            "flagged": False,
            "flag_reason": None,
            "proactive_questions": [],
            "first_seen_at": self._now(),
        }

    def record_reminder_sent(self, indeed_id: str, status: str = "sent") -> None:
        if indeed_id in self._data["candidates"]:
            self._data["candidates"][indeed_id]["reminder_sent_at"] = self._now()
            self._data["candidates"][indeed_id]["reminder_status"] = status

    def get_candidates_needing_reminder(self, hours: int = 48) -> list:
        """
        Return candidates who:
          - Were sent an initial message >= `hours` ago
          - Have NOT yet submitted the Google Form
          - Have NOT yet received a reminder
          - Have NOT been flagged
        """
        cutoff = datetime.now(self.tz) - timedelta(hours=hours)
        result = []
        for c in self._data["candidates"].values():
            if (
                c.get("initial_message_status") == "sent"
                and c.get("reminder_sent_at") is None
                and c.get("form_submitted_at") is None
                and not c.get("flagged")
                and c.get("initial_message_sent_at") is not None
            ):
                try:
                    sent_at_str = c["initial_message_sent_at"]
                    sent_at = datetime.fromisoformat(sent_at_str)
                    # Ensure timezone-aware for comparison
                    if sent_at.tzinfo is None:
                        sent_at = self.tz.localize(sent_at)
                    if sent_at <= cutoff:
                        result.append(c)
                except (ValueError, TypeError):
                    pass
        return result

    def record_proactive_question(self, indeed_id: str, question: str) -> None:
        """Log a question a candidate asked proactively on Indeed."""
        if indeed_id in self._data["candidates"]:
            questions = self._data["candidates"][indeed_id].get("proactive_questions", [])
            questions.append({"question": question, "asked_at": self._now()})
            self._data["candidates"][indeed_id]["proactive_questions"] = questions

    # ------------------------------------------------------------------ #
    # Candidate matching – link form responses back to Indeed records
    # ------------------------------------------------------------------ #

    def _match_by_email_or_name(self, email: str, name: str) -> Optional[str]:
        """
        Find a candidate's key in self._data["candidates"] by email or name.
        Returns the key string, or None if no match.
        """
        email = (email or "").strip().lower()
        name = (name or "").strip().lower()

        for key, c in self._data["candidates"].items():
            if email and (c.get("email") or "").strip().lower() == email:
                return key
            if name and (c.get("name") or "").strip().lower() == name:
                return key
        return None

    # ------------------------------------------------------------------ #
    # Form submissions
    # ------------------------------------------------------------------ #

    def has_form_been_processed(self, identifier: str) -> bool:
        """
        Returns True if we have already processed a form submission for this
        email address or name.
        """
        identifier = (identifier or "").strip().lower()
        for c in self._data["candidates"].values():
            if c.get("form_submitted_at") is None:
                continue
            if (c.get("email") or "").strip().lower() == identifier:
                return True
            if (c.get("name") or "").strip().lower() == identifier:
                return True
            # Also check the synthetic key for form-only submissions
        synthetic_key = f"form_{identifier}"
        return synthetic_key in self._data["candidates"]

    def record_form_submission(
        self,
        identifier: str,
        form_data: dict,
        email: str = "",
        name: str = "",
    ) -> None:
        """
        Record a Google Form submission. Links it to an existing Indeed candidate
        if one can be matched by email or name; otherwise creates a form-only record.
        """
        matched_key = self._match_by_email_or_name(email, name)

        if matched_key:
            self._data["candidates"][matched_key]["form_submitted_at"] = self._now()
            self._data["candidates"][matched_key]["form_submission"] = form_data
            if email:
                self._data["candidates"][matched_key]["email"] = email
        else:
            # Candidate applied via a different channel or was not yet in log
            synthetic_key = f"form_{identifier}"
            self._data["candidates"][synthetic_key] = {
                "name": name or identifier,
                "role": form_data.get("position", "Unknown"),
                "indeed_id": None,
                "email": email or None,
                "initial_message_sent_at": None,
                "initial_message_status": None,
                "reminder_sent_at": None,
                "reminder_status": None,
                "form_submitted_at": self._now(),
                "form_submission": form_data,
                "interview_invite_sent_at": None,
                "interview_invite_status": None,
                "flagged": False,
                "flag_reason": None,
                "proactive_questions": [],
                "first_seen_at": self._now(),
            }

    # ------------------------------------------------------------------ #
    # Interview invites & flags
    # ------------------------------------------------------------------ #

    def record_interview_invite(self, identifier: str, status: str = "sent") -> None:
        matched_key = self._match_by_email_or_name(identifier, identifier)
        if matched_key:
            self._data["candidates"][matched_key]["interview_invite_sent_at"] = self._now()
            self._data["candidates"][matched_key]["interview_invite_status"] = status

    def record_flag(self, identifier: str, reason: str) -> None:
        matched_key = self._match_by_email_or_name(identifier, identifier)
        if matched_key:
            self._data["candidates"][matched_key]["flagged"] = True
            self._data["candidates"][matched_key]["flag_reason"] = reason

    # ------------------------------------------------------------------ #
    # Reporting helpers
    # ------------------------------------------------------------------ #

    def get_pipeline_stats(self) -> dict:
        candidates = list(self._data["candidates"].values())
        total = len(candidates)
        messaged = sum(1 for c in candidates if c.get("initial_message_sent_at"))
        form_submitted = sum(1 for c in candidates if c.get("form_submitted_at"))
        interview_invited = sum(1 for c in candidates if c.get("interview_invite_sent_at"))
        pending_form = sum(
            1
            for c in candidates
            if c.get("initial_message_sent_at")
            and not c.get("form_submitted_at")
            and not c.get("flagged")
        )
        flagged = sum(1 for c in candidates if c.get("flagged"))
        reminder_sent = sum(1 for c in candidates if c.get("reminder_sent_at"))

        # Breakdown by role
        roles: dict = {}
        for c in candidates:
            role = c.get("role", "Unknown")
            if role not in roles:
                roles[role] = {"total": 0, "messaged": 0, "form": 0, "invited": 0}
            roles[role]["total"] += 1
            if c.get("initial_message_sent_at"):
                roles[role]["messaged"] += 1
            if c.get("form_submitted_at"):
                roles[role]["form"] += 1
            if c.get("interview_invite_sent_at"):
                roles[role]["invited"] += 1

        return {
            "total": total,
            "messaged": messaged,
            "form_submitted": form_submitted,
            "interview_invited": interview_invited,
            "pending_form": pending_form,
            "flagged": flagged,
            "reminder_sent": reminder_sent,
            "by_role": roles,
        }

    def get_interview_candidates(self) -> list:
        """All candidates who have been sent an interview invite."""
        return [
            c
            for c in self._data["candidates"].values()
            if c.get("interview_invite_sent_at")
        ]

    def get_flagged_candidates(self) -> list:
        return [c for c in self._data["candidates"].values() if c.get("flagged")]

    def append_run(self, run_summary: dict) -> None:
        self._data["runs"].append(run_summary)
        # Cap run history at 90 entries to prevent unbounded growth
        self._data["runs"] = self._data["runs"][-90:]
