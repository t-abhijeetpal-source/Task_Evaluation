# D2 Docker-Compose & E2E Validation Record

> Multi-service stack built, run, seeded, E2E-tested, logged, and torn down — every step executed
> with exit code 0. Engine: Docker (Colima) + Compose v5.1.4. Date: 2026-06-17.
> No claim below is made without captured execution evidence.

## 1. Stack Architecture

### API Service
* **Language:** Python 3.12
* **Framework:** FastAPI + Uvicorn (psycopg 3 driver)
* **Dockerfile Path:** `api/Dockerfile`
* **Purpose:** HTTP API — creates jobs (DB write), reads job status. `POST /jobs`, `GET /jobs/{id}`, `GET /jobs`, `GET /health`.

### Database Service
* **Engine:** PostgreSQL
* **Version:** 16-alpine (`postgres:16-alpine`)
* **Purpose:** System of record for `users` (fixtures) and `jobs` (work queue).

### Worker Service
* **Language:** Python 3.12
* **Framework:** psycopg 3 polling worker
* **Purpose:** Claims `pending` jobs (`FOR UPDATE SKIP LOCKED`), processes them (uppercases payload), marks `done` with `result`/`processed_by`/`processed_at`.

---

## 2. Configuration Artifacts

### docker-compose.yml
```yaml
name: d2-stack

services:
  database:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: appuser
      POSTGRES_PASSWORD: apppass
      POSTGRES_DB: appdb
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U appuser -d appdb"]
      interval: 5s
      timeout: 5s
      retries: 10
    networks: [app-network]

  api:
    build: ./api
    environment:
      DATABASE_URL: postgresql://appuser:apppass@database:5432/appdb
    depends_on:
      database:
        condition: service_healthy
    ports: ["8080:8000"]
    networks: [app-network]

  worker:
    build: ./worker
    environment:
      DATABASE_URL: postgresql://appuser:apppass@database:5432/appdb
      WORKER_ID: worker-1
    depends_on:
      database:
        condition: service_healthy
    networks: [app-network]

networks:
  app-network:
    driver: bridge
```

### Network Definition
A single explicitly-declared **user-defined bridge network** `app-network`. All three services join
it and communicate **only** through it — no host networking, no inter-service host ports. **Service
discovery** uses Docker's embedded DNS on the user-defined network: the API and worker reach the DB
by its service name `database` (`postgresql://appuser:apppass@database:5432/appdb`). Only the API
publishes a host port (`8080->8000`) so the E2E test can reach it from the host; the database has no
host port (internal only).

### Health Checks
* **Database:** `pg_isready -U appuser -d appdb` (interval 5s, timeout 5s, retries 10). Compose marks
  the container `healthy` only when Postgres accepts connections.
* **Startup ordering:** both `api` and `worker` declare `depends_on: { database: { condition:
  service_healthy } }`, so they start **only after** the DB is healthy (demonstrated in §4 — the
  compose output shows `database Healthy` before `api/worker Starting`).
* **API:** the image also has a `HEALTHCHECK` hitting `/health` (which does a real `SELECT 1`), so a
  healthy API container also proves API↔DB connectivity.

---

## 3. Build Verification
**Command:** `docker compose build`
**Exit Code:** `0`
**Output (tail):**
```text
Successfully built 15a635679a63
Successfully tagged d2-stack-api:latest
 Image d2-stack-api Built
 Image d2-stack-worker Built
```

## 4. Startup Verification
**Command:** `docker compose up -d`
**Exit Code:** `0`
**Output (health-gated ordering — DB healthy BEFORE api/worker start):**
```text
 Container d2-stack-database-1  Waiting
 Container d2-stack-database-1  Healthy
 Container d2-stack-api-1       Starting
 Container d2-stack-worker-1    Starting
 Container d2-stack-worker-1    Started
 Container d2-stack-api-1       Started
```

## 5. Container Status
**Command:** `docker compose ps`
**Output:**
```text
NAME                  IMAGE                COMMAND                  SERVICE    STATUS                    PORTS
d2-stack-api-1        d2-stack-api         "uvicorn app.main:ap…"   api        Up (health: starting)     0.0.0.0:8080->8000/tcp
d2-stack-database-1   postgres:16-alpine   "docker-entrypoint.s…"   database   Up (healthy)              5432/tcp
d2-stack-worker-1     d2-stack-worker      "python worker.py"       worker     Up
```

## 6. Seed Data Verification
**Command:** `./scripts/seed.sh`
**Exit Code:** `0`
**Output:**
```text
[seed] applying database/seed.sql to the running 'database' service...
CREATE TABLE
CREATE TABLE
INSERT 0 3
INSERT 0 1
[seed] row counts after seeding:
users=3
jobs=1
[seed] OK
```
**Rows Inserted:** 3 users (alice, bob, carol) + 1 pre-seeded job (`seed-job`).

## 7. End-to-End Test Verification
**Command:** `./scripts/integration-test.sh`
**Exit Code:** `0`
**Output:**
```text
[e2e] 1) API health (proves API <-> DB connectivity)
{"status":"ok","db":"up"}
[e2e] 2) create a job via the API (DB write)
  -> {"id":2,"payload":"hello-d2","status":"pending"}
[e2e] 3) poll until the WORKER processes job id=2 (DB update)
  -> final job: {"id":2,"payload":"hello-d2","status":"done","result":"HELLO-D2","processed_by":"worker-1"}
[e2e] expected: status=done result=HELLO-D2
[e2e] actual:   status=done result=HELLO-D2
[e2e] PASS
```
**Expected Result:** job transitions `pending → done` with `result=HELLO-D2`.
**Actual Result:** `status=done result=HELLO-D2 processed_by=worker-1`.
**Pass/Fail:** **PASS** (full flow: client → API → DB write → worker consumption → DB update → verification query).

## 8. Worker Verification
**Relevant Logs:**
```text
{"worker":"worker-1","msg":"worker starting","target":"database:5432/appdb"}
{"worker":"worker-1","msg":"processed job","job_id":1,"result":"SEED-JOB"}
{"worker":"worker-1","msg":"processed job","job_id":2,"result":"HELLO-D2"}
```
**Processed Records:** 2 — the seeded job (id 1, `SEED-JOB`) and the E2E job (id 2, `HELLO-D2`).
**Verification Evidence:** the API's `GET /jobs/2` returned `status=done, result=HELLO-D2, processed_by=worker-1`, confirming the worker's DB update is visible through the API↔DB path.

## 9. Service Logs
**API Logs:**
```text
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     172.18.0.1 - "POST /jobs HTTP/1.1" 201 Created
INFO:     172.18.0.1 - "GET /jobs/2 HTTP/1.1" 200 OK
```
**Database Logs:**
```text
2026-06-17 06:13:43 UTC [1] LOG:  database system is ready to accept connections
```
**Worker Logs:** see §8 (structured JSON, one line per processed job).

## 10. Teardown Verification
**Command:** `docker compose down -v` (via `./scripts/teardown.sh`)
**Exit Code:** `0`
**Output:**
```text
 Container d2-stack-api-1       Removed
 Container d2-stack-worker-1    Removed
 Container d2-stack-database-1  Removed
 Network d2-stack_app-network   Removed
[teardown] stack removed
# post-teardown `docker compose ps` -> (empty: no containers remain)
```

## 11. Known Limitations
* **Polling worker** (1 s interval), not event-driven — fine for the demo; a real system would use
  `LISTEN/NOTIFY` or a broker (Redis/RabbitMQ).
* **Credentials in compose env** (plain `appuser/apppass`) — use Docker secrets / a vault for prod.
* **No DB volume persistence declared** — data is ephemeral (intentional for deterministic, clean
  runs); add a named volume for durable data.
* **Single worker replica** — the `FOR UPDATE SKIP LOCKED` query already makes it safe to scale
  (`docker compose up --scale worker=N`) without double-processing, but this run used one.
* **No TLS / auth on the API** — internal demo.

## 12. Agent Generated vs Verified

### Agent Generated
* Architecture (FastAPI + PostgreSQL + Python worker), `docker-compose.yml`, Dockerfiles, API/worker
  source, `database/seed.sql`, the three scripts, README, and this document.

### Verified (executed, evidence above)
* **Build Output:** `docker compose build` → exit 0, images built.
* **Container Status:** `docker compose ps` → DB healthy, all up.
* **Seed Results:** `seed.sh` exit 0 → users=3, jobs=1.
* **E2E Test Results:** `integration-test.sh` exit 0 → PASS (`HELLO-D2`).
* **Logs:** worker processed jobs 1 & 2; API 201/200; DB ready.
* **Teardown Output:** `docker compose down -v` exit 0 → all containers + network removed.

---

## Deliverables Checklist
- [x] docker-compose.yml
- [x] API Dockerfile
- [x] Worker Dockerfile
- [x] Seed Script (`scripts/seed.sh`)
- [x] Integration Test Script (`scripts/integration-test.sh`)
- [x] Health Checks (DB `pg_isready`; API `/health`)
- [x] User-defined Network (`app-network`, bridge)
- [x] Build Verification (exit 0)
- [x] Startup Verification (exit 0, health-gated)
- [x] Seed Verification (exit 0, rows inserted)
- [x] E2E Verification (exit 0, PASS)
- [x] Logs (API/DB/worker captured)
- [x] README
- [x] D2_compose_e2e_record.md

**All success criteria met; every mandatory command returned exit code 0.**


## Screenshots

**api jobs json**

![api jobs json](../../screenshots/api-jobs-json.png)

**api swagger docs**

![api swagger docs](../../screenshots/api-swagger-docs.png)

