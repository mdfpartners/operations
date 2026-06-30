-- MDF Supply Tracker — Initial Schema
-- Migration 001

-- ============================================================
-- Shared updated_at trigger
-- ============================================================
CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- ============================================================
-- Collision-safe order number sequence
-- ============================================================
CREATE SEQUENCE IF NOT EXISTS order_number_seq START 1001;

CREATE OR REPLACE FUNCTION generate_order_number()
RETURNS TEXT AS $$
BEGIN
  RETURN 'MDF-' || nextval('order_number_seq')::TEXT;
END;
$$ LANGUAGE plpgsql;

-- ============================================================
-- 1. app_users
-- ============================================================
CREATE TABLE IF NOT EXISTS app_users (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name          TEXT NOT NULL,
  email         TEXT,
  phone         TEXT,
  role          TEXT NOT NULL,
  request_token TEXT UNIQUE,
  active        BOOLEAN NOT NULL DEFAULT TRUE,
  created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT app_users_role_check CHECK (role IN ('requester', 'analyst', 'executive', 'admin'))
);

CREATE UNIQUE INDEX IF NOT EXISTS app_users_email_unique
  ON app_users (email) WHERE email IS NOT NULL;

CREATE TRIGGER trg_app_users_updated_at
  BEFORE UPDATE ON app_users
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- ============================================================
-- 2. accounts
-- ============================================================
CREATE TABLE IF NOT EXISTS accounts (
  id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name       TEXT NOT NULL,
  location   TEXT,
  active     BOOLEAN NOT NULL DEFAULT TRUE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE UNIQUE INDEX IF NOT EXISTS accounts_name_active_unique
  ON accounts (name) WHERE active = TRUE;

CREATE TRIGGER trg_accounts_updated_at
  BEFORE UPDATE ON accounts
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- ============================================================
-- 3. requester_account_permissions
-- ============================================================
CREATE TABLE IF NOT EXISTS requester_account_permissions (
  id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  requester_id UUID NOT NULL REFERENCES app_users(id),
  account_id   UUID NOT NULL REFERENCES accounts(id),
  created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (requester_id, account_id)
);

-- ============================================================
-- 4. vendors
-- ============================================================
CREATE TABLE IF NOT EXISTS vendors (
  id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name       TEXT NOT NULL,
  website    TEXT,
  active     BOOLEAN NOT NULL DEFAULT TRUE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE UNIQUE INDEX IF NOT EXISTS vendors_name_active_unique
  ON vendors (name) WHERE active = TRUE;

CREATE TRIGGER trg_vendors_updated_at
  BEFORE UPDATE ON vendors
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- ============================================================
-- 5. supply_catalog
-- ============================================================
CREATE TABLE IF NOT EXISTS supply_catalog (
  id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  item_name           TEXT NOT NULL,
  category            TEXT,
  unit_of_measure     TEXT,
  preferred_vendor_id UUID REFERENCES vendors(id),
  default_notes       TEXT,
  active              BOOLEAN NOT NULL DEFAULT TRUE,
  created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TRIGGER trg_supply_catalog_updated_at
  BEFORE UPDATE ON supply_catalog
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- ============================================================
-- 6. supply_requests
-- ============================================================
CREATE TABLE IF NOT EXISTS supply_requests (
  id                 UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  order_number       TEXT UNIQUE NOT NULL DEFAULT generate_order_number(),
  requester_id       UUID NOT NULL REFERENCES app_users(id),
  account_id         UUID NOT NULL REFERENCES accounts(id),
  status             TEXT NOT NULL DEFAULT 'submitted',
  urgency            TEXT NOT NULL,
  requester_notes    TEXT,
  internal_notes     TEXT,
  public_status_token TEXT UNIQUE NOT NULL DEFAULT gen_random_uuid()::TEXT,
  submitted_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
  completed_at       TIMESTAMPTZ,
  cancelled_at       TIMESTAMPTZ,
  created_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT supply_requests_status_check
    CHECK (status IN ('submitted', 'purchased', 'delivered', 'complete_received', 'cancelled', 'delayed')),
  CONSTRAINT supply_requests_urgency_check
    CHECK (urgency IN ('normal_replenishment', 'running_low', 'out_of_stock', 'emergency_service_impacting'))
);

CREATE TRIGGER trg_supply_requests_updated_at
  BEFORE UPDATE ON supply_requests
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- ============================================================
-- 7. request_line_items
-- ============================================================
CREATE TABLE IF NOT EXISTS request_line_items (
  id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  request_id            UUID NOT NULL REFERENCES supply_requests(id),
  catalog_item_id       UUID REFERENCES supply_catalog(id),
  other_item_description TEXT,
  quantity_requested    NUMERIC NOT NULL CHECK (quantity_requested > 0),
  quantity_purchased    NUMERIC,
  line_status           TEXT NOT NULL DEFAULT 'submitted',
  created_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT request_line_items_line_status_check
    CHECK (line_status IN ('submitted', 'purchased', 'delivered', 'complete_received', 'cancelled'))
);

CREATE TRIGGER trg_request_line_items_updated_at
  BEFORE UPDATE ON request_line_items
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- ============================================================
-- 8. purchase_details
-- ============================================================
CREATE TABLE IF NOT EXISTS purchase_details (
  id                         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  line_item_id               UUID NOT NULL REFERENCES request_line_items(id),
  vendor_id                  UUID REFERENCES vendors(id),
  product_url                TEXT,
  product_name               TEXT,
  quantity_purchased         NUMERIC,
  unit_cost                  NUMERIC,
  tax                        NUMERIC,
  shipping                   NUMERIC,
  total_cost                 NUMERIC CHECK (total_cost >= 0),
  order_confirmation_number  TEXT,
  estimated_delivery_date    DATE,
  created_at                 TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at                 TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TRIGGER trg_purchase_details_updated_at
  BEFORE UPDATE ON purchase_details
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- ============================================================
-- 9. audit_log
-- ============================================================
CREATE TABLE IF NOT EXISTS audit_log (
  id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  request_id     UUID REFERENCES supply_requests(id),
  actor_user_id  UUID REFERENCES app_users(id),
  actor_name     TEXT NOT NULL,
  action         TEXT NOT NULL,
  old_value      JSONB,
  new_value      JSONB,
  notes          TEXT,
  created_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ============================================================
-- 10. notification_log
-- ============================================================
CREATE TABLE IF NOT EXISTS notification_log (
  id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  request_id        UUID REFERENCES supply_requests(id),
  recipient_email   TEXT NOT NULL,
  notification_type TEXT NOT NULL,
  status            TEXT NOT NULL,
  sent_at           TIMESTAMPTZ,
  error_message     TEXT,
  created_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);
