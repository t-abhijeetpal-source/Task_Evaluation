# D2 — Validation Run & Hardening Record

Validated on 2026-06-17. Stack: `api` (FastAPI) + `database` (postgres:16-alpine) + `worker` (Python).

## Gap found (and fixed)

**Symptom:** On a clean `docker compose up` from zero, the worker crash-looped:
```
{"worker":"worker-1","msg":"worker error (will retry)","error":"relation \"jobs\" does not exist ..."}
```
The schema only existed after a **manual** `./scripts/seed.sh`. This breaks the
document's D2 requirement of a *"clean re-up from zero"* — a fresh stand-up had no
`jobs` table until a human ran the seed script.

**Fix (`docker-compose.yml`):** mount the idempotent `database/seed.sql` into Postgres's
init directory so the schema + fixtures auto-apply on a fresh data dir:
```yaml
database:
  volumes:
    - ./database/seed.sql:/docker-entrypoint-initdb.d/01-seed.sql:ro
```
`seed.sh` is retained for *re-seeding* a running stack.

## Proof: clean re-up from zero (no manual seed)

```
$ docker compose down -v          # full teardown incl. volumes
$ docker compose up -d --build    # clean re-up
$ docker compose ps
d2-stack-api-1        Up (healthy)
d2-stack-database-1   Up (healthy)
d2-stack-worker-1     Up

$ ./scripts/integration-test.sh   # NO seed.sh run first
{"status":"ok","db":"up"}
  -> {"id":2,"payload":"hello-d2","status":"pending"}
  -> final job: {"id":2,...,"status":"done","result":"HELLO-D2","processed_by":"worker-1"}
[e2e] PASS

$ docker compose logs worker | grep -c "does not exist"
0                                  # was crash-looping before the fix
processed job job_id=1 result=SEED-JOB
processed job job_id=2 result=HELLO-D2
```

## Inter-service communication proof (services actually talked)
- **api logs:** `POST /jobs -> 201`, `GET /jobs/2 -> 200`, `GET /health -> 200` (DB connectivity).
- **worker logs:** structured JSON `processed job` lines for job ids 1 & 2 — worker polled the
  DB, ran the job (uppercase payload), and wrote the result back.
- The e2e assertion `result=HELLO-D2` only passes if API→DB→worker→DB all functioned.

## Result
All D2 document requirements satisfied: compose + per-service Dockerfiles, auto-seed,
one-command green e2e, inter-service logs, teardown + **clean re-up from zero**.
