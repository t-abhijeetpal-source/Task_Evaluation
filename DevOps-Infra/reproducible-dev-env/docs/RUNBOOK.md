# D5 Reproducible Dev Environment — Operational Runbook

Operational procedures for this folder's bootstrap. For the repo-wide monorepo
bootstrap (85 tests across Python/Node/Rust) see root [`docs/BOOTSTRAP.md`](../../../docs/BOOTSTRAP.md).

## Quick reference

| Task | Command |
|---|---|
| Fresh-clone bootstrap | `cd DevOps-Infra/reproducible-dev-env && make` |
| Fast inner loop (no install) | `make verify` |
| Tests + coverage only | `make test` |
| Prove a clean machine | `make verify-fresh` |
| Guard pin drift (root ⇄ D5) | `make check-sync` |
| Show resolved toolchain | `make doctor` |
| Serve on :8000 | `make run` |
| Rebuild venv from scratch | `make clean && make` |

## 1. `mise trust`

`mise` refuses to load a `mise.toml` it has not been told to trust (a safety feature
against malicious configs in cloned repos). `scripts/bootstrap.sh` runs
`mise trust --yes` automatically. To do it manually:

```bash
mise trust            # trust the config in the current directory
mise trust --yes      # non-interactive (used by bootstrap + CI)
```

## 2. Corporate proxy / offline notes

* `mise install` downloads precompiled Python/Node from GitHub releases. Behind a
  TLS-intercepting proxy, set the usual `HTTPS_PROXY`/`HTTP_PROXY` env vars.
* Python standalone builds are normally checked against **GitHub artifact
  attestations**, which require `gpg`. On clean/proxied machines `gpg` is often
  absent or the attestation API is blocked, so `mise.toml` sets
  `python.github_attestations = false`. **Checksum** verification of the download
  still applies — this only drops the attestation signature step, not integrity.
* Air-gapped: pre-seed `~/.local/share/mise/installs/{python,node}/<version>` from a
  mirror; `mise install` is then a no-op ("all tools are installed").

## 3. gpg / attestation troubleshooting

Symptom on a clean machine:
```
mise ERROR Failed to install python@3.12.8: No GitHub artifact attestations found …
           gpg not found, skipping verification
```
Cause: attestation verification is on and `gpg` is missing. Fix is already in
`mise.toml` (`python.github_attestations = false`). If you see this, confirm you are
reading **this folder's** `mise.toml` (`mise config ls`) and that it is trusted (§1).

## 4. Bumping a pinned version

Pins live in **four** files that must stay in lockstep (Python in all four, Node in
the first three). The sync guard fails CI if they drift.

1. Edit `mise.toml` (`[tools]`).
2. Edit `.tool-versions` (asdf format: `python`, `nodejs`).
3. Edit `.python-version` (Python only).
4. If bumping Python/Node, also edit the **repo-root** `mise.toml` and `.tool-versions`
   (Python + Node are shared; Rust is root-only).
5. Run the guard + rebuild:
   ```bash
   make check-sync          # must pass
   make clean && make       # reinstall + full gates + tests
   make verify-fresh        # clean-machine proof
   ```
6. Refresh the captured evidence in `docs/agent-analysis/D5_bootstrap_output.txt`.

## 5. Bootstrap failure troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `ERROR: mise is not installed` | mise missing / not on PATH | `brew install mise` or `curl https://mise.run | sh`; reopen shell |
| `node <v…> does not match pinned v22.12.x` | stale/global Node shadowing mise | `mise install`; ensure `mise which node` resolves under `~/.local/share/mise` |
| `No GitHub artifact attestations` | gpg/attestation (see §3) | already handled by `mise.toml`; verify config is trusted |
| `mypy … import-not-found` in fresh-clone | new module not `git add`ed | stage new files — `verify-fresh-clone.sh` only copies tracked files |
| coverage below 80% | new code paths untested | add tests; gate is `--cov-fail-under=80` in `pytest.ini` |
| a new warning fails pytest | `filterwarnings = error` caught it | fix the warning in app code; only documented upstream warnings are ignored |

## 6. The suppressed upstream warning (intentional)

`pytest.ini` runs with `filterwarnings = error` so our **own** code can never ship a
silent deprecation. There is exactly one scoped `ignore`:

```
ignore:Using `httpx` with `starlette.testclient` is deprecated
```

`starlette.testclient` now prefers a package named `httpx2` and warns when standard
`httpx` is used. We **do not** adopt `httpx2`: it is unvetted, typosquat-shaped, and
absent from every lockfile in this repo — pulling it in would be a supply-chain risk.
The warning originates entirely in the upstream library, not in `app/`, so ignoring
that one message (and nothing else) is the correct trade-off. Revisit if Starlette
makes `httpx2` a hard requirement or `httpx` support is removed.

## 7. CI

`.github/workflows/d5-reproducible-env.yml` runs on changes to this folder or the
root toolchain files:
* **toolchain-sync** — `check-toolchain-sync.sh` (fails on root/D5 pin drift).
* **bootstrap-linux** — installs mise on `ubuntu-latest`, runs `make`, then
  `verify-fresh-clone.sh` (true clean-machine proof).
* **bootstrap-macos** — same, opt-in via `workflow_dispatch` (`run_macos: true`).

Actions are SHA-pinned; `permissions: contents: read`. mise is installed via its
official script (no third-party action to pin/trust).
