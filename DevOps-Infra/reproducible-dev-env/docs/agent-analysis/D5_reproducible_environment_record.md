# D5 Reproducible Development Environment Record

## 1. Environment Strategy & Toolchain Blueprint
* **Chosen Reproducibility Strategy:** **mise (version-locker) + Makefile (`make bootstrap` entrypoint).**
* **Architectural Justification:** the repo is a **polyglot monorepo** (Python + Node + Rust + Docker
  + Terraform). A single language-specific tool (e.g. a Python venv or a Node-only devcontainer)
  can't pin all three runtimes. **mise** pins Python/Node/Rust to exact versions in one declarative
  file (`mise.toml`), installs them precompiled (fast, no per-language version managers), and works
  on the bare host (no Docker prerequisite for the toolchain). A thin **Makefile** then chains the
  full lifecycle into one atomic command. This is the cleanest path: one locker for all runtimes,
  one entrypoint, runnable from a fresh clone with only `mise` + `make` present. (Dev Containers /
  Nix were rejected: Dev Containers force a Docker dependency for everyday dev; Nix's learning curve
  and flake overhead are disproportionate for three mainstream runtimes.)
* **Version Pinning Matrix:**
  | Runtime/Tool | Exact Target Version | Lock Mechanism Used | Source Reference |
  |--------------|----------------------|---------------------|------------------|
  | Python | 3.12.7 | `mise.toml` `[tools]` + `.tool-versions` | Dockerfiles `FROM python:3.12-slim` |
  | Node.js | 22.11.0 (LTS) | `mise.toml` + `.tool-versions` | `package.json` (jest 29); LTS (no `engines` pin) |
  | Rust | 1.83.0 | `mise.toml` + `.tool-versions` | `Cargo.toml` `edition = "2021"` |
  | Python deps | pinned `==` | per-project `requirements*.txt` | e.g. `DevOps-Infra/ci-pipeline/requirements.txt` |
  | Node deps | locked | `package-lock.json` (+ `npm ci`-style install) | `Basics/node-transaction-service/package-lock.json` |
  | Rust deps | locked | `Cargo.lock` | `Basics/rust-logcount-cli/Cargo.lock` |

## 2. Infrastructure as Code Developer Configurations

### Toolchain Definition Artifact
```toml
# mise.toml
[settings]
python.github_attestations = false   # corporate proxy blocks GitHub attestation API; checksum still verified

[tools]
python = "3.12.7"
node   = "22.11.0"
rust   = "1.83.0"

[env]
PYTHONDONTWRITEBYTECODE = "1"

[tasks.bootstrap]
run = "make bootstrap"
[tasks.verify]
run = "make test"
```
```makefile
# Makefile (bootstrap-relevant targets)
MISE := $(shell command -v mise 2>/dev/null)
RUN  := $(if $(strip $(MISE)),mise exec --,)     # run under the pinned toolchain

bootstrap: doctor setup-env test    ## Fresh-clone onboarding: runtimes -> deps -> env -> verify
doctor:      # mise install + report active python/node/cargo versions
setup-env:   # cp .env.example .env (no overwrite)
rust:  @for d in $(RUST_PROJECTS); do (cd "$$d" && $(RUN) cargo test); done
node:  @for d in $(NODE_PROJECTS); do (cd "$$d" && $(RUN) npm install && $(RUN) npm test); done
python:@for d in $(PY_PROJECTS); do (cd "$$d" && $(RUN) python -m venv .venv && . .venv/bin/activate \
          && pip install -r requirements.txt && python -m pytest -q); done
test: rust node python
```
(`.tool-versions` mirrors the pins for asdf compatibility; `.env.example` documents all env vars.)

### Single-Command Entrypoint
```bash
make bootstrap
# Fresh Clone -> mise install (pinned runtimes) -> install deps (lockfiles) -> generate .env -> build + test
```

## 3. Verification & Simulation Pipeline (clean-slate)

### Runtime Installation (mise)
```text
$ mise install
mise node@22.11.0   ✓ installed
mise rust@1.83.0    ✓ installed
mise python@3.12.7  ✓ installed
$ mise ls --current
node    22.11.0   mise.toml  22.11.0
python  3.12.7    mise.toml  3.12.7
rust    1.83.0    mise.toml  1.83.0
```

### Clean-slate bootstrap (`make clean` then `make bootstrap`)
```text
$ make clean
cleaned                                  # removed ALL .venv / node_modules / target

$ make bootstrap
== toolchain ==
python: Python 3.12.7  |  node: v22.11.0  |  cargo: cargo 1.83.0
== generated .env from .env.example ==
== rust: Basics/rust-logcount-cli ==              test result: ok. 7 passed; 0 failed
== rust: Advanced/polyglot-fraud-system/rust-engine == test result: ok. 6 passed; 0 failed
== node: Basics/node-transaction-service ==              Tests: 7 passed, 7 total
== node: Intermediate/polyglot-currency-pair/node-client == Tests: 9 passed, 9 total
== node: Advanced/polyglot-fraud-system/node-worker ==     Tests: 12 passed, 12 total
== python: Basics/fastapi-transaction-service ==                       6 passed
== python: Intermediate/bug-diagnosis ==            5 passed
== python: Advanced/parallel-expense-tracker ==               16 passed
== python: Advanced/polyglot-fraud-system/fastapi-service == 10 passed
== python: Intermediate/polyglot-currency-pair/fastapi-service == 7 passed
== ALL SUITES PASSED ==
✅ BOOTSTRAP COMPLETE — repository is runnable.
```

### Deterministic Test Engine Run
* **Test Automation Command:** `make bootstrap` (or `make test` / `make verify`)
* **Test Suite Output Logs (100% green — 85 tests across 3 languages, 10 components):**
```text
Rust:   B6 7 + A3-engine 6                          = 13 passed
Node:   B5 7 + I4-client 9 + A3-worker 12           = 28 passed
Python: B4 6 + I6 5 + A2 16 + A3-fastapi 10 + I4 7  = 44 passed
TOTAL:  85 passed, 0 failed   →  ✅ ALL SUITES PASSED
```

## 4. Discovered & Extracted Assumptions
* **Previously Implicit System Requirements (now automated):**
  - No repo-level runtime pinning (only `python:3.12-slim` inside Dockerfiles) → now pinned in `mise.toml` + `.tool-versions` and installed by `mise install`.
  - No single onboarding command (each component had its own test invocation) → now `make bootstrap`.
  - Env vars (`DATABASE_URL`, `QUEUE_DIR`, `API_URL`, `A3_INTERNAL_TOKEN`, `ENGINE_BIN`, `WORKER_ID`, `POLL_INTERVAL`, `PORT`) were set ad-hoc → now declared in `.env.example`, auto-copied to `.env`.
  - Node version was unstated (no `engines`) → pinned to 22 LTS explicitly.
* **Known Workspace Limitations / Edge Cases:**
  - **Prerequisites:** `mise` + `make` on the host. (`mise install` needs network to fetch runtimes; behind a corporate TLS proxy set `python.github_attestations = false` — already in `mise.toml`.)
  - **Docker** is required only for the container/compose tasks (D2/D3/A2/A3 image builds, `make a3-integration`), not for the runtime/test toolchain.
  - Platform validated: macOS arm64. mise serves the same pins for linux/x86_64 (CI/Codespaces).
  - The only test-log "warnings" are upstream library **deprecation notices** (FastAPI `on_event`, Starlette TestClient/httpx) inside pytest output — not setup/build warnings; the bootstrap chain itself is warning-free.

## 5. README Integration & Runbook Requirements
```markdown
### Getting Started
1. **Prerequisites:** `mise` (https://mise.jdx.dev) and `make`. (Docker only for the container/compose tasks.)
2. **Setup Environment:** `make bootstrap`   # installs pinned runtimes, all deps, generates .env, builds + tests
3. **Run Test Verification:** `make test`     # (or `make verify`) — full suite across Python/Node/Rust
4. **Environment Variables:** `make setup-env` copies `.env.example` -> `.env`; edit `.env` to override
   locally (e.g. `DATABASE_URL`, `A3_INTERNAL_TOKEN`). Apps read these from the process environment.
```

## Completion Checklist Gating
* [x] Precise bootstrap + version-pinning configs at workspace root (`mise.toml`, `.tool-versions`, `.env.example`, `Makefile`).
* [x] Env variables/stubs auto-populated by the script (`make setup-env` → `.env`).
* [x] Toolchain isolation driven by a single command (`make bootstrap`, runtimes via `mise exec`).
* [x] Project builds + passes its complete test suite under the automated runtime (**85/85 green**, clean-slate).
* [x] This record populated with raw terminal logs (no placeholders).
