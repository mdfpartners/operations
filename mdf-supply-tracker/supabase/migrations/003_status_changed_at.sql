-- Migration 003: Add status_changed_at to supply_requests
-- Tracks when the status field last changed (not all updates)

ALTER TABLE supply_requests
  ADD COLUMN IF NOT EXISTS status_changed_at TIMESTAMPTZ NOT NULL DEFAULT now();

-- Backfill: for existing rows, use submitted_at as the baseline
UPDATE supply_requests SET status_changed_at = submitted_at WHERE status_changed_at IS NOT NULL;

-- Trigger function: only update status_changed_at when status actually changes
CREATE OR REPLACE FUNCTION set_status_changed_at()
RETURNS TRIGGER AS $$
BEGIN
  IF NEW.status IS DISTINCT FROM OLD.status THEN
    NEW.status_changed_at := now();
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_supply_requests_status_changed_at
  BEFORE UPDATE ON supply_requests
  FOR EACH ROW EXECUTE FUNCTION set_status_changed_at();
