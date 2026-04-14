"""
Daily pipeline report generator for Jenny.

Produces an HTML email (with a plain-text fallback) that includes:
  - Recruiting pipeline stats with an at-a-glance stat-box row
  - Per-role breakdown table
  - Candidate leaderboard (interview-invited candidates ranked by AI scores)
  - Flagged items table (unanswered questions, felony disclosures, system errors)
  - Today's actions summary
"""

from datetime import date
from typing import Optional


class ReportGenerator:
    """Generates the daily HTML + plain-text recruiting pipeline report."""

    @staticmethod
    def generate(
        pipeline_stats: dict,
        leaderboard: list,
        run_summary: dict,
        flagged_items: list,
        company_name: str = "Mad Dog Facility Partners",
    ) -> tuple:
        """
        Build and return (html_string, plaintext_string).

        Parameters
        ----------
        pipeline_stats : dict   from LogManager.get_pipeline_stats()
        leaderboard    : list   from AIResponder.generate_leaderboard()
        run_summary    : dict   { run_at, actions: [...], flagged_items: [...] }
        flagged_items  : list   combined list of flagged dicts for the report
        company_name   : str
        """
        today = date.today().strftime("%B %d, %Y")
        actions_count = len(run_summary.get("actions", []))

        html = ReportGenerator._html(
            today, company_name, pipeline_stats, leaderboard, flagged_items, actions_count
        )
        text = ReportGenerator._text(
            today, company_name, pipeline_stats, leaderboard, flagged_items, actions_count
        )
        return html, text

    # ── HTML report ───────────────────────────────────────────────────────────

    @staticmethod
    def _stat_box(num, label: str, color: str = "#1a5fa8") -> str:
        return (
            f'<div class="stat-box">'
            f'<div class="stat-num" style="color:{color};">{num}</div>'
            f'<div class="stat-label">{label}</div>'
            f"</div>"
        )

    @staticmethod
    def _html(
        today: str,
        company_name: str,
        stats: dict,
        leaderboard: list,
        flagged: list,
        actions_count: int,
    ) -> str:

        # ── Stat boxes ──
        stat_boxes = "".join(
            [
                ReportGenerator._stat_box(stats["total"], "Total Applicants"),
                ReportGenerator._stat_box(stats["messaged"], "Messaged on Indeed"),
                ReportGenerator._stat_box(stats["form_submitted"], "Forms Submitted"),
                ReportGenerator._stat_box(stats["interview_invited"], "Interview Invited"),
                ReportGenerator._stat_box(stats["pending_form"], "Pending Form"),
                ReportGenerator._stat_box(
                    stats["flagged"], "Flagged", color="#c0392b"
                ),
            ]
        )

        # ── By-role table rows ──
        role_rows = ""
        for role, rs in stats.get("by_role", {}).items():
            role_rows += (
                f"<tr>"
                f"<td>{role}</td>"
                f"<td>{rs['total']}</td>"
                f"<td>{rs['messaged']}</td>"
                f"<td>{rs['form']}</td>"
                f"<td>{rs['invited']}</td>"
                f"</tr>"
            )
        if not role_rows:
            role_rows = "<tr><td colspan='5' style='color:#888;'>No roles yet.</td></tr>"

        # ── Leaderboard rows ──
        lb_rows = ""
        for rank, c in enumerate(leaderboard, 1):
            scores = c.get("scores", {})
            resp = scores.get("responsiveness", "—")
            pro = scores.get("proactiveness", "—")
            exp = scores.get("relevant_experience", "—")
            total = c.get("total_score", "—")
            summary = c.get("summary", "")
            lb_rows += (
                f"<tr>"
                f"<td><strong>#{rank}</strong></td>"
                f"<td>{c.get('name', 'Unknown')}</td>"
                f"<td>{resp}</td>"
                f"<td>{pro}</td>"
                f"<td>{exp}</td>"
                f"<td><strong>{total}</strong></td>"
                f"<td><em>{summary}</em></td>"
                f"</tr>"
            )
        if not lb_rows:
            lb_rows = (
                "<tr><td colspan='7' style='color:#888;'>"
                "No interview candidates yet."
                "</td></tr>"
            )

        # ── Flagged rows ──
        flag_rows = ""
        for item in flagged:
            flag_type = item.get("type", "").replace("_", " ").title()
            candidate = item.get("candidate", "Unknown")
            role = item.get("role", "")
            detail = item.get("reason") or item.get("question") or ""
            flag_rows += (
                f'<tr style="background:#fff8e1;">'
                f"<td>{flag_type}</td>"
                f"<td>{candidate}</td>"
                f"<td>{role}</td>"
                f"<td style='max-width:300px;word-break:break-word;'>{detail}</td>"
                f"</tr>"
            )
        if not flag_rows:
            flag_rows = (
                "<tr><td colspan='4' style='color:#888;'>"
                "No flagged items today."
                "</td></tr>"
            )

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<style>
  body {{
    font-family: Arial, sans-serif;
    max-width: 820px;
    margin: 0 auto;
    color: #222;
    font-size: 14px;
    line-height: 1.55;
  }}
  h1 {{ color: #0d3c6e; margin-bottom: 2px; }}
  h2 {{
    color: #1a5fa8;
    border-bottom: 2px solid #1a5fa8;
    padding-bottom: 4px;
    margin-top: 30px;
  }}
  .meta {{ color: #666; font-size: 13px; margin-bottom: 20px; }}
  .stat-row {{ display: flex; flex-wrap: wrap; gap: 10px; margin: 16px 0; }}
  .stat-box {{
    background: #f0f5ff;
    border: 1px solid #bed0f7;
    border-radius: 8px;
    padding: 14px 20px;
    text-align: center;
    min-width: 110px;
  }}
  .stat-num {{ font-size: 2em; font-weight: bold; }}
  .stat-label {{ font-size: 0.78em; color: #555; margin-top: 2px; }}
  table {{
    border-collapse: collapse;
    width: 100%;
    margin-bottom: 16px;
    font-size: 13px;
  }}
  th {{
    background: #1a5fa8;
    color: #fff;
    padding: 8px 12px;
    text-align: left;
  }}
  td {{
    padding: 7px 12px;
    border-bottom: 1px solid #e0e8f5;
    vertical-align: top;
  }}
  tr:nth-child(even) td {{ background: #f7f9fd; }}
  tr:hover td {{ background: #eef3fc; }}
  footer {{
    color: #aaa;
    font-size: 11px;
    margin-top: 36px;
    border-top: 1px solid #ddd;
    padding-top: 10px;
  }}
</style>
</head>
<body>
<h1>Jenny Daily Recruiting Report</h1>
<p class="meta">
  <strong>{company_name}</strong> &nbsp;&bull;&nbsp; {today}
  &nbsp;&bull;&nbsp; {actions_count} action(s) taken today
</p>

<h2>Pipeline Overview</h2>
<div class="stat-row">{stat_boxes}</div>

<h2>Breakdown by Role</h2>
<table>
  <tr>
    <th>Role</th>
    <th>Applicants</th>
    <th>Messaged</th>
    <th>Form Submitted</th>
    <th>Interview Invited</th>
  </tr>
  {role_rows}
</table>

<h2>Interview Candidate Leaderboard</h2>
<p style="color:#555;font-size:13px;">
  Ranked by AI-scored average of Responsiveness, Proactiveness, and Relevant Experience (each 0–100).
</p>
<table>
  <tr>
    <th>Rank</th>
    <th>Name</th>
    <th>Responsiveness</th>
    <th>Proactiveness</th>
    <th>Experience</th>
    <th>Total</th>
    <th>Summary</th>
  </tr>
  {lb_rows}
</table>

<h2>Flagged Items</h2>
<table>
  <tr>
    <th>Type</th>
    <th>Candidate</th>
    <th>Role</th>
    <th>Details</th>
  </tr>
  {flag_rows}
</table>

<footer>
  Generated by Jenny Recruiting Automation &bull; {company_name} &bull; {today}
</footer>
</body>
</html>"""

    # ── Plain-text report ─────────────────────────────────────────────────────

    @staticmethod
    def _text(
        today: str,
        company_name: str,
        stats: dict,
        leaderboard: list,
        flagged: list,
        actions_count: int,
    ) -> str:
        sep = "=" * 56
        thin = "-" * 56
        lines = [
            sep,
            "JENNY DAILY RECRUITING REPORT",
            f"{company_name}  |  {today}",
            f"{actions_count} action(s) taken today",
            sep,
            "",
            "PIPELINE OVERVIEW",
            thin,
            f"  Total Applicants    : {stats['total']}",
            f"  Messaged on Indeed  : {stats['messaged']}",
            f"  Forms Submitted     : {stats['form_submitted']}",
            f"  Interview Invited   : {stats['interview_invited']}",
            f"  Pending Form        : {stats['pending_form']}",
            f"  Reminders Sent      : {stats['reminder_sent']}",
            f"  Flagged             : {stats['flagged']}",
            "",
            "BY ROLE",
            thin,
        ]

        for role, rs in stats.get("by_role", {}).items():
            lines.append(
                f"  {role:<35} "
                f"tot={rs['total']}  msg={rs['messaged']}  "
                f"form={rs['form']}  inv={rs['invited']}"
            )

        lines += ["", "INTERVIEW CANDIDATE LEADERBOARD", thin]
        if leaderboard:
            for rank, c in enumerate(leaderboard, 1):
                s = c.get("scores", {})
                lines.append(
                    f"  #{rank:<3} {c.get('name', 'Unknown'):<28} "
                    f"Total={c.get('total_score','?'):>3}  "
                    f"[R={s.get('responsiveness','?')} "
                    f"P={s.get('proactiveness','?')} "
                    f"E={s.get('relevant_experience','?')}]"
                )
                if c.get("summary"):
                    lines.append(f"       {c['summary']}")
        else:
            lines.append("  No interview candidates yet.")

        lines += ["", "FLAGGED ITEMS", thin]
        if flagged:
            for item in flagged:
                flag_type = item.get("type", "").replace("_", " ").upper()
                candidate = item.get("candidate", "Unknown")
                role = item.get("role", "")
                detail = item.get("reason") or item.get("question") or ""
                lines.append(f"  [{flag_type}] {candidate} / {role}")
                if detail:
                    # Wrap long detail text
                    words = detail.split()
                    line_buf = "    "
                    for word in words:
                        if len(line_buf) + len(word) > 72:
                            lines.append(line_buf)
                            line_buf = "    " + word + " "
                        else:
                            line_buf += word + " "
                    if line_buf.strip():
                        lines.append(line_buf)
        else:
            lines.append("  No flagged items today.")

        lines += ["", sep, "Generated by Jenny Recruiting Automation", sep]
        return "\n".join(lines)
