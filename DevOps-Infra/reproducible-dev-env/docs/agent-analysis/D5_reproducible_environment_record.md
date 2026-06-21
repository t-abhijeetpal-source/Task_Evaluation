# D5 Reproducible Development Environment Record

> **Scope.** This record describes **only what exists in
> `DevOps-Infra/reproducible-dev-env/`** — its local `mise.toml`, local `Makefile`,
> `scripts/bootstrap.sh`, the demo FastAPI service, its 27 tests, and its dev
> container. The **repo-root** monorepo bootstrap (`make bootstrap` → 85 tests
> across Python/Node/Rust) is a *separate* entrypoint documented in
> [root `docs/BOOTSTRAP.md`](../../../../docs/BOOTSTRAP.md). The two are deliberately
> not conflated; `scripts/check-toolchain-sync.sh` keeps their Python/Node pins aligned.

## 0. Two entrypoints (authoritative)

| | **This folder** (`make`) | **Repo root** (`make bootstrap`) |
|---|---|---|
| Command | `cd DevOps-Infra/reproducible-dev-env && make` | `make bootstrap` (repo root) |
| Installs | python 3.12.8 + node 22.12.0 | python 3.12.8 + node 22.12.0 + rust 1.83.0 |
| Runs | this demo's gates + `pytest` | every component's `pytest`/`jest`/`cargo test` |
| Tests | **27** (this service) | **85** (10 components) |
| Doc | this file + folder README | root `docs/BOOTSTRAP.md` |

## 1. Environment Strategy & Toolchain Blueprint
* **Chosen strategy:** **mise (version-locker) + a thin Makefile** whose default
  goal is the full bootstrap, so a fresh clone of this folder is one command: `make`.
* **Why mise here:** even though this demo is Python-only at runtime, the parent
  repo is polyglot and pins a single Node alongside Python. mise pins both in one
  declarative `mise.toml`, installs them precompiled, and needs no Docker for the
  toolchain. The Makefile chains install → verify-pins → venv → deps → gates → tests.
  (Dev Containers / Nix were rejected for everyday host dev: Docker dependency and
  flake overhead respectively. A dev container is still provided as an *alternative*
  that uses the same mise path — see §2.)
* **Version Pinning Matrix (this folder):**
  | Runtime/Tool | Exact version | Lock mechanism | Source / rationale |
  |--------------|---------------|----------------|--------------------|
  | Python | 3.12.8 | `mise.toml` `[tools]`, `.tool-versions`, `.python-version` | tests assert 3.12.x; host runs 3.14 |
  | Node.js | 22.12.0 | `mise.toml` `[tools]`, `.tool-versions` | monorepo parity; **verified live** (see §3) |
  | Python deps | pinned `==` | `requirements.txt` / `requirements-dev.txt` | aligned with sibling `ci-pipeline` (D3) |

  Rust is intentionally **not** present here (no Rust code in this folder); it is a
  root-only pin. `check-toolchain-sync.sh` compares Python + Node across root and D5.

## 2. Infrastructure-as-Code Developer Configurations

### Toolchain definition (`mise.toml`)
```toml
[tools]
python = "3.12.8"
node   = "22.12.0"

[settings]
python.github_attestations = false   # clean machines often lack gpg; checksums still verified

[env]
APP_ENV = "dev"
PYTHONDONTWRITEBYTECODE = "1"
```

### Single-command entrypoint (`Makefile`, default goal = `bootstrap`)
```makefile
bootstrap:    ./scripts/bootstrap.sh           # install -> verify pins -> venv -> deps -> gates -> tests
verify:       ruff + mypy + pytest (existing venv, no install)   # fast inner loop
test:         pytest (coverage gate)
check-sync:   ./scripts/check-toolchain-sync.sh
verify-fresh: ./scripts/verify-fresh-clone.sh
```

### Idempotent / incremental bootstrap (`scripts/bootstrap.sh`)
* Step 2 reads the pinned Node from `mise.toml` and **fails** if the resolved
  `node --version` is not `v22.12.x` (Node was previously pinned but never checked).
* Step 3 creates `.venv` **only if missing**.
* Step 4 hashes `requirements*.txt` into `.venv/.reqs-sha256` and **skips pip**
  when unchanged. Cold ≈ 18s; warm ≈ 2s.

### Dev container (`.devcontainer/devcontainer.json`)
Installs `mise` and runs the same `make` bootstrap (not divergent feature runtimes),
so the container and host read one `mise.toml`. `postStartCommand` runs `make verify`.

### Static analysis & tests
* `ruff.toml` — `E,F,I,UP,B,S,SIM,RUF`. `mypy.ini` — `strict = true` on `app/`.
* `pytest.ini` — `--cov=app --cov-fail-under=80`; `filterwarnings = error` (zero
  warnings) with one scoped ignore for an upstream-only Starlette/httpx deprecation
  (we deliberately do **not** adopt the unvetted `httpx2` package — see RUNBOOK).

## 3. Verification & Simulation Pipeline (clean-slate)

### Runtime install + pin verification
```text
==> [1/6] Trust + install pinned toolchain from mise.toml
    using Python: ~/.local/share/mise/installs/python/3.12.8/bin/python
    using Node:   ~/.local/share/mise/installs/node/22.12.0/bin/node
==> [2/6] Verify runtimes match the pins
    python: Python 3.12.8   node: v22.12.0  (pinned v22.12.x)
```

### Clean-slate bootstrap (`make clean && make`) — real output
```text
==> [3/6] Create virtualenv (.venv) with the pinned Python (only if missing)
    created .venv
==> [4/6] Install dependencies (skip if requirements unchanged)
    dependencies installed
==> [5/6] Quality gates (ruff + mypy)
All checks passed!  /  Success: no issues found in 8 source files
==> [6/6] Run tests (with coverage gate)
...........................                                              [100%]
TOTAL                          149      0   100%
Required test coverage of 80% reached. Total coverage: 100.00%
27 passed in 0.41s
```

### Deterministic test engine run
* **Command:** `make` (or `make verify` / `make test`).
* **Result:** **27 passed, 100% statement coverage, 0 warnings** under Python 3.12.8.
  Suites: `test_calc.py` (pure-function edges), `test_app.py` (health, security
  headers, `POST /v1/add`, deprecated `GET /add`, 422 validation, `/metrics`),
  `test_middleware.py` (server-error path, CORS), `test_toolchain.py` (Python +
  **Node** pin proof). Full log: `D5_bootstrap_output.txt`.

### Idempotency (real timings, this host)
```text
cold (make clean && make):  17.99s
warm (make again):           2.08s   # .venv reused, pip skipped
verify (no install):         1.71s
```

### Fresh-clone simulation (`scripts/verify-fresh-clone.sh`)
`rsync` of **git-tracked files only** (no `.venv`, no caches) into a temp dir, then
`make` there. Asserts exit 0 + a pytest `N passed` summary:
```text
✅ fresh-clone bootstrap succeeded — 27 passed
```

## 4. Discovered & Extracted Assumptions
* **Node was pinned but never verified** → bootstrap now fails if the resolved Node
  is not `v22.12.x`, and `test_node_toolchain_pinned` asserts it via `mise which node`.
* **Bootstrap recreated `.venv` and reinstalled every run** → now incremental
  (venv-if-missing + requirements content hash).
* **Dev container used feature-installed Python/Node** (a path that could drift from
  `mise.toml`) → now installs mise and runs the same `make`.
* **No CI proved a clean-machine bootstrap** → `.github/workflows/d5-reproducible-env.yml`
  installs mise on `ubuntu-latest`, runs `make`, and runs the fresh-clone simulation;
  a sync-guard job fails if root/D5 pins diverge.
* **Record previously described the monorepo bootstrap** (85 tests, Rust, root
  Makefile) while the folder ships a 27-test demo → this record is now folder-scoped
  and cross-links the root bootstrap doc.

### Known limitations / edge cases
* Prerequisites: `mise` + `make`. `mise install` needs network on a cold machine;
  behind a TLS proxy keep `python.github_attestations = false` (already set).
* The one suppressed warning is an **upstream** Starlette/httpx deprecation, not app
  code; every app-origin warning still fails the suite (`filterwarnings = error`).
* Platforms validated: macOS arm64 (locally) + `ubuntu-latest` (CI). macOS CI is
  available opt-in via `workflow_dispatch`.

## 5. Getting Started (folder runbook)
1. **Prerequisite:** install `mise` (`brew install mise` or `curl https://mise.run | sh`).
2. **Bootstrap:** `cd DevOps-Infra/reproducible-dev-env && make`.
3. **Inner loop:** `make verify` (no reinstall). **Tests only:** `make test`.
4. **Prove a clean machine:** `make verify-fresh`. **Pin drift guard:** `make check-sync`.
5. **Run the service:** `make run` (`:8000`). See `docs/RUNBOOK.md` for operations.

## Completion Checklist Gating
* [x] Folder-scoped bootstrap + pinning configs (`mise.toml`, `.tool-versions`, `.python-version`, `Makefile`, `bootstrap.sh`).
* [x] Python **and Node** pins verified live (bootstrap step 2 + `test_toolchain.py`).
* [x] One-command onboarding preserved (`make`), now idempotent/incremental.
* [x] Gates added: ruff + mypy(strict) + pytest coverage (100%), zero warnings.
* [x] Clean-slate + fresh-clone bootstrap verified with **real** logs (27 passed).
* [x] CI proves the bootstrap on a clean Linux runner; sync-guard prevents pin drift.
* [x] Record scoped to this folder; monorepo bootstrap cross-linked, not conflated.
