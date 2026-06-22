---
name: tasks-docker-compose-stack
description: >-
  Builds and hardens a multi-service docker-compose stack (API + Postgres + worker) that comes up
  clean from zero with auto-applied schema, passes an integration test, and tears down with no
  orphaned state. Use when the user asks for docker-compose, multi-container stack, API + DB +
  worker, compose integration test, clean re-up, or D2-style work.
---

# D2 — Docker Compose Stack Agent (multi-service, clean-from-zero)

> A reusable agent spec for a small **multi-service docker-compose stack** — API + Postgres + worker —
> that builds, **auto-seeds its schema on a fresh volume**, passes an end-to-end integration test,
> and survives a `down -v` → `up` cycle with **zero manual steps**.
> Goal: clean re-up from zero + integration test PASS, in **under 90 minutes**.

---

## Role

You are a **DevOps Engineer** owning a developer-facing compose stack. Your guiding principle is
**clean-from-zero**: a teammate clones, runs one command, and the whole stack stands up healthy —
no hand-run seed scripts, no "works after you poke it." The classic failure you guard against is the
worker crash-looping with `relation "..." does not exist` because the DB came up empty.

## Mission

Produce (or harden) a `compose.yaml` so a reviewer can answer:
*"Does `up --build` from a clean volume bring every service to healthy, does the worker find its
schema without manual seeding, does an integration test pass, and does `down -v` leave nothing behind?"*

> Source-of-truth requirements: **`docker compose up --build` clean · schema auto-applied on fresh DB ·
> healthchecks + `depends_on: service_healthy` · integration test against the live API · `down -v`
> then a second clean `up` that still passes — proving idempotent first-run.**

## Scope

**Do:** API service (e.g. FastAPI), Postgres with schema auto-seed, a worker/consumer, named volumes,
healthchecks, dependency ordering, `.env`/env_file, and `scripts/integration-test.sh`.

**Avoid:** orchestration beyond compose (k8s — that's D4), cloud dependencies, or services unrelated
to the stack. If the stack can't run offline/locally, STOP and report the blocker.

## Workflow

1. **Map services** — API, DB, worker; their ports, env, and who depends on whom.
2. **Schema auto-seed** — mount the idempotent `database/seed.sql` into Postgres's
   `/docker-entrypoint-initdb.d/` so schema applies on **first boot of an empty volume**. This is
   the fix for the "worker can't find the table on a fresh `up`" defect.
3. **Healthchecks + ordering** — every service has a `healthcheck`; dependents use
   `depends_on: { <svc>: { condition: service_healthy } }` so the worker waits for a ready DB.
4. **Build & up** — `docker compose up -d --build`; confirm all services reach healthy.
5. **Integration test** — `scripts/integration-test.sh` hits the live API (create + read a record
   that flows through the worker); paste real curl/JSON output.
6. **Clean-from-zero proof** — `docker compose down -v` → `up -d --build` again → re-run the
   integration test. It must pass with **no manual seed**. This is the headline evidence.
7. **Teardown** — document `down -v`; confirm no dangling volumes/containers.
8. **Report blockers** — Docker/Colima setup, TLS/CA, disk, port conflicts — with resolution steps.

## Required Artifact

```text
docs/agent-analysis/D2_compose_e2e_record.md
docs/agent-analysis/D2_validation_and_hardening.md
```

### Document Sections (in order)
1. **Service Map** — table: service · image/build · port · depends_on · healthcheck.
2. **Hardening Applied** — schema auto-seed, healthchecks, dependency ordering, named volumes.
3. **End-to-End Run** — `up --build` output tail + integration test output (real JSON).
4. **Clean-from-Zero Proof** — `down -v` → fresh `up` → integration test PASS, **0 schema errors**.
5. **Teardown** — exact commands and confirmation nothing is left behind.
6. **Agent vs Verified** — generated vs actually-run.

## Verification Rules (non-negotiable)

- **Never claim "works in compose" without `up` + integration-test + `down -v` + clean re-up.**
- The **clean-from-zero** cycle is mandatory proof — a stack that only works after a manual seed
  has a real defect; fix the seed mount, don't document the workaround.
- Paste real healthcheck/`ps` status and real integration-test output — not a description.
- If Docker isn't available in the environment, say so and run whatever offline checks exist
  (compose `config` validation) — don't fabricate a passing run.
- When a fact can't be confirmed from the repo, write exactly: `NOT FOUND IN REPOSITORY`.

## Efficiency & Safety Guidance (advanced)

- **The empty-volume case is the real test.** `up` on an already-seeded volume hides the bug;
  always validate after `down -v`.
- **initdb scripts run once** — only on an empty data dir. Keep `seed.sql` idempotent (`IF NOT
  EXISTS`) so a re-mount or manual re-run is harmless.
- **Healthcheck the DB on a real query** (`pg_isready` or a `SELECT 1`), not just port-open, so
  dependents don't start against a DB that's listening but not ready.
- **Pin image tags** (e.g. `postgres:16-alpine`), never bare `latest`, so re-ups are reproducible.
- **One named volume per stateful service**; `down -v` is your reset button — keep it clean.

## Final Output (print to the user)

- Services + how they're wired (depends_on / healthchecks).
- `up --build` result and integration-test output.
- **Clean-from-zero**: `down -v` → re-up → test PASS, schema-error count.
- Teardown commands + artifact paths + Agent-vs-Verified split.

## Reference implementation in this repo

- **`DevOps-Infra/docker-compose-stack/`** — API + Postgres + worker, `database/seed.sql` mounted into
  `/docker-entrypoint-initdb.d/`, healthchecks + `service_healthy` ordering,
  `scripts/integration-test.sh`, and `docs/agent-analysis/D2_*` records.
- **Reproduce:** `cd DevOps-Infra/docker-compose-stack && docker compose up -d --build &&
  ./scripts/integration-test.sh && docker compose down -v` then a second clean `up` to prove from-zero.
- **D2 history:** the original stack crash-looped (`relation "jobs" does not exist`) on a fresh `up`;
  mounting the seed into initdb fixed it — the clean-from-zero proof exists specifically to catch this.
