# Jenny – Recruiting Automation Agent

Automated recruiting pipeline for **Mad Dog Facility Partners**, a veteran-owned
janitorial and facility services company. Jenny runs every morning via cron job and
handles the full top-of-funnel workflow: contacting Indeed applicants, following up,
processing Google Form submissions, sending interview invites, and emailing you a
daily pipeline report.

---

## Table of Contents

1. [What Jenny does (step-by-step)](#what-jenny-does)
2. [Tech stack](#tech-stack)
3. [Prerequisites](#prerequisites)
4. [Installation](#installation)
5. [Configuration](#configuration)
6. [Google Sheets API setup](#google-sheets-api-setup)
7. [Gmail API setup](#gmail-api-setup)
8. [One-time authorization](#one-time-authorization)
9. [Running manually](#running-manually)
10. [Scheduling with cron](#scheduling-with-cron)
11. [Log file reference](#log-file-reference)
12. [Troubleshooting](#troubleshooting)

---

## What Jenny does

Jenny executes 8 steps in order on every run:

| Step | Action |
|------|--------|
| 1 | Log into your Indeed Employer Center via Playwright |
| 2 | Scan the inbox for unanswered candidate questions. Feed each question + the job description to Claude. If Claude is confident (score ≥ 0.75), send the reply automatically. Otherwise, add the item to the flagged list for your morning report. |
| 3–4 | Pull the applicant list for every open role. Send an initial outreach message (with your Google Form link) to every applicant not yet in the log. |
| 4.5 | Send a one-time follow-up reminder to applicants who were messaged ≥ 48 hours ago and still haven't submitted the form. |
| 5–6 | Pull new Google Form responses. For each new submission: check for a recent felony disclosure. If clean → send a first-round interview invite via Gmail. If flagged → add to the report. |
| 7 | Generate an HTML pipeline report with stats, a candidate leaderboard (scored by Claude on responsiveness, proactiveness, and experience), and all flagged items. Email it to you. |
| 8 | Write all changes to the local JSON log. |

---

## Tech stack

| Library | Purpose |
|---------|---------|
| `playwright` | Browser automation for Indeed Employer Center |
| `anthropic` | Claude API – auto-replies and leaderboard scoring |
| `google-api-python-client` | Google Sheets API (read form responses) |
| `google-auth-oauthlib` | OAuth2 authorization for Google APIs |
| `google-auth` | Token refresh |
| `pytz` | Timezone-aware timestamps |

---

## Prerequisites

- Python 3.10+
- A browser (Playwright will download Chromium automatically)
- An Indeed Employer Center account with active job postings
- A Google Form collecting candidate information, linked to a Google Sheet
- A Gmail account to send recruiting emails from
- An Anthropic API key (claude.ai/api)

---

## Installation

```bash
# Clone / navigate to the jenny directory
cd jenny

# Create a virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate          # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install Playwright browser
playwright install chromium
```

---

## Configuration

```bash
cp config.example.json config.json
```

Open `config.json` and fill in every field:

```jsonc
{
  "indeed": {
    "email": "your-employer@indeed.com",   // Indeed employer login email
    "password": "••••••••",                // Indeed employer login password
    "employer_name": "Mad Dog Facility Partners",
    "headless": true,                      // false = show browser window (for debugging)
    "slow_mo": 500                         // ms delay between Playwright actions
  },
  "google": {
    "form_link": "https://forms.gle/...",  // Full URL of your Google Form
    "sheet_id": "1BxiMVs0...",            // Google Sheet ID (from the URL)
    "credentials_file": "credentials/google_credentials.json",
    "form_columns": {                      // Map your form's exact column headers
      "timestamp": "Timestamp",
      "email": "Email Address",
      "full_name": "Full Name",
      "phone": "Phone Number",
      "position": "Position Applying For",
      "experience": "Describe your relevant experience",
      "felony_question": "Have you been convicted of a felony in the past 7 years?",
      "felony_details": "If yes, please provide details"
    }
  },
  "gmail": {
    "recruiting_address": "recruiting@yourdomain.com",  // Sends from this address
    "report_recipient": "owner@yourdomain.com",          // Report delivered here
    "credentials_file": "credentials/gmail_credentials.json"
  },
  "anthropic": {
    "api_key": "sk-ant-...",
    "model": "claude-opus-4-6"             // Change to claude-sonnet-4-6 for lower cost
  },
  "company": {
    "name": "Mad Dog Facility Partners",
    "tagline": "a veteran-owned janitorial and facility services company"
  },
  "timezone": "America/Phoenix",           // Arizona = no DST
  "log_file": "jenny_log.json",
  "reminder_hours": 48
}
```

### Finding your Google Sheet ID

Your Google Sheet URL looks like:
```
https://docs.google.com/spreadsheets/d/1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgVE2upms/edit
```
The Sheet ID is the long string between `/d/` and `/edit`:
`1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgVE2upms`

---

## Google Sheets API setup

See **[docs/google_sheets_setup.md](docs/google_sheets_setup.md)** for full instructions.

Short version:
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a project → Enable the **Google Sheets API**
3. Create credentials – choose **Service Account** (recommended for cron)
4. Download the JSON key and save it to `credentials/google_credentials.json`
5. Share your Google Sheet with the service account's email address (Viewer)

---

## Gmail API setup

See **[docs/gmail_setup.md](docs/gmail_setup.md)** for full instructions.

Short version:
1. In the same Google Cloud project, enable the **Gmail API**
2. Create **OAuth 2.0 Client ID** credentials → Desktop App
3. Download the JSON and save it to `credentials/gmail_credentials.json`
4. Run `python setup_auth.py` (described below)

---

## One-time authorization

Before scheduling Jenny as a cron job you must authorize the Google APIs
interactively once. This creates token files that are refreshed automatically
on every subsequent run.

```bash
cd jenny
source venv/bin/activate
python setup_auth.py
```

The script will:
1. Open a browser window for Gmail authorization
2. Walk you through Google Sheets authorization (or just remind you to share
   the sheet if you're using a service account)

Token files are saved to `credentials/` and are excluded from git.

---

## Running manually

```bash
cd jenny
source venv/bin/activate

# Normal run
python jenny.py

# Dry run – logs every action but sends nothing
python jenny.py --dry-run

# Custom config path
python jenny.py --config /path/to/my_config.json
```

---

## Scheduling with cron

Arizona (Mountain Standard Time) is **UTC-7 year-round** (no Daylight Saving Time).
7 AM Arizona time = **14:00 UTC**.

### Step 1 – Find your Python path

```bash
source venv/bin/activate
which python   # e.g. /home/user/operations/jenny/venv/bin/python
```

### Step 2 – Add the cron job

```bash
crontab -e
```

Add this line (replace paths with your actual paths):

```
0 14 * * * cd /home/user/operations/jenny && /home/user/operations/jenny/venv/bin/python jenny.py >> /home/user/operations/jenny/jenny.log 2>&1
```

This runs Jenny at **7:00 AM Arizona time every day**.

To confirm the job was saved:
```bash
crontab -l
```

### Alternative: using TZ variable (if your cron supports it)

```
0 7 * * * TZ="America/Phoenix" cd /home/user/operations/jenny && /home/user/operations/jenny/venv/bin/python jenny.py >> jenny.log 2>&1
```

---

## Log file reference

`jenny_log.json` stores all state. Structure:

```jsonc
{
  "candidates": {
    "indeed_abc123": {
      "name": "Jane Smith",
      "role": "Janitorial Technician",
      "indeed_id": "indeed_abc123",
      "email": "jane@example.com",
      "initial_message_sent_at": "2024-01-10T07:02:14-07:00",
      "initial_message_status": "sent",
      "reminder_sent_at": null,             // null = no reminder sent yet
      "reminder_status": null,
      "form_submitted_at": "2024-01-11T09:15:00-07:00",
      "form_submission": { /* raw form data */ },
      "interview_invite_sent_at": "2024-01-11T07:01:05-07:00",
      "interview_invite_status": "sent",
      "flagged": false,
      "flag_reason": null,
      "proactive_questions": [],            // questions candidate asked on Indeed
      "first_seen_at": "2024-01-10T07:02:14-07:00"
    }
  },
  "runs": [
    // Last 90 daily run summaries
    { "run_at": "...", "actions_count": 12, "flagged_count": 1 }
  ]
}
```

**Key status transitions:**

```
New applicant seen
  → initial_message_status = "sent"
    → (48h later, no form) reminder_sent_at set
    → form_submitted_at set
      → interview_invite_sent_at set   (clean)
      → flagged = true                  (felony disclosure)
```

---

## Troubleshooting

### Indeed login fails / CAPTCHA

Set `"headless": false` in config.json and run `python jenny.py` manually.
A browser window opens; complete the challenge. Jenny will proceed with the
rest of the run using the authenticated session. You may need to do this
occasionally if Indeed requires re-verification.

### "Could not find job cards" or selector errors

Indeed updates its frontend periodically. When this happens:
1. Set `"headless": false` and run Jenny
2. Open the `screenshots/` directory – Jenny saves a screenshot on every
   selector failure
3. Inspect the screenshot to see what the page looks like
4. Update the relevant selector list in `modules/indeed_automation.py`

### Gmail send fails

Re-run `python setup_auth.py` to refresh the token. If it still fails,
check that the Gmail API is enabled in your Google Cloud project and that
the OAuth consent screen is configured.

### Google Sheet not reading

- **Service account**: Confirm the sheet is shared with the service account email (Viewer)
- **OAuth2**: Run `python setup_auth.py` again to re-authorize
- Confirm `sheet_id` in config.json matches the actual Sheet ID in the URL

### Candidates getting messaged twice

This should not happen — Jenny checks the log before every send. If it
does occur, inspect `jenny_log.json` to see if the `indeed_id` values are
consistent. If Indeed returns different IDs for the same applicant across
runs, open an issue.

### Dry-run mode for testing

```bash
python jenny.py --dry-run
```

All logic runs and all decisions are logged, but no messages are sent,
no emails are delivered, and the log is still updated. Use this to verify
behavior without affecting candidates.
