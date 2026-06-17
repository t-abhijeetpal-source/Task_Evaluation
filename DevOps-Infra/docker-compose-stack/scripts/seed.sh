#!/usr/bin/env bash
# Apply deterministic schema + fixtures to the live database service, then show counts.
set -euo pipefail
cd "$(dirname "$0")/.."

echo "[seed] applying database/seed.sql to the running 'database' service..."
docker compose exec -T database psql -U appuser -d appdb -v ON_ERROR_STOP=1 < database/seed.sql

echo "[seed] row counts after seeding:"
docker compose exec -T database psql -U appuser -d appdb -tAc "SELECT 'users=' || count(*) FROM users;"
docker compose exec -T database psql -U appuser -d appdb -tAc "SELECT 'jobs='  || count(*) FROM jobs;"
echo "[seed] OK"
