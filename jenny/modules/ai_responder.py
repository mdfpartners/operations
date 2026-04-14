"""
AI response generation for Jenny using the Anthropic Claude API.

Two responsibilities:
  1. answer_question() – Try to answer a candidate's Indeed question using
     the job description. Returns a confidence score so Jenny can decide
     whether to send the reply automatically or flag it for manual review.

  2. generate_leaderboard() – Score and rank interview-invited candidates
     on three dimensions: responsiveness, proactiveness, and relevant
     experience. Returns a sorted list for the daily report.
"""

import json
import logging
from typing import Any

import anthropic

logger = logging.getLogger(__name__)

# ── System prompts ─────────────────────────────────────────────────────────────

_ANSWER_SYSTEM = """\
You are a professional recruiting assistant for Mad Dog Facility Partners, \
a veteran-owned janitorial and facility services company. \
Your role is to answer candidate questions about job postings accurately and helpfully.

Guidelines:
- Be warm, professional, and concise.
- Only answer when you are confident the job description supports your response.
- Do not invent details not present in the job description.
- If the question asks for something not covered (pay negotiation, schedule \
exceptions, etc.), do not guess.

Always respond with a valid JSON object – no markdown, no prose outside the object:
{
    "confident": true | false,
    "confidence_score": <float 0.0–1.0>,
    "answer": "<your answer, or empty string if not confident>",
    "reason_for_uncertainty": "<brief reason if not confident, else empty string>"
}

Set confident=true only when confidence_score >= 0.75 AND the job description \
clearly addresses the question."""

_LEADERBOARD_SYSTEM = """\
You are a recruiting analyst scoring candidates for janitorial and facility \
services positions at Mad Dog Facility Partners (veteran-owned company).

Score each candidate on three dimensions (0–100):

1. Responsiveness – speed from initial Indeed contact to form completion.
   Scoring guide (based on days_to_form_completion if computable):
   < 1 day  → 90–100 | 1–2 days → 75–89 | 2–5 days → 55–74
   5–7 days → 35–54  | > 7 days → 15–34  | no form  → 0

2. Proactiveness – did the candidate ask questions or follow up on Indeed?
   0 questions → 15  | 1 question → 50 | 2 questions → 75 | 3+ → 92

3. Relevant Experience – janitorial, facility, cleaning, or customer service work.
   Strong janitorial/facility experience → 85–100
   Some customer-service or related work → 60–84
   Limited relevant experience           → 30–59
   No relevant experience               →  0–29

Compute total_score = round((responsiveness + proactiveness + relevant_experience) / 3).

Return a JSON array sorted by total_score descending – no markdown, no prose:
[
  {
    "name": "<string>",
    "indeed_id": "<string or null>",
    "scores": {
      "responsiveness": <int>,
      "proactiveness": <int>,
      "relevant_experience": <int>
    },
    "total_score": <int>,
    "summary": "<one concise sentence explaining this candidate's ranking>"
  }
]"""


class AIResponder:
    """Wraps the Anthropic Claude API for Jenny's two AI tasks."""

    def __init__(self, api_key: str, model: str = "claude-opus-4-6"):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _parse_json(self, raw: str) -> Any:
        """Strip markdown fences and parse JSON. Raises ValueError on failure."""
        text = raw.strip()
        if text.startswith("```"):
            # Remove opening fence (```json or ```)
            text = text.split("\n", 1)[-1]
            # Remove closing fence
            if "```" in text:
                text = text.rsplit("```", 1)[0]
        return json.loads(text.strip())

    def _call(self, system: str, user: str, max_tokens: int = 1024) -> str:
        response = self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        return response.content[0].text

    # ── Public API ────────────────────────────────────────────────────────────

    def answer_question(self, question: str, job_description: str) -> dict:
        """
        Ask Claude to answer a candidate's Indeed question.

        Returns a dict with:
          confident         bool    – whether to auto-send the reply
          confidence_score  float   – 0.0–1.0
          answer            str     – the reply text (empty if not confident)
          reason_for_uncertainty str
        """
        logger.info(f"Claude answering question: {question[:80]}…")

        user_prompt = (
            f"Job Description:\n{job_description}\n\n"
            f"Candidate Question:\n{question}\n\n"
            "Please answer this question based solely on the job description above."
        )

        try:
            raw = self._call(_ANSWER_SYSTEM, user_prompt, max_tokens=1024)
            result = self._parse_json(raw)
        except json.JSONDecodeError:
            logger.error("Claude returned invalid JSON for question answer.")
            result = {}
        except Exception as exc:
            logger.error(f"Claude API error (answer_question): {exc}")
            result = {}

        return {
            "confident": bool(result.get("confident", False)),
            "confidence_score": float(result.get("confidence_score", 0.0)),
            "answer": str(result.get("answer", "")),
            "reason_for_uncertainty": str(result.get("reason_for_uncertainty", "")),
        }

    def generate_leaderboard(self, candidates: list) -> list:
        """
        Score and rank interview-invited candidates.

        Accepts candidate dicts from LogManager.get_interview_candidates().
        Returns a list of scored, sorted candidate dicts for the report.
        """
        if not candidates:
            return []

        logger.info(f"Generating leaderboard for {len(candidates)} candidate(s)…")

        # Build a compact summary for each candidate to keep the prompt concise
        summaries = []
        for c in candidates:
            form = c.get("form_submission") or {}
            initial = c.get("initial_message_sent_at") or ""
            submitted = c.get("form_submitted_at") or ""
            proactive_count = len(c.get("proactive_questions", []))

            summaries.append(
                {
                    "name": c.get("name", "Unknown"),
                    "indeed_id": c.get("indeed_id"),
                    "role": c.get("role", ""),
                    "initial_message_sent_at": initial,
                    "form_submitted_at": submitted,
                    "proactive_questions_count": proactive_count,
                    "experience_description": form.get("experience", ""),
                    "position_applied_for": form.get("position", c.get("role", "")),
                }
            )

        user_prompt = (
            "Score and rank the following candidates:\n\n"
            + json.dumps(summaries, indent=2)
        )

        try:
            raw = self._call(_LEADERBOARD_SYSTEM, user_prompt, max_tokens=2048)
            leaderboard = self._parse_json(raw)
            if not isinstance(leaderboard, list):
                raise ValueError("Expected a JSON array")
            logger.info(f"Leaderboard generated with {len(leaderboard)} entry(ies).")
            return leaderboard
        except (json.JSONDecodeError, ValueError) as exc:
            logger.error(f"Claude returned invalid leaderboard JSON: {exc}")
            return []
        except Exception as exc:
            logger.error(f"Claude API error (generate_leaderboard): {exc}")
            return []
