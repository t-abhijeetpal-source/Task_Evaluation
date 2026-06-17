# D5 — Environment Discovery & Toolchain Audit (Phase 1)

> Every tool/version below maps to a direct file in the repo (Direct Evidence Rule). No assumptions.
> Target: the `Task_Eval` polyglot monorepo. Date: 2026-06-17.

## Primary languages & package managers (evidence)

| Language | Package manager | Evidence (files in repo) |
|---|---|---|
| **Python** | pip (+ venv) | 8 `requirements*.txt` — e.g. `Basics/fastapi-transaction-service/requirements.txt`, `Advanced/parallel-expense-tracker/requirements.txt`, `Advanced/polyglot-fraud-system/fastapi-service/requirements.txt`, `Intermediate/polyglot-currency-pair/fastapi-service/requirements.txt`, `Intermediate/bug-diagnosis/requirements.txt`, `DevOps-Infra/ci-pipeline/requirements.txt` + `requirements-dev.txt` |
| **Node.js** | npm | 3 `package.json` — `Basics/node-transaction-service/package.json` (jest `^29.7.0`, `test: jest`), `Intermediate/polyglot-currency-pair/node-client/package.json`, `Advanced/polyglot-fraud-system/node-worker/package.json`; lockfiles `package-lock.json` present |
| **Rust** | cargo | 2 `Cargo.toml` — `Basics/rust-logcount-cli/Cargo.toml`, `Advanced/polyglot-fraud-system/rust-engine/Cargo.toml` (both `edition = "2021"`); `Cargo.lock` present |

## Strict runtime versions (evidence)

| Runtime | Target version | Direct evidence |
|---|---|---|
| Python | **3.12** | every Dockerfile: `FROM python:3.12-slim` (A2, A3, D2 api/worker, D3, I5) |
| Node | **22 LTS** | `package.json` use jest 29 / CommonJS; no `engines` pin found → LTS chosen (documented assumption made explicit) |
| Rust | **1.83 (2021 edition)** | `Cargo.toml` `edition = "2021"` |

## Build tools (evidence)
- `make` — root `Makefile` (test/build entrypoint).
- `docker` + `docker compose` — `Dockerfile`s + `DevOps-Infra/docker-compose-stack/docker-compose.yml`, `DevOps-Infra/ci-pipeline/Dockerfile`.
- `terraform` — `DevOps-Infra/terraform-aws-stack/*.tf` (`versions.tf` pins `>= 1.6.0, < 2.0.0`).
- test runners: `pytest` (`pytest.ini`), `jest` (`package.json`), `cargo test` (`tests/`).

## Environment variables (evidence — grepped from source)
`DATABASE_URL`, `QUEUE_DIR`, `API_URL`, `ENGINE_BIN`, `WORKER_ID`, `POLL_INTERVAL`, `PORT`,
`A3_INTERNAL_TOKEN` — referenced in `Advanced/parallel-expense-tracker/app/database.py`, `Advanced/polyglot-fraud-system/**`,
`DevOps-Infra/docker-compose-stack/**`. Previously these were **implicit** (only set ad-hoc in compose/run commands).

## System-level / native dependencies (evidence)
- **PostgreSQL** — required by A2/A3/D2 at runtime; provided via container (`postgres:16-alpine` in `D2/docker-compose.yml`). No host Postgres needed.
- **psycopg[binary]** — bundles libpq (no system libpq build dep). (`*/requirements.txt`)
- **Docker engine** — needed only for the container/compose tasks (D2/D3/I5/A2 image builds).
- No other native compile deps (pure-Python wheels; precompiled Rust/Node).

## Previously-implicit assumptions now made explicit
1. **No runtime version pinning existed** at the repo level — only `python:3.12-slim` inside Dockerfiles; host Python/Node/Rust versions were ambient. → now pinned in `mise.toml` + `.tool-versions`.
2. **No single setup command** — each component had its own `pytest`/`npm test`/`cargo test`. → now `make bootstrap`.
3. **Env vars undocumented** — set ad-hoc per command. → now `.env.example` (auto-instantiated to `.env`).
4. **Node version unstated** (no `engines`) — → pinned to 22 LTS explicitly.

These findings drive the Phase 2–6 reproducibility design (see `D5_reproducible_environment_record.md`).
