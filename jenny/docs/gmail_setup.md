# Gmail API Setup

Jenny sends two kinds of emails via the Gmail API:
- First-round interview invitations (from your recruiting address)
- Daily pipeline reports (to you)

Gmail API access uses **OAuth2**. You authorize it once via browser, and
the token is refreshed automatically on every cron run.

> Note: Gmail API with service accounts requires Google Workspace (paid).
> For a standard Gmail/Google account, OAuth2 is the correct approach.

---

## Steps

### 1. Use the same Google Cloud project as Google Sheets

If you followed the Google Sheets setup guide, you already have a project.
Use it here. If not, create one at [console.cloud.google.com](https://console.cloud.google.com/).

### 2. Enable the Gmail API

1. In the left menu: **APIs & Services** → **Library**
2. Search for **Gmail API**
3. Click it → **Enable**

### 3. Configure the OAuth consent screen (if not done already)

1. **APIs & Services** → **OAuth consent screen**
2. User type: **External** → **Create**
3. Fill in:
   - **App name**: `Jenny Recruiting`
   - **User support email**: your email
   - **Developer contact email**: your email
4. Click **Save and Continue**
5. On the Scopes page, click **Add or Remove Scopes**
6. Search for `gmail.send` → check `https://www.googleapis.com/auth/gmail.send`
7. Click **Update** → **Save and Continue**
8. On the Test users page, click **+ Add Users** → add your recruiting Gmail address
9. Click **Save and Continue** → **Back to Dashboard**

### 4. Create OAuth2 Client ID credentials

1. **APIs & Services** → **Credentials** → **+ Create Credentials** → **OAuth client ID**
2. Application type: **Desktop app**
3. Name: `Jenny Gmail`
4. Click **Create**
5. Click **Download JSON** on the confirmation dialog
6. Save the downloaded file as:
   ```
   jenny/credentials/gmail_credentials.json
   ```

### 5. Update config.json

```json
"gmail": {
  "recruiting_address": "recruiting@yourdomain.com",
  "report_recipient":   "owner@yourdomain.com",
  "credentials_file":   "credentials/gmail_credentials.json",
  "token_file":         "credentials/token_gmail.pickle"
}
```

- `recruiting_address` – the Gmail account Jenny sends **from**
  (must match the account you authorize in the next step)
- `report_recipient` – where the daily report is delivered

### 6. Authorize (one time)

```bash
cd jenny
source venv/bin/activate
python setup_auth.py
```

When prompted for Gmail authorization:
1. A browser window opens
2. **Sign in with the recruiting Gmail account** (not your personal account)
3. You may see a warning that the app is unverified – click **Advanced** →
   **Go to Jenny Recruiting (unsafe)** (this is normal for internal tools
   with a test-mode consent screen)
4. Click **Allow**

The token is saved to `credentials/token_gmail.pickle`. Cron runs will
refresh it automatically; you won't need to repeat this step unless you
revoke access from your Google account settings.

---

## Moving to production (optional)

The OAuth consent screen in "Testing" mode works fine for a personal cron
job. If you ever need to authorize additional Gmail accounts, either:
- Add them as test users on the OAuth consent screen, **or**
- Submit the app for verification (not required for internal tools)

---

## Troubleshooting

**"Access blocked: Jenny Recruiting has not completed the Google verification process"**

This appears when your consent screen is in Testing mode and the account you're
trying to authorize wasn't added as a test user. Go to
**APIs & Services → OAuth consent screen → Test users** and add the recruiting
Gmail address.

**"Token has been expired or revoked"**

Re-run `python setup_auth.py`. This generates a fresh token.

**Emails land in spam**

This is a deliverability issue unrelated to Jenny. Consider:
- Setting up SPF/DKIM/DMARC for your domain
- Using a dedicated sending domain rather than a personal Gmail
- Warming up the sending address gradually
