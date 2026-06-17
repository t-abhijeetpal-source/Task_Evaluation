# D5 — Reproducible Dev Environment from a Fresh Clone

A fresh clone builds and passes its tests with **one command**, on a clean machine,
using **pinned runtime versions** — no "works on my machine" drift.

## The single command

```bash
make
```

That's it. `make` (default target → `scripts/bootstrap.sh`):
1. installs the pinned toolchain from `mise.toml` (`mise install`),
2. creates an isolated `.venv` using the pinned Python,
3. installs dependencies (`requirements-dev.txt`),
4. runs the test suite.

Full captured output: [`docs/agent-analysis/D5_bootstrap_output.txt`](docs/agent-analysis/D5_bootstrap_output.txt).
Verification record: [`docs/agent-analysis/D5_reproducibility_record.md`](docs/agent-analysis/D5_reproducibility_record.md).

## Prerequisite (one-time, per machine)

[`mise`](https://mise.jdx.dev) — the version manager that reads `mise.toml`:
```bash
brew install mise        # or: curl https://mise.run | sh
```
Everything else (Python, Node, dependencies) is installed *by* `make` at the exact
pinned versions. No system Python/Node required.

## Pinned toolchain (`mise.toml`)

| Tool | Version | Why pinned |
|---|---|---|
| python | 3.12.8 | tests assert 3.12; avoids host-Python drift (this host runs 3.14) |
| node | 22.12.0 | repo is polyglot; one declared Node for all clones |

Plus declared env (`APP_ENV`, `PYTHONDONTWRITEBYTECODE`) that was previously implicit.

## Other targets

```bash
make test       # run tests in the existing venv
make run        # serve the app on :8000
make doctor     # show the resolved pinned toolchain (mise ls)
make clean      # remove .venv
make help       # list targets
```

## Alternative bootstrap: Dev Container

`.devcontainer/devcontainer.json` reproduces the same environment in VS Code /
GitHub Codespaces (Python 3.12.8 + Node 22.12.0 features), running the test suite
on start via `postStartCommand`.

## What was previously implicit (now explicit)

| Previously implicit | Now declared in |
|---|---|
| Python version (host had 3.14 → deprecation drift) | `mise.toml` `python = "3.12.8"` |
| Node version | `mise.toml` `node = "22.12.0"` |
| `gpg` needed for mise's Python attestation verification | `mise.toml` `[settings] python.github_attestations = false` |
| `APP_ENV` environment variable | `mise.toml` `[env]` + devcontainer |
| Exact dependency versions | `requirements*.txt` (`==` pins) |
