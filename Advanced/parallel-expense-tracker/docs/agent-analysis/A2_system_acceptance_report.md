# A2 — System Acceptance Report

> System: Expense Tracker (FastAPI + SQLite + vanilla-JS frontend + pytest + Docker/CI).
> Built by 6 parallel workstream agents against a locked contract; integrated, run, and verified by
> the coordinator. Status: **ACCEPTED — integration-verified, tests pass, deploys in Docker.**
> Original date: 2026-06-17. Env (corrected): **Python 3.12.7** (pinned via mise; the original
> "3.14" claim was wrong) · FastAPI · SQLAlchemy 2 · Docker (Colima).

---

## ⚠️ 2026-06-21 — Production-hardening update (supersedes claims below)

The original report (below) **overclaimed** on several points. This section is the
current source of truth; the original is retained for history. All items verified
under Python 3.12.7 via `make a2-verify` (warm: ~8s) and `A2_DOCKER=1` (container).

| Original claim | Reality at the time | Now |
|---|---|---|
| "DB schema ↔ ORM reconciled, with `CHECK`" | **False at runtime** — startup used `Base.metadata.create_all`, which emits no `CHECK` and no indexes; `db/schema.sql` was never executed | **Fixed.** Startup + tests apply `db/migrations/*.sql` (`app.database.run_migrations`). `CHECK(amount_cents>0)`, `CHECK(length(category)>0)`, and both indexes now exist at runtime and are asserted by `tests/test_schema_honesty.py`. |
| `amount: float` end-to-end | NaN → **HTTP 500**; `0.1+0.2` drift; overflow → `total: null` | **Fixed.** Money is **integer cents**; aggregation in SQL is exact. NaN/Inf/sub-cent/overflow → `422` (regression-tested, incl. raw JSON literals). |
| Shallow `/api/health` (200 even if DB dead) | true | **Fixed.** Deep health does `SELECT 1` → `503` on DB failure; Docker HEALTHCHECK acts on it. |
| "16/16 tests" | true then | **40 tests** (unit + integration + money regression + schema-honesty + deep-health + validation/pagination). |
| CI workflow nested in A2 folder | Would never run on GitHub | Root workflow `.github/workflows/a2-parallel-expense-tracker.yml` runs `pytest + integration smoke + perf gate + docker build/smoke`. |
| pytest in the production image | true | **Fixed.** `requirements.txt` (prod) and `requirements-dev.txt` (tests) split; image installs prod only. |
| No one-command verify / no `CONTRACT.md` | true | `make a2-verify`; `CONTRACT.md` is the locked contract. |
| Frontend `fmtMoney(null)` → fake `$0.00` | true | Null/non-finite summary renders **"unavailable"** + error status; `fetch` has an 8s timeout. |
| Temp test DB never cleaned | `mkdtemp` leaked | `pytest_sessionfinish` disposes the engine and removes the temp dir. |

**A6 linkage:** `GET /api/summary` aggregates via SQL `GROUP BY` over an indexed
integer-cents column. `scripts/perf_guard.py` gates p50 ≤ 50 ms @ 50k rows (40 ms warn band)
(measured p50 ≈ 31–35 ms locally).

---

## Components Delivered

| Component | Workstream / Agent | Key files | Status |
|---|---|---|---|
| Backend (API + business logic) | Backend | `app/{main,database,models,schemas,routes}.py` | ✅ |
| Frontend (UI + API integration) | Frontend | `static/index.html`, `static/app.js` | ✅ |
| Database (schema + migration + seed) | Database | `db/schema.sql`, `db/migrations/0001_init.sql`, `db/seed.sql` | ✅ |
| Tests (unit + integration) | QA | `tests/{conftest,test_api,test_integration}.py`, `pytest.ini` | ✅ |
| Deployment (Docker + CI) | DevOps | `Dockerfile`, `.dockerignore`, `docker-compose.yml`, `.github/workflows/ci.yml` | ✅ |
| Documentation | Docs | `README.md`, `RUNBOOK.md` | ✅ |

All 6 workstreams completed; reports in `docs/agent-analysis/A2_<role>.md`.

---

## Integration Results (Phase 3 — every connection verified)

| Integration point | Verified how | Result |
|---|---|---|
| Frontend ↔ Backend | `app.js` calls relative `/api/expenses` + `/api/summary`; backend exposes exactly those | ✅ aligned (grep + live curl) |
| Backend ↔ Database | `Base.metadata.create_all` on startup; CRUD persists to SQLite | ✅ live POST→GET round trip |
| Backend ↔ Frontend serving | `app.mount("/", StaticFiles(html=True))` after router | ✅ `GET /` → 200, 5033 bytes; `/app.js` → 200 |
| Tests ↔ System | conftest temp-DB override before import; TestClient | ✅ 16/16 pass |
| CI ↔ Build | workflow: pip install → pytest → docker build | ✅ YAML valid; build step verified locally |
| DB schema ↔ ORM | `db/schema.sql` matches `app/models.py` (REAL/TEXT/INTEGER, PK, CHECK) | ⚠️ **superseded** — the `CHECK`/indexes were NOT applied at runtime (`create_all`). Fixed via migrations; see the 2026-06-21 hardening update above. |

**No component accepted without integration verification** (completion rule satisfied).

---

## Test Results (VERIFIED — executed)

```text
$ pytest -v
... tests/test_api.py (12) + tests/test_integration.py (4) ...
======================== 16 passed, 3 warnings in 0.15s ========================
```
**16 passed, 0 failed.** (Warnings: Starlette TestClient httpx deprecation + FastAPI `on_event` deprecation — non-blocking; see Known Issues.)

### Live server (uvicorn) — captured
```text
GET  /api/health                         -> {"status":"ok"}
POST /api/expenses {12.5, food}          -> 201 {id:1,...,created_at:...}
POST /api/expenses {40, transport}       -> 201 {id:2,...}
POST /api/expenses {-5, food}            -> HTTP 422 {"error":"amount must be positive"}
GET  /api/expenses                       -> [id:2, id:1]  (newest first)
GET  /api/summary                        -> {"total":52.5,"count":2,"by_category":{"food":12.5,"transport":40.0}}
GET  /                                   -> HTTP 200, 5033 bytes (frontend)
GET  /app.js                             -> HTTP 200
```

---

## Deployment Results (VERIFIED — Docker via Colima)

```text
$ docker build -t expense-tracker:a2 .      -> Successfully tagged expense-tracker:a2  (312 MB)
$ docker run -d -p 8091:8000 expense-tracker:a2
$ docker ps                                 -> expense  Up (healthy)  0.0.0.0:8091->8000/tcp
$ curl localhost:8091/api/health            -> {"status":"ok"}
$ curl -X POST .../api/expenses {99,utilities}; curl .../api/summary
                                            -> {"total":99.0,"count":1,"by_category":{"utilities":99.0}}
$ curl localhost:8091/                      -> HTTP 200, 5033 bytes (frontend in container)
```
Container reaches **healthy** (Docker HEALTHCHECK on `/api/health`); API + frontend both serve from the image.

---

## Agent Conflict Resolution

| Issue | Affected | Resolution | Evidence |
|---|---|---|---|
| QA's `test_root_serves_html_page` depends on `static/index.html`, built in a parallel lane (empty at author time) | QA ↔ Frontend | Cross-lane dependency, not a true conflict — Frontend delivered `index.html` (5033 bytes) before Phase 4, so the test passed. | test PASSED; `GET /` 200 |
| Two schema sources: ORM (`app/models.py`) + raw SQL (`db/schema.sql`) could drift | Backend ↔ Database | Both authored to the locked contract; app uses ORM `create_all` at runtime, `db/schema.sql` is the canonical/portable DDL (with an added `CHECK(amount>0)` DB guard). Coordinator confirmed they match. | column types/PK match; 422 guard at API |

No blocking conflicts; both items reconciled against the contract.

---

## Risks

1. **SQLite single-writer (LOW–MED):** fine for a single-instance app; not for high-concurrency or multi-replica deploys → move to Postgres if scaling.
2. **`create_all` vs migrations (LOW):** runtime uses `create_all` (no Alembic); schema changes need a real migration tool for production evolution. `db/migrations/0001_init.sql` is a starting point.
3. **No auth (LOW, by design):** API is open; add auth before exposing publicly.
4. **Data persistence in Docker:** relies on the `./data` volume mount (compose) — without it, container restarts lose data.

## Known Issues

- Deprecation warnings: FastAPI `@app.on_event("startup")` (use lifespan handlers) and Starlette TestClient/httpx notice. Non-blocking; tidy-up items.
- No client-side pagination on the expenses list (fine at small scale).

## Rollback Strategy

- **App/image:** redeploy the previous image tag (`docker run … expense-tracker:<prev>`), or `git revert` the commit; CI rebuilds.
- **Data:** SQLite is a single file — back up `data/expenses.db` (or `sqlite3 .dump`) before changes; restore by replacing the file. (See `RUNBOOK.md`.)
- **Compose:** `docker compose down` then `docker compose up` from a known-good tag.

---

## Completion criteria

- [x] All 6 agents executed (parallel, disjoint ownership)
- [x] All workstreams completed (reports + artifacts)
- [x] Integration verified (every connection, live + container)
- [x] Tests passed (16/16)
- [x] Documentation completed (README + RUNBOOK + 6 reports)
- [x] Acceptance report generated (this file)
- [x] Master report generated (`A2_master_report.md`)
- [x] Evidence attached (commands + outputs + exit/health states captured)
