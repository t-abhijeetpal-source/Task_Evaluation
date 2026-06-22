# D2 Compose Stack — Operational Runbook

Operating guide for the API + PostgreSQL + worker stack: how to start it, drive
the end-to-end flow, debug failures, run migrations, and tear it down.

## Components

| Service | Port | Role |
|---|---|---|
| `api` | 8080→8000 | FastAPI Jobs API (`/health`, `/metrics`, `/jobs`) |
| `database` | internal 5432 | PostgreSQL 16 — system of record (`users`, `jobs`) |
| `worker` | — | Polls `pending` jobs (`FOR UPDATE SKIP LOCKED`), processes, marks `done` |

Service discovery is via Docker DNS on the `app-network` bridge; only the API
publishes a host port. Credentials come from `.env` (never committed).

## 1. Startup

```bash
cp .env.example .env            # demo defaults (apppass, auth disabled)
docker compose up -d --build --wait     # api/worker gate on DB healthy

# Production profile: required secrets, API on loopback, durable DB volume
export POSTGRES_PASSWORD='<strong>' API_KEY='<key>'
docker compose -f docker-compose.yml -f compose.prod.yml up -d --build --wait
```

`--wait` blocks until every healthcheck passes. `docker compose ps` should show
`database` and `api` as `Up (healthy)`.

## 2. End-to-end flow

```bash
./scripts/integration-test.sh   # POST /jobs → worker → GET /jobs/:id status=done
./scripts/verify-stack.sh       # one-shot: clean down → build → up → E2E → log proof
```

`integration-test.sh` auto-sends `X-API-Key` when `API_KEY` is set in `.env`.

## 3. Reading the signals

```bash
curl -s localhost:8080/health                      # {"status":"ok","db":"up"}
curl -s localhost:8080/metrics | grep http_requests # Prometheus metrics
docker compose logs -f worker                       # structured JSON, one line per job
```

Each API request emits one JSON log line (`request_completed` / `request_failed`)
with `request_id` (also returned as `X-Request-ID`), `method`, route-template
`path`, `status_code`, `duration_ms`. Unmatched URLs collapse to `/_unmatched`
to protect metric cardinality.

## 4. Common failures

| Symptom | Cause | Fix |
|---|---|---|
| `up --wait` hangs / api unhealthy | DB not ready, or wrong creds in `.env` | `docker compose logs database`; confirm `POSTGRES_PASSWORD` set |
| API `503 {"db":"down"}` | DB not reachable from api | wait for `database` healthy; check `DATABASE_URL` |
| E2E `FAIL` / job stuck `pending` | stale DB volume from a pre-seed-mount run | `docker compose down -v` then `up` to re-init schema |
| worker logs `relation "jobs" does not exist` | stale volume predating the init mount | `docker compose down -v` to recreate a fresh, auto-seeded DB |
| `401 invalid or missing API key` | `API_KEY` set but header missing | send `-H "X-API-Key: <key>"` (the E2E script does this automatically) |
| port 8080 in use | another process on 8080 | free it or change the `api` host port mapping |
| prod overlay errors `API_KEY is missing` | required secret unset | `export API_KEY=...` (prod fails fast by design) |

## 5. Worker debugging

```bash
docker compose logs --tail=50 worker          # recent processing activity
docker compose exec database psql -U appuser -d appdb \
  -c "SELECT id,status,result,processed_by FROM jobs ORDER BY id DESC LIMIT 10;"
docker compose up -d --scale worker=3         # safe: FOR UPDATE SKIP LOCKED dedupes
```

The worker installs a SIGTERM handler: `docker compose stop` / `down` lets it
finish the in-flight batch (up to `stop_grace_period: 10s`) and exit cleanly.

## 6. Database migrations (Alembic)

Fresh installs auto-apply `database/seed.sql` via the Postgres init mount. For
an **existing** database, evolve the schema with Alembic (a dev/ops tool kept
out of the lean runtime image):

```bash
cd api
python -m venv .venv && . .venv/bin/activate && pip install -r requirements-dev.txt

alembic upgrade head --sql        # preview the DDL without touching a DB (used in CI)
DATABASE_URL=postgresql://appuser:apppass@localhost:5432/appdb alembic upgrade head
```

Revision `0001` creates `users` + `jobs` (schema equivalent to `seed.sql`; the
demo fixtures remain in `seed.sql`). New schema changes go in new revisions
under `api/alembic/versions/`.

## 7. Teardown

```bash
docker compose down            # stop, keep volumes
docker compose down -v         # stop + delete volumes (next up re-seeds from zero)
```

## 8. Scripted verification

```bash
make check        # offline: ruff + mypy --strict + pytest (api & worker, ≥90% cov)
make verify       # full docker E2E: build → up --wait → integration test → log proof
```
