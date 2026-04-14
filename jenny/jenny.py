#!/usr/bin/env python3
"""
Jenny – Recruiting Automation Agent
Mad Dog Facility Partners

Runs every morning via cron job. Executes all 8 pipeline steps in order:

  1  Login to Indeed, get open jobs
  2  Scan inbox for unanswered questions; auto-reply via Claude or flag
  3  Pull applicant list for each open job
  4  Send initial outreach message to every new (uncontacted) applicant
  4.5 Send 48-hour reminder to applicants who haven't completed the form yet
  5  Pull Google Form responses for new submissions
  6  Review each new submission; send interview invite or flag for felony
  7  Generate and email the daily pipeline report
  8  Persist all changes to the JSON log

Usage:
    python jenny.py [--config path/to/config.json] [--dry-run]

    --dry-run  Log all planned actions but send no messages / emails.
"""

import argparse
import asyncio
import json
import logging
import sys
from datetime import datetime
from pathlib import Path

import pytz

from modules.ai_responder import AIResponder
from modules.gmail_client import GmailClient
from modules.google_sheets import GoogleSheetsReader
from modules.indeed_automation import IndeedAutomation
from modules.log_manager import LogManager
from modules.report_generator import ReportGenerator

# ── Logging setup ─────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)-8s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler("jenny.log"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger("jenny")


# ── Config ─────────────────────────────────────────────────────────────────────

def load_config(path: str = "config.json") -> dict:
    p = Path(path)
    if not p.exists():
        logger.error(
            f"Config file '{path}' not found. "
            "Copy config.example.json → config.json and fill in your credentials."
        )
        sys.exit(1)
    with open(p) as f:
        return json.load(f)


# ── Message templates ──────────────────────────────────────────────────────────

def _initial_message(config: dict, form_link: str) -> str:
    company = config["company"]["name"]
    tagline = config["company"].get("tagline", "a veteran-owned facility services company")
    return (
        f"Hi there,\n\n"
        f"Thank you for applying to {company}! We're thrilled you're interested.\n\n"
        f"We are {tagline}, and we're proud to build a team that reflects our values "
        f"of integrity, reliability, and service excellence.\n\n"
        f"The next step in our process is a short form that helps us get to know you better:\n\n"
        f"{form_link}\n\n"
        f"It only takes a few minutes. Once you've submitted it we'll be in touch quickly.\n\n"
        f"Looking forward to connecting!\n\n"
        f"Best,\n"
        f"The {company} Recruiting Team"
    )


def _reminder_message(config: dict, form_link: str) -> str:
    company = config["company"]["name"]
    return (
        f"Hi again,\n\n"
        f"We wanted to follow up on our message about your application to {company}.\n\n"
        f"We're still very interested in you and would love to move your application forward. "
        f"If you haven't had a chance yet, please take a few minutes to complete our form:\n\n"
        f"{form_link}\n\n"
        f"If you have any questions or need anything from us, just reply here – we're happy to help.\n\n"
        f"Best,\n"
        f"The {company} Recruiting Team"
    )


# ── Main workflow ──────────────────────────────────────────────────────────────

async def run(config: dict, dry_run: bool = False) -> None:
    tz = pytz.timezone(config.get("timezone", "America/Phoenix"))
    now = datetime.now(tz)

    logger.info(
        f"{'[DRY-RUN] ' if dry_run else ''}Jenny starting run at {now.isoformat()}"
    )

    # Initialise components
    log_manager = LogManager(
        config.get("log_file", "jenny_log.json"),
        timezone_str=config.get("timezone", "America/Phoenix"),
    )
    ai = AIResponder(
        api_key=config["anthropic"]["api_key"],
        model=config["anthropic"].get("model", "claude-opus-4-6"),
    )
    gmail = GmailClient(config["gmail"])
    sheets = GoogleSheetsReader(config["google"])

    form_link = config["google"]["form_link"]
    company_name = config["company"]["name"]
    reminder_hours = int(config.get("reminder_hours", 48))

    run_summary: dict = {
        "run_at": now.isoformat(),
        "dry_run": dry_run,
        "actions": [],
        "flagged_items": [],
    }

    # ── Steps 1–4.5 – Indeed automation ──────────────────────────────────────
    try:
        async with IndeedAutomation(config["indeed"]) as indeed:

            # ── Step 1: Login + open jobs ─────────────────────────────────
            logger.info("─── Step 1: Login & open jobs ───")
            logged_in = await indeed.login() if not dry_run else True

            if not logged_in:
                msg = (
                    "Indeed login failed – manual verification may be required. "
                    "Set headless=false in config.json and run jenny.py once manually."
                )
                logger.error(msg)
                run_summary["flagged_items"].append(
                    {"type": "system_error", "candidate": "N/A", "role": "N/A", "reason": msg}
                )
                # Skip all Indeed steps
                open_jobs = []
            else:
                open_jobs = await indeed.get_open_jobs() if not dry_run else []
                logger.info(f"Open jobs found: {len(open_jobs)}")

            # ── Step 2: Auto-reply or flag unanswered questions ───────────
            logger.info("─── Step 2: Unanswered candidate questions ───")
            for job in open_jobs:
                questions = await indeed.get_unanswered_questions(job)
                for q in questions:
                    # Log the proactive question in the candidate record
                    if q.get("candidate_id"):
                        log_manager.record_proactive_question(
                            q["candidate_id"], q["text"]
                        )

                    ai_resp = ai.answer_question(q["text"], job.get("description", ""))

                    if ai_resp["confident"]:
                        sent = (
                            await indeed.reply_to_question(q["conversation_id"], ai_resp["answer"])
                            if not dry_run
                            else True
                        )
                        action_status = "sent" if sent else "failed"
                        run_summary["actions"].append(
                            {
                                "type": "auto_reply",
                                "candidate": q["candidate_name"],
                                "role": job["title"],
                                "status": action_status,
                                "confidence": ai_resp["confidence_score"],
                            }
                        )
                        logger.info(
                            f"Auto-reply [{action_status}] → {q['candidate_name']} "
                            f"({job['title']}) confidence={ai_resp['confidence_score']:.2f}"
                        )
                    else:
                        run_summary["flagged_items"].append(
                            {
                                "type": "unanswered_question",
                                "candidate": q["candidate_name"],
                                "role": job["title"],
                                "question": q["text"],
                                "reason": (
                                    f"Claude not confident (score={ai_resp['confidence_score']:.2f}). "
                                    f"{ai_resp['reason_for_uncertainty']}"
                                ),
                            }
                        )
                        logger.info(
                            f"Flagged unanswered question from {q['candidate_name']} "
                            f"({job['title']}) – needs manual reply."
                        )

            # ── Steps 3 & 4: Initial outreach to new applicants ───────────
            logger.info("─── Steps 3–4: Initial outreach to new applicants ───")
            initial_msg = _initial_message(config, form_link)

            for job in open_jobs:
                applicants = await indeed.get_applicants(job)
                for applicant in applicants:
                    if log_manager.has_been_contacted(applicant["id"]):
                        continue  # Already messaged in a prior run

                    sent = (
                        await indeed.send_message(applicant["id"], initial_msg)
                        if not dry_run
                        else True
                    )
                    status = "sent" if sent else "failed"
                    log_manager.record_initial_message(
                        indeed_id=applicant["id"],
                        name=applicant["name"],
                        role=job["title"],
                        status=status,
                    )
                    run_summary["actions"].append(
                        {
                            "type": "initial_message",
                            "candidate": applicant["name"],
                            "indeed_id": applicant["id"],
                            "role": job["title"],
                            "status": status,
                        }
                    )
                    logger.info(
                        f"Initial message [{status}] → {applicant['name']} ({job['title']})"
                    )

            # ── Step 4.5: 48-hour reminders ───────────────────────────────
            logger.info("─── Step 4.5: Follow-up reminders ───")
            reminder_msg = _reminder_message(config, form_link)
            for candidate in log_manager.get_candidates_needing_reminder(hours=reminder_hours):
                if not candidate.get("indeed_id"):
                    continue  # Can't message without an Indeed ID

                sent = (
                    await indeed.send_message(candidate["indeed_id"], reminder_msg)
                    if not dry_run
                    else True
                )
                status = "sent" if sent else "failed"
                log_manager.record_reminder_sent(candidate["indeed_id"], status)
                run_summary["actions"].append(
                    {
                        "type": "reminder",
                        "candidate": candidate["name"],
                        "indeed_id": candidate["indeed_id"],
                        "role": candidate["role"],
                        "status": status,
                    }
                )
                logger.info(
                    f"Reminder [{status}] → {candidate['name']} "
                    f"(initial msg sent {candidate['initial_message_sent_at']})"
                )

    except Exception as exc:
        logger.exception(f"Indeed automation block failed: {exc}")
        run_summary["flagged_items"].append(
            {
                "type": "system_error",
                "candidate": "N/A",
                "role": "N/A",
                "reason": f"Indeed automation error: {exc}",
            }
        )

    # ── Steps 5–6 – Google Form processing ───────────────────────────────────
    logger.info("─── Steps 5–6: Google Form submissions ───")
    try:
        form_responses = sheets.get_responses() if not dry_run else []
        for response in form_responses:
            email = response.get("email", "").strip()
            name = response.get("full_name", "").strip()
            identifier = email or name

            if not identifier:
                continue

            if log_manager.has_form_been_processed(identifier):
                continue  # Already handled in a prior run

            # Record the submission first
            log_manager.record_form_submission(
                identifier=identifier,
                form_data=response,
                email=email,
                name=name,
            )

            if sheets.has_recent_felony(response):
                # Flag – do not invite
                flag_reason = "Candidate disclosed a recent felony conviction on the application form."
                log_manager.record_flag(identifier, flag_reason)
                run_summary["flagged_items"].append(
                    {
                        "type": "felony_disclosure",
                        "candidate": name or email,
                        "role": response.get("position", "Unknown"),
                        "reason": flag_reason,
                    }
                )
                run_summary["actions"].append(
                    {
                        "type": "felony_flag",
                        "candidate": name or email,
                        "role": response.get("position", "Unknown"),
                        "status": "flagged",
                    }
                )
                logger.info(f"Flagged (felony) → {name or email}")
            else:
                # Send interview invite
                sent = gmail.send_interview_invite(response, company_name) if not dry_run else True
                status = "sent" if sent else "failed"
                log_manager.record_interview_invite(identifier, status)
                run_summary["actions"].append(
                    {
                        "type": "interview_invite",
                        "candidate": name or email,
                        "role": response.get("position", "Unknown"),
                        "status": status,
                    }
                )
                logger.info(
                    f"Interview invite [{status}] → {name or email} "
                    f"({response.get('position', 'Unknown')})"
                )

    except Exception as exc:
        logger.exception(f"Form processing block failed: {exc}")
        run_summary["flagged_items"].append(
            {
                "type": "system_error",
                "candidate": "N/A",
                "role": "N/A",
                "reason": f"Google Form processing error: {exc}",
            }
        )

    # ── Step 7 – Daily report ─────────────────────────────────────────────────
    logger.info("─── Step 7: Daily report ───")
    try:
        pipeline_stats = log_manager.get_pipeline_stats()
        interview_candidates = log_manager.get_interview_candidates()
        leaderboard = ai.generate_leaderboard(interview_candidates)

        # Merge run-time flags with any persistent flags from the log
        historical_flagged = [
            {
                "type": "candidate_flag",
                "candidate": c.get("name", "Unknown"),
                "role": c.get("role", ""),
                "reason": c.get("flag_reason", ""),
            }
            for c in log_manager.get_flagged_candidates()
            # Avoid duplicating items already in run_summary["flagged_items"]
            if not any(
                f.get("candidate") == c.get("name")
                for f in run_summary["flagged_items"]
            )
        ]
        all_flagged = run_summary["flagged_items"] + historical_flagged

        report_html, report_text = ReportGenerator.generate(
            pipeline_stats=pipeline_stats,
            leaderboard=leaderboard,
            run_summary=run_summary,
            flagged_items=all_flagged,
            company_name=company_name,
        )

        if not dry_run:
            gmail.send_daily_report(report_html, report_text)
        else:
            logger.info("[DRY-RUN] Would send daily report. Plain-text preview:\n" + report_text)

    except Exception as exc:
        logger.exception(f"Report generation block failed: {exc}")

    # ── Step 8 – Save log ─────────────────────────────────────────────────────
    logger.info("─── Step 8: Saving log ───")
    run_summary["actions_count"] = len(run_summary["actions"])
    run_summary["flagged_count"] = len(run_summary["flagged_items"])
    log_manager.append_run(
        {
            "run_at": run_summary["run_at"],
            "dry_run": dry_run,
            "actions_count": run_summary["actions_count"],
            "flagged_count": run_summary["flagged_count"],
        }
    )
    log_manager.save()

    logger.info(
        f"{'[DRY-RUN] ' if dry_run else ''}Run complete – "
        f"{run_summary['actions_count']} action(s), "
        f"{run_summary['flagged_count']} flagged item(s)."
    )


# ── Entry point ────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="Jenny – Recruiting Automation Agent")
    parser.add_argument(
        "--config",
        default="config.json",
        help="Path to config file (default: config.json)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Log all planned actions without sending any messages or emails.",
    )
    args = parser.parse_args()

    config = load_config(args.config)
    asyncio.run(run(config, dry_run=args.dry_run))


if __name__ == "__main__":
    main()
