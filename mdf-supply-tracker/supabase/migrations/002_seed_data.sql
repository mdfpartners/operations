-- MDF Supply Tracker — Seed Data
-- Migration 002

-- ============================================================
-- Accounts
-- ============================================================
INSERT INTO accounts (id, name, location, active) VALUES
  ('a1000000-0000-0000-0000-000000000001', 'Woodford County', 'Eureka, IL', TRUE),
  ('a1000000-0000-0000-0000-000000000002', 'Winpak', 'Peoria, IL', TRUE),
  ('a1000000-0000-0000-0000-000000000003', 'Midwest MultiCare', 'Peoria, IL', TRUE)
ON CONFLICT DO NOTHING;

-- ============================================================
-- Vendors
-- ============================================================
INSERT INTO vendors (id, name, website, active) VALUES
  ('b1000000-0000-0000-0000-000000000001', 'Amazon Business', 'https://business.amazon.com', TRUE),
  ('b1000000-0000-0000-0000-000000000002', 'Home Depot', 'https://www.homedepot.com', TRUE),
  ('b1000000-0000-0000-0000-000000000003', 'Grainger', 'https://www.grainger.com', TRUE),
  ('b1000000-0000-0000-0000-000000000004', 'Uline', 'https://www.uline.com', TRUE),
  ('b1000000-0000-0000-0000-000000000005', 'Local JanSan Supplier', NULL, TRUE)
ON CONFLICT DO NOTHING;

-- ============================================================
-- Supply Catalog (12 items)
-- ============================================================
INSERT INTO supply_catalog (id, item_name, category, unit_of_measure, preferred_vendor_id, active) VALUES
  ('c1000000-0000-0000-0000-000000000001', 'Paper Towels',        'Paper Products',  'Case',   'b1000000-0000-0000-0000-000000000001', TRUE),
  ('c1000000-0000-0000-0000-000000000002', 'Toilet Paper',        'Paper Products',  'Case',   'b1000000-0000-0000-0000-000000000001', TRUE),
  ('c1000000-0000-0000-0000-000000000003', 'Trash Liners',        'Waste Management','Case',   'b1000000-0000-0000-0000-000000000004', TRUE),
  ('c1000000-0000-0000-0000-000000000004', 'Nitrile Gloves',      'PPE',             'Box',    'b1000000-0000-0000-0000-000000000003', TRUE),
  ('c1000000-0000-0000-0000-000000000005', 'Disinfectant',        'Chemicals',       'Gallon', 'b1000000-0000-0000-0000-000000000005', TRUE),
  ('c1000000-0000-0000-0000-000000000006', 'Glass Cleaner',       'Chemicals',       'Gallon', 'b1000000-0000-0000-0000-000000000005', TRUE),
  ('c1000000-0000-0000-0000-000000000007', 'Neutral Floor Cleaner','Chemicals',      'Gallon', 'b1000000-0000-0000-0000-000000000005', TRUE),
  ('c1000000-0000-0000-0000-000000000008', 'Mop Heads',           'Equipment',       'Each',   'b1000000-0000-0000-0000-000000000003', TRUE),
  ('c1000000-0000-0000-0000-000000000009', 'Microfiber Towels',   'Equipment',       'Dozen',  'b1000000-0000-0000-0000-000000000001', TRUE),
  ('c1000000-0000-0000-0000-000000000010', 'Hand Soap',           'Paper Products',  'Gallon', 'b1000000-0000-0000-0000-000000000001', TRUE),
  ('c1000000-0000-0000-0000-000000000011', 'Urinal Screens',      'Restroom',        'Box',    'b1000000-0000-0000-0000-000000000005', TRUE),
  ('c1000000-0000-0000-0000-000000000012', 'Toilet Bowl Cleaner', 'Restroom',        'Case',   'b1000000-0000-0000-0000-000000000005', TRUE)
ON CONFLICT DO NOTHING;

-- ============================================================
-- Requesters / Site Leads
-- ============================================================
INSERT INTO app_users (id, name, email, role, request_token, active) VALUES
  (
    'd1000000-0000-0000-0000-000000000001',
    'Site Lead A',
    'sitelead.a@example.com',
    'requester',
    'token-site-lead-a-0000000000000001',
    TRUE
  ),
  (
    'd1000000-0000-0000-0000-000000000002',
    'Site Lead B',
    'sitelead.b@example.com',
    'requester',
    'token-site-lead-b-0000000000000002',
    TRUE
  ),
  (
    'd1000000-0000-0000-0000-000000000003',
    'Site Lead C',
    'sitelead.c@example.com',
    'requester',
    'token-site-lead-c-0000000000000003',
    TRUE
  )
ON CONFLICT DO NOTHING;

-- ============================================================
-- Requester-Account Permissions
-- Site Lead A → Woodford County, Winpak
-- Site Lead B → Midwest MultiCare
-- Site Lead C → all three
-- ============================================================
INSERT INTO requester_account_permissions (requester_id, account_id) VALUES
  ('d1000000-0000-0000-0000-000000000001', 'a1000000-0000-0000-0000-000000000001'),
  ('d1000000-0000-0000-0000-000000000001', 'a1000000-0000-0000-0000-000000000002'),
  ('d1000000-0000-0000-0000-000000000002', 'a1000000-0000-0000-0000-000000000003'),
  ('d1000000-0000-0000-0000-000000000003', 'a1000000-0000-0000-0000-000000000001'),
  ('d1000000-0000-0000-0000-000000000003', 'a1000000-0000-0000-0000-000000000002'),
  ('d1000000-0000-0000-0000-000000000003', 'a1000000-0000-0000-0000-000000000003')
ON CONFLICT DO NOTHING;
