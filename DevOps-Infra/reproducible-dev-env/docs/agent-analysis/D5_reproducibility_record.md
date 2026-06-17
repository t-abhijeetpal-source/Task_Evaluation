# D5 — Reproducibility Verification Record

Verified 2026-06-17 by bootstrapping a **simulated fresh clone** (`rsync` of tracked
files only — no `.venv`, no caches — into `/tmp/d5-freshclone`) and running the single
command there.

## Bootstrap config files
* `mise.toml` — pinned `python = 3.12.8`, `node = 22.12.0`, `[env]`, and the attestation setting.
* `Makefile` — `.DEFAULT_GOAL := bootstrap`; one command = `make`.
* `scripts/bootstrap.sh` — install toolchain → venv → deps → tests.
* `.devcontainer/devcontainer.json` — alternative container-based bootstrap.

## The single command and its full output
`make` (from `/tmp/d5-freshclone`):
```
==> [1/4] Trust + install pinned toolchain from mise.toml
mise python@3.12.8 ✓ installed
    using Python: ~/.local/share/mise/installs/python/3.12.8/bin/python
    using Node:   ~/.local/share/mise/installs/node/22.12.0/bin/node
==> [2/4] Create virtualenv (.venv) with the pinned Python
==> [3/4] Install dependencies (requirements-dev.txt)
==> [4/4] Run tests
....                                                                     [100%]
4 passed, 1 warning in 1.03s
==> Bootstrap complete.
```
`make` exit code: `0`. Wall time: ~40s (cold — includes downloading Python+Node).
Full log: `D5_bootstrap_output.txt`.

## Passing test run
`4 passed` — including `test_runtime_is_pinned_312`, which asserts
`sys.version_info[:2] == (3, 12)`. The venv path resolves to
`.venv/lib/python3.12/...`, proving the bootstrap used the **mise-pinned** Python,
not the host interpreter (the host runs Python 3.14).

## Gap found and fixed during verification
**First run failed:** `mise ERROR Failed to install python@3.12.8: No GitHub artifact
attestations found ... gpg not found, skipping verification`. mise verifies Python
builds via GitHub attestations, which require `gpg` — absent on this (clean) machine.
This was an **implicit system dependency** that would break a real fresh clone.

**Fix:** declared in `mise.toml`:
```toml
[settings]
python.github_attestations = false   # checksums still verified; no gpg dependency
```
Re-run from a fresh clone then succeeded end-to-end (output above). Node had already
installed cleanly; only Python was affected.

## What was previously implicit (now explicit)
- **Python version** — host default was 3.14 (caused Starlette/httpx deprecation drift); now pinned to 3.12.8.
- **Node version** — now pinned to 22.12.0.
- **`gpg`** — was an undeclared prerequisite of mise's attestation step; now bypassed via settings.
- **`APP_ENV`** env var — now declared in `mise.toml [env]` and the devcontainer.
- **Dependency versions** — pinned with `==` in `requirements*.txt`.

## Agent vs. human-verified
* **Agent hypothesis:** `mise install` + venv + pip would bootstrap cleanly in one shot.
* **Verified outcome:** *Refuted on first run* — the gpg/attestation dependency surfaced
  only by actually executing from a clean directory. Fixed and re-verified. The "4 passed"
  and the pinned-3.12 assertion are from real command output, not assumed.
