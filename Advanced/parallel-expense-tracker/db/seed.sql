-- Agent Generated
-- Sample expenses for manual/dev seeding.
-- Apply after schema.sql: sqlite3 data/expenses.db < db/seed.sql

INSERT INTO expenses (amount, category, note, created_at) VALUES
    (12.50,  'food',      'Lunch at the deli',        '2026-06-10T12:30:00Z'),
    (45.00,  'transport', 'Monthly metro top-up',     '2026-06-11T08:15:00Z'),
    (89.99,  'utilities', 'Electricity bill',         '2026-06-12T18:00:00Z'),
    (6.75,   'food',      'Morning coffee',           '2026-06-13T09:05:00Z'),
    (120.00, 'utilities', 'Internet + landline',      '2026-06-14T14:45:00Z'),
    (30.20,  'transport', 'Ride share to airport',    '2026-06-15T05:50:00Z');
