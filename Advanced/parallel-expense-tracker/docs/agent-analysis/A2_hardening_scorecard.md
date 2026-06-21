# A2 — Production-Hardening Scorecard

> Self-assessment against the upgrade rubric. Verified 2026-06-21 under the
> pinned toolchain (Python 3.12.7 via mise, Node 22, Docker via Colima) with
> `make a2-verify` and `A2_DOCKER=1 make a2-verify`.

## Evidence (reproducible)

```
$ make a2-verify                      # warm venv: ~8s wall-clock
  40 passed in ~0.5s                   # pytest (unit+integration+regression+honesty+health+validation)
  app.js OK                            # node --check static/app.js
  integration smoke: 8 checks passed   # live HTTP incl. NaN→422, exact 12.80 total, static UI
  PERF OK: p50≈31–35ms <= 40ms warn band (50ms ceiling, N=50000)

$ A2_DOCKER=1 make a2-verify
  container healthy (deep /api/health passed inside container)
  POST /api/expenses -> 201 ; GET /api/summary -> total 99.0 ; GET / -> 200
```

## Automatic score caps — all cleared

| Cap condition | Status |
|---|---|
| NaN POST returns 500 → max 70 | **Cleared.** NaN/Inf (incl. raw JSON literals) → `422`; custom validation handler never echoes the non-finite value. `tests/test_money.py::test_nan_amount_returns_422_not_500`. |
| Runtime schema lacks CHECK/indexes while docs claim them → max 75 | **Cleared.** Migrations applied at startup + tests; `tests/test_schema_honesty.py` asserts `CHECK` + indexes on the live DB and that the DB enforces the CHECK. |
| No `make a2-verify` one-command gate → max 80 | **Cleared.** `make a2-verify` exists (pytest + integration + perf + frontend; docker via flag). |
| CI nested, never runs at root, no alternative → max 82 | **Cleared.** Root `.github/workflows/a2-parallel-expense-tracker.yml` (path-filtered); nested copy demoted to `workflow_dispatch` + documented. |
| Blocking fixes without regression tests → max 85 | **Cleared.** Every fix has a regression test (money, schema-honesty, deep-health, validation/pagination). |

## Rubric (target ≥ 90)

| Dimension | Wt | Self-score | Justification |
|---|---|---|---|
| Financial & data correctness | 25 | **24** | Integer cents end-to-end; SQL aggregation exact (`0.1+0.2==0.3`, 100×0.01==1.00 tested); NaN/Inf/sub-cent/overflow → 422; runtime `CHECK` + indexes enforced. (−1: amount on the wire is a JSON number, not a string — standard, documented.) |
| One-command verification | 20 | **20** | `make a2-verify`: 40 tests + live integration smoke + captured output; ~8s warm, well under the 90s budget. |
| Contract & doc honesty | 15 | **15** | `CONTRACT.md` locked; acceptance report corrected (3.12.7, false CHECK claim retracted); README/RUNBOOK updated; deep-health + money documented. |
| DevOps & CI | 15 | **14** | Root CI (test + docker build/smoke); deep health; HEALTHCHECK verified healthy in-container; prod/dev requirements split; `COPY db/` so migrations ship. (−1: SQLite/no Alembic — documented limitation.) |
| Security & validation | 10 | **9** | Amount/category/note bounds; category normalized; pagination with bounds; XSS-safe DOM. (−1: no auth — documented as a demo limitation, not silently claimed secure.) |
| Performance (A6 linkage) | 10 | **10** | `scripts/perf_guard.py` gates p50 ≤ 50ms @ 50k (40ms warn band) via the A6 bench; measured ≈31–35ms; bench updated for the integer-cents schema. |
| Frontend reliability | 5 | **5** | Null/non-finite summary → "unavailable" + error status (no fake $0.00); `fetch` 8s timeout; `node --check` in verify + CI. |
| **Total** | **100** | **97** | ≥ 90 — **ship**. |

## What a skeptic should still know (residual risk)

- **No authentication** — public CRUD + `/docs`. Acceptable for the demo/local
  scope; flagged in README + CONTRACT, not hidden.
- **SQLite + forward-only migrations** — single-writer; no down-migrations or
  `ALTER` of a legacy table. Move to Postgres + Alembic to scale/evolve.
- **Wire `amount` is a JSON number** — exact for ≤2-dp values derived from
  integer cents; a string field would be marginally stricter but breaks the
  existing client/tests for no real-world gain at this scale.
