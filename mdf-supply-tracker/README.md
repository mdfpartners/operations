# MDF Supply Tracker

Internal supply request and procurement tracking web app for MDF Partners.

## Tech Stack

- **Next.js 16** (App Router, TypeScript)
- **Supabase** — database and server-side data access
- **Resend** — transactional emails
- **Tailwind CSS** — styling
- **PapaParse** — CSV import/export
- **jose** — JWT-based admin session cookie

---

## Setup

### 1. Clone and install

```bash
cd mdf-supply-tracker
npm install
```

### 2. Configure environment variables

Copy `.env.example` to `.env.local` and fill in all values:

```bash
cp .env.example .env.local
```

| Variable | Description |
|---|---|
| `NEXT_PUBLIC_SUPABASE_URL` | Supabase project URL |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | Supabase anon key |
| `SUPABASE_SERVICE_ROLE_KEY` | Supabase service role key (server-side only) |
| `RESEND_API_KEY` | Resend API key for email |
| `INTERNAL_NOTIFICATION_EMAILS` | Comma-separated analyst/admin emails for new request alerts |
| `EXECUTIVE_NOTIFICATION_EMAILS` | Comma-separated emails for daily aging email |
| `APP_BASE_URL` | Full base URL, e.g. `https://yourapp.vercel.app` |
| `APP_TIMEZONE` | Operational timezone, default `America/Chicago` |
| `ADMIN_PASSWORD` | Shared admin password for the V1 password gate |
| `CRON_SECRET` | Secret token protecting the executive email cron route |
| `SEND_REAL_EMAILS_IN_DEV` | Set `true` to send real emails outside production |

### 3. Run database migrations

Apply the SQL files in `supabase/migrations/` to your Supabase project in order:

1. `001_initial_schema.sql` — tables, triggers, constraints, order number sequence
2. `002_seed_data.sql` — seed accounts, vendors, catalog items, requesters

You can run these in the Supabase SQL editor or using the Supabase CLI:

```bash
supabase db push
```

### 4. Run locally

```bash
npm run dev
```

The app will be at http://localhost:3000.

---

## Routes

| Route | Description |
|---|---|
| `/admin/login` | Admin login page |
| `/admin/orders` | Analyst order dashboard |
| `/admin/orders/[id]` | Order detail and procurement workflow |
| `/admin/catalog` | Supply catalog management |
| `/admin/vendors` | Vendor management |
| `/admin/accounts` | Account management |
| `/admin/requesters` | Requester/site lead management |
| `/admin/import` | Bulk import/export (CSV) |
| `/admin/reports` | Reporting dashboard |
| `/request/[token]` | Site lead request form (public, token-gated) |
| `/status/[token]` | Public order status page |
| `/api/cron/executive-email` | Executive daily email trigger (requires CRON_SECRET) |

---

## Daily Executive Email (Vercel Cron)

Add to `vercel.json`:

```json
{
  "crons": [
    {
      "path": "/api/cron/executive-email?secret=YOUR_CRON_SECRET",
      "schedule": "0 8 * * *"
    }
  ]
}
```

---

## Deployment (Vercel)

1. Push to GitHub.
2. Import into Vercel.
3. Set all environment variables from `.env.example`.
4. Deploy.

---

## Manual Test Checklist

- [ ] Valid requester token shows correct requester name and assigned accounts only
- [ ] Invalid/inactive token shows friendly error message
- [ ] Submit request with catalog items
- [ ] Submit request with "Other" item (requires description)
- [ ] Validation prevents submission without urgency or items
- [ ] Order number generated in MDF-XXXX format
- [ ] Confirmation email logged in notification_log
- [ ] Internal new request notification sent/logged
- [ ] Analyst dashboard shows open orders with aging buckets
- [ ] Filters (account, status, urgency, aging) work
- [ ] Order detail shows line items, audit log, recent similar requests (last 14 days)
- [ ] Add/edit purchase details per line item
- [ ] Status change creates audit log entry
- [ ] Status change to purchased/delayed/delivered/complete_received/cancelled triggers requester email
- [ ] completed_at set on complete_received; cancelled_at set on cancelled
- [ ] Catalog/vendor/account/requester management: add, edit, activate/deactivate
- [ ] Requester request link copies; form shows only assigned accounts
- [ ] CSV import: preview required before import
- [ ] Intra-file duplicates flagged as rejected in preview
- [ ] Import upserts existing records; does not create duplicates
- [ ] Import audit_log entry created with correct counts
- [ ] CSV export for all entity types
- [ ] Reports: open orders by status/aging, spend by account/vendor/category
- [ ] Order history CSV export from reports page
- [ ] Executive email route returns 401 without CRON_SECRET
- [ ] Public status page shows order info, no vendor/cost/admin data
- [ ] Admin login sets HTTP-only cookie
- [ ] Unauthenticated access to /admin/* redirects to login
- [ ] Logout clears session cookie

---

## Production Hardening Notes

The following are **intentionally deferred from V1** and required before broader rollout:

**Admin Authentication:** V1 uses a shared `ADMIN_PASSWORD`. Replace with Supabase Auth + RBAC before wider deployment so admins have individual credentials and audit attribution.

**Row Level Security (RLS):** V1 uses server-side service role access for all DB operations. Enable RLS policies on all tables before exposing any client-side Supabase access.

**Rate Limiting:** The `/request/[token]` route is public. Add rate limiting to prevent brute-force token enumeration.

**Token Rotation:** Add an admin action to rotate a requester's `request_token` if a link is compromised.

**Error Monitoring:** Add Sentry or similar for production exception tracking.

**Email Domain Verification:** Verify your sending domain in Resend. Update the `from` address in `src/lib/email.ts`.

**HTTPS / Secure Cookies:** Ensure `APP_BASE_URL` is HTTPS in production. The session cookie is `secure: true` in production automatically.

**Database Backups:** Enable Supabase scheduled backups and verify restore procedures.
