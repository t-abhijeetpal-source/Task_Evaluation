# D5 — Reproducibility Verification Record

Verified by bootstrapping a **simulated fresh clone** (`scripts/verify-fresh-clone.sh`:
`rsync` of git-tracked files only — no `.venv`, no caches — into a temp dir) and
running the single command there. Scope is **this folder only**; the repo-root
monorepo bootstrap (85 tests) is verified separately in root `docs/BOOTSTRAP.md`.

## Bootstrap config files
* `mise.toml` — pinned `python = 3.12.8`, `node = 22.12.0`, `[env]`, attestation setting.
* `.tool-versions` + `.python-version` — mirror the pins (asdf compat / tooling).
* `Makefile` — `.DEFAULT_GOAL := bootstrap`; one command = `make`.
* `scripts/bootstrap.sh` — install → **verify pins (python + node)** → venv (if missing)
  → deps (if changed) → ruff + mypy → pytest --cov.
* `scripts/verify-fresh-clone.sh` / `scripts/check-toolchain-sync.sh` — proofs + drift guard.
* `.devcontainer/devcontainer.json` — alternative container bootstrap on the same mise path.

## The single command and its full output
`make` (cold, from a simulated fresh clone):
```
==> [1/6] Trust + install pinned toolchain from mise.toml
    using Python: ~/.local/share/mise/installs/python/3.12.8/bin/python
    using Node:   ~/.local/share/mise/installs/node/22.12.0/bin/node
==> [2/6] Verify runtimes match the pins
    python: Python 3.12.8   node: v22.12.0  (pinned v22.12.x)
==> [3/6] Create virtualenv (.venv) with the pinned Python (only if missing)
==> [4/6] Install dependencies (skip if requirements unchanged)
==> [5/6] Quality gates (ruff + mypy)
All checks passed!  /  Success: no issues found in 8 source files
==> [6/6] Run tests (with coverage gate)
...........................                                              [100%]
Required test coverage of 80% reached. Total coverage: 100.00%
27 passed in 0.41s
```
`make` exit code: `0`. Full log: `D5_bootstrap_output.txt`.

## Passing test run
**27 passed, 100% statement coverage, 0 warnings.** Includes:
* `test_python_runtime_is_pinned` — `.venv` runs the mise-pinned **3.12.x**, not the
  host interpreter (host is 3.14). The venv path resolves to `.venv/lib/python3.12/...`.
* `test_node_toolchain_pinned` — resolves Node via `mise which node` and asserts
  `v22.12.x` (Node is now *verified*, not merely declared).
* `POST /v1/add` happy path + 422 on unknown keys / out-of-range; deprecated `GET /add`;
  security headers + `X-Request-ID` on every response; `/metrics` scrape; server-error
  path; CORS allow-list parsing.

## Idempotency (real timings, this host)
```
cold (make clean && make):  17.99s
warm (make again):           2.08s   # ".venv already present — reusing" + "skipping pip install"
verify (no install):         1.71s
```

## Gaps found and fixed during verification
1. **gpg/attestation (pre-existing).** `mise` verifies Python builds via GitHub
   attestations, which need `gpg` — absent on a clean machine. Bypassed via
   `mise.toml [settings] python.github_attestations = false` (checksums still verified).
2. **Node pinned but unverified.** Bootstrap declared Node but never checked it.
   Fixed: bootstrap step 2 fails if `node --version` ≠ `v22.12.x`, plus a test asserts it.
3. **Wasteful re-bootstrap.** `.venv` was recreated and deps reinstalled every run.
   Fixed: venv-if-missing + `requirements*.txt` content hash → warm run is ~8× faster.
4. **Zero-warning gate vs. upstream deprecation.** `filterwarnings = error` surfaced a
   Starlette/httpx `TestClient` deprecation. Adopting the suggested `httpx2` package was
   **rejected** (unvetted, typosquat-shaped, not in any lockfile); instead the single
   upstream warning is scoped-ignored with a documented reason, so app-origin warnings
   still fail. See `docs/RUNBOOK.md`.

## Agent vs. human-verified
* **Agent hypothesis:** `mise install` + venv + pip + gates would bootstrap cleanly,
  and Node + Python pins would resolve to the declared versions.
* **Verified outcome:** confirmed by **actually running** `make`, `make verify`,
  `make verify-fresh`, and `check-toolchain-sync.sh`. The "27 passed", the
  100% coverage, the pinned-3.12 + pinned-node assertions, and the cold/warm timings
  are real command output, not assumed.
