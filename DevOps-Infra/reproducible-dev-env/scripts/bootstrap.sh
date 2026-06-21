#!/usr/bin/env bash
#
# D5 one-command bootstrap. From a fresh clone this installs the pinned toolchain,
# verifies Python AND Node resolve to the pinned versions, creates an isolated
# virtualenv, installs dependencies, and runs the quality gates + tests.
#
# Idempotent and incremental: the venv is created only if missing, and pip runs
# only when requirements change (content-hashed). Re-running is cheap — see
# `make verify` for a tests-only path that skips install entirely.
set -euo pipefail
cd "$(dirname "$0")/.."

if ! command -v mise >/dev/null 2>&1; then
  echo "ERROR: mise is not installed. Install it first:  brew install mise" >&2
  echo "       (or: curl https://mise.run | sh)" >&2
  exit 1
fi

# Read a pinned tool version from mise.toml (ignores comments).
mise_pin() {  # <tool>
  grep -E "^[[:space:]]*$1[[:space:]]*=" mise.toml | head -n1 | sed -E 's/.*"([^"]+)".*/\1/'
}

# Portable sha256 of stdin (Linux: sha256sum, macOS: shasum).
sha256() {
  if command -v sha256sum >/dev/null 2>&1; then sha256sum | awk '{print $1}';
  else shasum -a 256 | awk '{print $1}'; fi
}

echo "==> [1/6] Trust + install pinned toolchain from mise.toml"
mise trust --yes >/dev/null 2>&1 || true
mise install              # installs python + node at the exact pinned versions

PY="$(mise which python)"
NODE="$(mise which node)"
echo "    using Python: ${PY}"
echo "    using Node:   ${NODE}"

echo "==> [2/6] Verify runtimes match the pins"
want_node_mm="$(mise_pin node | cut -d. -f1-2)"     # e.g. 22.12
node_ver="$("${NODE}" --version)"                   # e.g. v22.12.0
echo "    python: $("${PY}" --version)   node: ${node_ver}  (pinned v${want_node_mm}.x)"
if [[ "${node_ver}" != v"${want_node_mm}".* ]]; then
  echo "ERROR: node ${node_ver} does not match pinned v${want_node_mm}.x" >&2
  exit 1
fi

echo "==> [3/6] Create virtualenv (.venv) with the pinned Python (only if missing)"
if [[ -x .venv/bin/python ]]; then
  echo "    .venv already present — reusing"
else
  "${PY}" -m venv .venv
  echo "    created .venv"
fi
PIP=(./.venv/bin/python -m pip)

echo "==> [4/6] Install dependencies (skip if requirements unchanged)"
req_hash="$(cat requirements.txt requirements-dev.txt | sha256)"
hash_file=".venv/.reqs-sha256"
if [[ -f "${hash_file}" && "$(cat "${hash_file}")" == "${req_hash}" ]]; then
  echo "    dependencies unchanged — skipping pip install"
else
  "${PIP[@]}" install --quiet --upgrade pip
  "${PIP[@]}" install --quiet -r requirements-dev.txt
  echo "${req_hash}" >"${hash_file}"
  echo "    dependencies installed"
fi

echo "==> [5/6] Quality gates (ruff + mypy)"
./.venv/bin/ruff check .
./.venv/bin/ruff format --check .
./.venv/bin/mypy app

echo "==> [6/6] Run tests (with coverage gate)"
./.venv/bin/python -m pytest -q

echo ""
echo "==> Bootstrap complete. Activate with:  source .venv/bin/activate"
echo "==> Run the service with:               make run"
