# Google Sheets API Setup

Jenny reads Google Form responses via the Google Sheets API.
This guide walks through creating credentials from scratch.

---

## Which credential type should I use?

| Type | Best for | Interactive auth required? |
|------|----------|--------------------------|
| **Service Account** (recommended) | Cron jobs, servers | No – just share the sheet |
| **OAuth2 Desktop App** | Local testing | Yes – browser auth once |

Use a **Service Account** for production. It never expires and requires
no interactive re-authorization.

---

## Option A – Service Account (Recommended)

### 1. Create or open a Google Cloud project

1. Go to [console.cloud.google.com](https://console.cloud.google.com/)
2. Click the project drop-down at the top → **New Project**
3. Name it (e.g. `jenny-recruiting`) and click **Create**

### 2. Enable the Google Sheets API

1. In the left menu: **APIs & Services** → **Library**
2. Search for **Google Sheets API**
3. Click it → **Enable**

### 3. Create a Service Account

1. In the left menu: **APIs & Services** → **Credentials**
2. Click **+ Create Credentials** → **Service Account**
3. Give it a name (e.g. `jenny-sheets-reader`) → **Create and Continue**
4. Role: **Viewer** → **Continue** → **Done**

### 4. Download the JSON key

1. Back on the Credentials page, click your new service account
2. Tab: **Keys** → **Add Key** → **Create new key** → **JSON**
3. A file downloads. Save it as:
   ```
   jenny/credentials/google_credentials.json
   ```

### 5. Share the Google Sheet with the service account

1. Open the `google_credentials.json` file and copy the `client_email` value.
   It looks like: `jenny-sheets-reader@jenny-recruiting.iam.gserviceaccount.com`
2. Open your Google Sheet
3. Click **Share** (top right)
4. Paste the service account email
5. Set permission to **Viewer**
6. Un-check "Notify people" → **Share**

### 6. Update config.json

```json
"google": {
  "credentials_file": "credentials/google_credentials.json",
  ...
}
```

No token file is needed for service accounts. You're done!

---

## Option B – OAuth2 Desktop App

Use this if you prefer not to set up a service account.

### 1–2. Same as Option A (create project, enable Sheets API)

### 3. Create OAuth2 credentials

1. **APIs & Services** → **Credentials** → **+ Create Credentials** → **OAuth client ID**
2. If prompted, configure the OAuth consent screen first:
   - User type: **External** → **Create**
   - Fill in app name (e.g. `Jenny Recruiting`) and your email
   - Add scope: `https://www.googleapis.com/auth/spreadsheets.readonly`
   - Add your email as a test user → **Save**
3. Back in Create OAuth client ID:
   - Application type: **Desktop app**
   - Name: `Jenny Sheets`
   - Click **Create**
4. Download the JSON → save as `jenny/credentials/google_credentials.json`

### 4. Authorize (one time)

```bash
cd jenny
source venv/bin/activate
python setup_auth.py
```

A browser window opens. Sign in and grant access. The token is saved to
`credentials/token_sheets.pickle` and auto-refreshes on future runs.

---

## Finding your Google Sheet ID

Your Google Form automatically creates a linked Google Sheet. Open it and
look at the URL:

```
https://docs.google.com/spreadsheets/d/SHEET_ID_HERE/edit
```

Copy the `SHEET_ID_HERE` portion into `config.json → google.sheet_id`.

---

## Mapping form columns

Jenny tries to auto-detect your form's column headers using keyword matching,
but you can specify exact names in `config.json → google.form_columns` to
avoid any ambiguity:

```json
"form_columns": {
  "timestamp":       "Timestamp",
  "email":           "Email Address",
  "full_name":       "Full Name",
  "phone":           "Phone Number",
  "position":        "Position Applying For",
  "experience":      "Describe your relevant experience",
  "felony_question": "Have you been convicted of a felony in the past 7 years?",
  "felony_details":  "If yes, please provide details"
}
```

The values must match your Google Form's question text **exactly** as it
appears in the sheet header row.
