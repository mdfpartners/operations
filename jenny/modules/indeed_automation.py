"""
Indeed Employer Center automation via Playwright.

Handles login, job listing, applicant enumeration, inbox scanning, and
outbound/reply messaging. Because Indeed is a React SPA that changes
selectors periodically, every interaction uses multiple fallback selectors
and captures a debug screenshot on failure.

NOTE: Indeed may present a CAPTCHA or 2-FA challenge during login.
If that happens the script will detect the block, save a screenshot, and
log an error. To resolve it, set `headless: false` in config.json and run
jenny.py manually once so you can complete the challenge. The session
cookies will then carry through the rest of the run.
"""

import asyncio
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Optional

from playwright.async_api import (
    async_playwright,
    Browser,
    BrowserContext,
    Page,
    TimeoutError as PlaywrightTimeout,
)

logger = logging.getLogger(__name__)

# ── URL constants ──────────────────────────────────────────────────────────────
_BASE = "https://employers.indeed.com"
_LOGIN_URL = "https://secure.indeed.com/account/login"
_JOBS_URL = f"{_BASE}/jobs"
_MESSAGES_URL = f"{_BASE}/messages"
_CANDIDATES_URL = f"{_BASE}/candidates"


class IndeedAutomation:
    """
    Async context manager that drives the Indeed Employer Center via Playwright.

    Usage::

        async with IndeedAutomation(config["indeed"]) as indeed:
            await indeed.login()
            jobs = await indeed.get_open_jobs()
            ...
    """

    def __init__(self, config: dict):
        self.email: str = config["email"]
        self.password: str = config["password"]
        self.employer_name: str = config.get("employer_name", "")
        self.headless: bool = config.get("headless", True)
        self.slow_mo: int = config.get("slow_mo", 500)
        self.screenshot_dir = Path(config.get("screenshot_dir", "screenshots"))
        self.screenshot_dir.mkdir(parents=True, exist_ok=True)

        self._playwright = None
        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None
        self._page: Optional[Page] = None

    # ── Lifecycle ────────────────────────────────────────────────────────────

    async def __aenter__(self):
        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(
            headless=self.headless,
            slow_mo=self.slow_mo,
            args=["--no-sandbox", "--disable-dev-shm-usage"],
        )
        self._context = await self._browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1280, "height": 900},
        )
        self._page = await self._context.new_page()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()

    # ── Internal helpers ─────────────────────────────────────────────────────

    async def _screenshot(self, label: str) -> None:
        """Save a debug screenshot. Never raises."""
        try:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            path = self.screenshot_dir / f"{label}_{ts}.png"
            await self._page.screenshot(path=str(path), full_page=True)
            logger.debug(f"Screenshot: {path}")
        except Exception:
            pass

    async def _wait_and_fill(self, selectors: list, value: str, timeout: int = 8000) -> bool:
        """Try each selector in order; fill the first that becomes visible."""
        for sel in selectors:
            try:
                await self._page.wait_for_selector(sel, timeout=timeout, state="visible")
                await self._page.fill(sel, value)
                return True
            except PlaywrightTimeout:
                continue
        return False

    async def _click_first(self, selectors: list, timeout: int = 6000) -> bool:
        """Click the first selector that becomes visible."""
        for sel in selectors:
            try:
                await self._page.wait_for_selector(sel, timeout=timeout, state="visible")
                await self._page.click(sel)
                return True
            except PlaywrightTimeout:
                continue
        return False

    async def _text_of(self, element, *child_selectors) -> str:
        """Return stripped text content of the first matching child element."""
        for sel in child_selectors:
            try:
                el = await element.query_selector(sel)
                if el:
                    text = (await el.text_content() or "").strip()
                    if text:
                        return text
            except Exception:
                continue
        return ""

    # ── Step 1: Login ────────────────────────────────────────────────────────

    async def login(self) -> bool:
        """
        Log in to the Indeed Employer Center.
        Returns True on success, False if blocked by CAPTCHA/2FA.
        """
        logger.info("Logging into Indeed Employer Center…")

        await self._page.goto(_LOGIN_URL, wait_until="domcontentloaded")
        await self._page.wait_for_timeout(1500)

        # ── Email field ──
        email_filled = await self._wait_and_fill(
            [
                "input[type='email']",
                "input[name='__email']",
                "input[autocomplete='email']",
                "#ifl-InputFormField-3",
                "input[data-testid='login-email-input']",
            ],
            self.email,
        )
        if not email_filled:
            await self._screenshot("login_no_email_field")
            logger.error("Could not find the email input on the Indeed login page.")
            return False

        # Click Continue (some flows split email and password onto two pages)
        await self._click_first(
            [
                "button[type='submit']",
                "button:has-text('Continue')",
                "button:has-text('Sign in')",
                "#login-submit-button",
                "[data-testid='login-submit-button']",
            ]
        )
        await self._page.wait_for_timeout(2500)

        # ── Password field ──
        pw_filled = await self._wait_and_fill(
            [
                "input[type='password']",
                "input[name='__password']",
                "input[data-testid='login-password-input']",
                "#ifl-InputFormField-password",
            ],
            self.password,
        )
        if not pw_filled:
            # Some login flows put both fields on one page – we may already
            # be logged in if the employer portal loaded.
            if _BASE in self._page.url:
                logger.info("Already reached employer portal (single-page login).")
                return True
            await self._screenshot("login_no_pw_field")
            logger.error("Could not find the password input on the Indeed login page.")
            return False

        await self._click_first(
            [
                "button[type='submit']",
                "button:has-text('Sign in')",
                "button:has-text('Continue')",
                "#login-submit-button",
                "[data-testid='login-submit-button']",
            ]
        )
        await self._page.wait_for_timeout(4000)

        current_url = self._page.url

        # ── Success check ──
        if _BASE in current_url or "employers.indeed" in current_url:
            logger.info("Indeed login successful.")
            return True

        # ── Challenge / 2FA ──
        if any(k in current_url for k in ("challenge", "verify", "2fa", "otp", "mfa")):
            await self._screenshot("login_2fa_challenge")
            logger.warning(
                "Indeed is requesting additional verification (2FA/CAPTCHA). "
                "Set 'headless': false in config.json and run Jenny manually once "
                "to complete the challenge."
            )
            return False

        # ── Last-resort redirect attempt ──
        await self._page.goto(_BASE, wait_until="networkidle", timeout=20000)
        if _BASE in self._page.url:
            logger.info("Reached employer portal after manual redirect.")
            return True

        await self._screenshot("login_failed")
        logger.error(f"Indeed login failed. Current URL: {self._page.url}")
        return False

    # ── Step 1: Get open jobs ────────────────────────────────────────────────

    async def get_open_jobs(self) -> list:
        """
        Return a list of open job dicts:
          { id, title, description, url }
        """
        logger.info("Fetching open job postings…")
        await self._page.goto(_JOBS_URL, wait_until="networkidle")
        await self._page.wait_for_timeout(2000)

        job_card_selectors = [
            "[data-testid='job-card']",
            "[data-testid='jobCard']",
            "[class*='JobCard']",
            "[class*='jobCard']",
            ".job-listing",
            "tr[data-job-id]",
        ]

        cards = []
        for sel in job_card_selectors:
            cards = await self._page.query_selector_all(sel)
            if cards:
                break

        if not cards:
            await self._screenshot("jobs_no_cards")
            logger.warning(
                "No job cards found with standard selectors. "
                "The Indeed UI may have changed – check screenshots/."
            )
            return []

        jobs = []
        for card in cards:
            try:
                # Extract job key from data attribute or nested href
                job_id = (
                    await card.get_attribute("data-job-id")
                    or await card.get_attribute("data-job-key")
                    or ""
                )
                if not job_id:
                    link = await card.query_selector("a[href*='job']")
                    if link:
                        href = await link.get_attribute("href") or ""
                        m = re.search(r"job[Kk]ey[=/_]([a-zA-Z0-9]+)", href)
                        if m:
                            job_id = m.group(1)

                title = await self._text_of(
                    card,
                    "[data-testid='job-title']",
                    "[class*='jobTitle']",
                    "[class*='JobTitle']",
                    "h2",
                    "h3",
                    "a[data-testid='job-link']",
                )

                if not (job_id or title):
                    continue

                description = await self._get_job_description(job_id) if job_id else ""

                jobs.append(
                    {
                        "id": job_id,
                        "title": title,
                        "description": description,
                        "url": f"{_CANDIDATES_URL}?jobKey={job_id}",
                    }
                )
            except Exception as exc:
                logger.warning(f"Error parsing job card: {exc}")
                continue

        logger.info(f"Found {len(jobs)} open job(s).")
        return jobs

    async def _get_job_description(self, job_id: str) -> str:
        """Fetch the plain-text job description from the edit/preview page."""
        if not job_id:
            return ""
        try:
            await self._page.goto(
                f"{_BASE}/job/{job_id}/edit",
                wait_until="networkidle",
                timeout=15000,
            )
            desc = await self._text_of(
                self._page,
                "[data-testid='job-description']",
                ".jobDescription",
                "textarea[name='jobDescription']",
                "[class*='description']",
            )
            # Fall back to the whole page body text if nothing specific found
            if not desc:
                desc = (await self._page.text_content("body") or "")[:3000]
            return desc.strip()
        except Exception:
            return ""

    # ── Step 2: Unanswered candidate questions ───────────────────────────────

    async def get_unanswered_questions(self, job: dict) -> list:
        """
        Scan the employer message inbox for inbound messages that have no reply,
        filtered to the given job where possible.

        Returns a list of dicts:
          { conversation_id, candidate_name, candidate_id, text, role }
        """
        logger.info(f"Checking inbox for unanswered questions – {job['title']}…")
        await self._page.goto(_MESSAGES_URL, wait_until="networkidle")
        await self._page.wait_for_timeout(2000)

        conv_selectors = [
            "[data-testid='conversation-item']",
            "[data-testid='conversationItem']",
            "[class*='ConversationItem']",
            "[class*='conversationItem']",
            ".conversation",
        ]

        conversations = []
        for sel in conv_selectors:
            conversations = await self._page.query_selector_all(sel)
            if conversations:
                break

        if not conversations:
            logger.info("No conversations found in inbox.")
            return []

        questions = []

        for conv in conversations:
            try:
                # Skip conversations that don't match this job (best-effort)
                job_el = await conv.query_selector(
                    "[data-testid='job-title'], [class*='jobTitle'], .role, .job"
                )
                if job_el:
                    conv_job = (await job_el.text_content() or "").strip()
                    if conv_job and job["title"] not in conv_job and conv_job not in job["title"]:
                        continue

                # Check for unread indicator
                unread_el = await conv.query_selector(
                    "[class*='unread'], [data-testid='unread'], .unread-badge"
                )

                candidate_name = await self._text_of(
                    conv,
                    "[data-testid='candidate-name']",
                    "[class*='candidateName']",
                    "[class*='CandidateName']",
                    "strong",
                    "b",
                )

                # Open the conversation
                await conv.click()
                await self._page.wait_for_timeout(1800)

                # Get the last message bubble
                all_bubbles = await self._page.query_selector_all(
                    "[data-testid='message-bubble'], "
                    "[class*='MessageBubble'], "
                    "[class*='messageBubble'], "
                    ".message-bubble"
                )

                if not all_bubbles:
                    await self._page.goto(_MESSAGES_URL, wait_until="networkidle")
                    await self._page.wait_for_timeout(1000)
                    continue

                last = all_bubbles[-1]
                last_cls = (await last.get_attribute("class") or "").lower()
                last_text = (await last.text_content() or "").strip()

                # Determine if the last message is inbound (from candidate)
                is_inbound = (
                    "inbound" in last_cls
                    or "candidate" in last_cls
                    or "received" in last_cls
                    or bool(unread_el)
                )

                if is_inbound and last_text:
                    conv_id = self._page.url.rstrip("/").split("/")[-1]
                    # Try to get candidate Indeed ID from URL or data attribute
                    candidate_id = ""
                    url_match = re.search(r"candidate[s]?[/=]([a-zA-Z0-9_-]+)", self._page.url)
                    if url_match:
                        candidate_id = url_match.group(1)

                    questions.append(
                        {
                            "conversation_id": conv_id,
                            "candidate_name": candidate_name,
                            "candidate_id": candidate_id,
                            "text": last_text,
                            "role": job["title"],
                        }
                    )

                # Return to inbox
                await self._page.goto(_MESSAGES_URL, wait_until="networkidle")
                await self._page.wait_for_timeout(1000)
                # Re-query conversations since the page reloaded
                conversations = []
                for sel in conv_selectors:
                    conversations = await self._page.query_selector_all(sel)
                    if conversations:
                        break

            except Exception as exc:
                logger.warning(f"Error reading conversation: {exc}")
                await self._page.goto(_MESSAGES_URL, wait_until="networkidle")
                await self._page.wait_for_timeout(1000)
                continue

        logger.info(
            f"Found {len(questions)} unanswered question(s) for '{job['title']}'."
        )
        return questions

    async def reply_to_question(self, conversation_id: str, reply: str) -> bool:
        """Send a reply inside an existing Indeed conversation thread."""
        try:
            await self._page.goto(
                f"{_MESSAGES_URL}/{conversation_id}",
                wait_until="networkidle",
            )
            await self._page.wait_for_timeout(1500)

            typed = await self._wait_and_fill(
                [
                    "[data-testid='message-input']",
                    "textarea[placeholder*='message' i]",
                    "[contenteditable='true'][aria-label*='message' i]",
                    "[contenteditable='true']",
                    "textarea",
                ],
                reply,
            )
            if not typed:
                await self._screenshot(f"reply_no_input_{conversation_id}")
                return False

            sent = await self._click_first(
                [
                    "[data-testid='send-button']",
                    "button:has-text('Send')",
                    "button[aria-label*='Send' i]",
                    "button[type='submit']",
                    "[class*='sendButton']",
                    "[class*='SendButton']",
                ]
            )
            if sent:
                await self._page.wait_for_timeout(1500)
                logger.info(f"Reply sent to conversation {conversation_id}.")
            else:
                await self._screenshot(f"reply_no_send_btn_{conversation_id}")
            return sent

        except Exception as exc:
            await self._screenshot(f"reply_error_{conversation_id}")
            logger.error(f"Error replying to conversation {conversation_id}: {exc}")
            return False

    # ── Steps 3-4: Applicant list & initial messaging ────────────────────────

    async def get_applicants(self, job: dict) -> list:
        """
        Return all applicants for a given job as a list of dicts:
          { id, name, role, job_id }
        Handles pagination automatically.
        """
        logger.info(f"Fetching applicants for '{job['title']}'…")

        if job.get("id"):
            url = f"{_CANDIDATES_URL}?jobKey={job['id']}"
        else:
            url = _CANDIDATES_URL

        await self._page.goto(url, wait_until="networkidle")
        await self._page.wait_for_timeout(2000)

        card_selectors = [
            "[data-testid='candidate-card']",
            "[data-testid='applicant-row']",
            "[class*='CandidateCard']",
            "[class*='candidateCard']",
            ".candidate-card",
            "tr[data-applicant-id]",
            "tr[data-candidate-id]",
        ]

        applicants: list = []

        while True:
            cards = []
            for sel in card_selectors:
                cards = await self._page.query_selector_all(sel)
                if cards:
                    break

            for card in cards:
                try:
                    app_id = (
                        await card.get_attribute("data-applicant-id")
                        or await card.get_attribute("data-candidate-id")
                        or ""
                    )
                    if not app_id:
                        link = await card.query_selector("a[href*='candidate']")
                        if link:
                            href = await link.get_attribute("href") or ""
                            m = re.search(r"candidate[s]?[/=]([a-zA-Z0-9_-]+)", href)
                            if m:
                                app_id = m.group(1)

                    name = await self._text_of(
                        card,
                        "[data-testid='candidate-name']",
                        "[class*='candidateName']",
                        "[class*='CandidateName']",
                        ".candidate-name",
                        "h3",
                        "h4",
                        "strong",
                    )

                    if app_id or name:
                        applicants.append(
                            {
                                "id": app_id,
                                "name": name,
                                "role": job["title"],
                                "job_id": job.get("id", ""),
                            }
                        )
                except Exception as exc:
                    logger.warning(f"Error parsing applicant card: {exc}")
                    continue

            # Pagination
            next_btn = await self._page.query_selector(
                "button[aria-label='Next page']:not([disabled]), "
                "a[aria-label='Next']:not([disabled]), "
                "[data-testid='pagination-next']:not([disabled]), "
                "button:has-text('Next'):not([disabled])"
            )
            if next_btn:
                await next_btn.click()
                await self._page.wait_for_timeout(2000)
            else:
                break

        logger.info(f"Found {len(applicants)} applicant(s) for '{job['title']}'.")
        return applicants

    async def send_message(self, applicant_id: str, message: str) -> bool:
        """
        Send a message to an applicant via Indeed's employer messaging.
        Tries the candidate profile page first, then the new-message URL.
        """
        try:
            # Attempt 1: candidate profile page
            await self._page.goto(
                f"{_BASE}/candidates/{applicant_id}",
                wait_until="networkidle",
                timeout=15000,
            )
            await self._page.wait_for_timeout(1800)

            msg_btn_clicked = await self._click_first(
                [
                    "button:has-text('Message')",
                    "button:has-text('Send message')",
                    "[data-testid='message-button']",
                    "[class*='MessageButton']",
                    "a[href*='messages']",
                ]
            )

            if not msg_btn_clicked:
                # Attempt 2: direct new-message URL
                await self._page.goto(
                    f"{_MESSAGES_URL}/new?applicantId={applicant_id}",
                    wait_until="networkidle",
                    timeout=15000,
                )

            await self._page.wait_for_timeout(1500)

            typed = await self._wait_and_fill(
                [
                    "[data-testid='message-input']",
                    "textarea[placeholder*='message' i]",
                    "[contenteditable='true'][aria-label*='message' i]",
                    "[contenteditable='true']",
                    "textarea",
                ],
                message,
            )
            if not typed:
                await self._screenshot(f"send_no_input_{applicant_id}")
                return False

            sent = await self._click_first(
                [
                    "[data-testid='send-button']",
                    "button:has-text('Send')",
                    "button[aria-label*='Send' i]",
                    "button[type='submit']",
                    "[class*='sendButton']",
                    "[class*='SendButton']",
                ]
            )
            if sent:
                await self._page.wait_for_timeout(1500)
                logger.info(f"Message sent to applicant {applicant_id}.")
            else:
                await self._screenshot(f"send_no_btn_{applicant_id}")
            return sent

        except Exception as exc:
            await self._screenshot(f"send_error_{applicant_id}")
            logger.error(f"Error sending message to applicant {applicant_id}: {exc}")
            return False
