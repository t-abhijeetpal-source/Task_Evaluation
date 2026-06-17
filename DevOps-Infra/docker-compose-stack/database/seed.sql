-- D2 deterministic schema + fixtures (idempotent — safe to re-run).

CREATE TABLE IF NOT EXISTS users (
  id    SERIAL PRIMARY KEY,
  name  TEXT UNIQUE NOT NULL,
  email TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS jobs (
  id           SERIAL PRIMARY KEY,
  payload      TEXT NOT NULL,
  status       TEXT NOT NULL DEFAULT 'pending',
  result       TEXT,
  processed_by TEXT,
  created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
  processed_at TIMESTAMPTZ
);

-- Deterministic user fixtures.
INSERT INTO users (name, email) VALUES
  ('alice', 'alice@example.com'),
  ('bob',   'bob@example.com'),
  ('carol', 'carol@example.com')
ON CONFLICT (name) DO NOTHING;

-- One pre-seeded pending job (the worker will pick it up). Idempotent guard.
INSERT INTO jobs (payload, status)
SELECT 'seed-job', 'pending'
WHERE NOT EXISTS (SELECT 1 FROM jobs WHERE payload = 'seed-job');
