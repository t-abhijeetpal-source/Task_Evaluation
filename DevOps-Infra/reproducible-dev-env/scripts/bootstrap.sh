#!/usr/bin/env bash
#
# D5 one-command bootstrap. From a fresh clone, this installs the pinned
# toolchain, creates an isolated virtualenv, installs dependencies, and runs
# the test suite. Idempotent: safe to re-run.
set -euo pipefail
cd "$(dirname "$0")/.."

if ! command -v mise >/dev/null 2>&1; then
  echo "ERROR: mise is not installed. Install it first:  brew install mise" >&2
  echo "       (or: curl https://mise.run | sh)" >&2
  exit 1
fi

echo "==> [1/4] Trust + install pinned toolchain from mise.toml"
mise trust --yes >/dev/null 2>&1 || true
mise install              # installs python + node at the exact pinned versions

PY="$(mise which python)"
echo "    using Python: ${PY}"
echo "    using Node:   $(mise which node)"

echo "==> [2/4] Create virtualenv (.venv) with the pinned Python"
"${PY}" -m venv .venv

echo "==> [3/4] Install dependencies (requirements-dev.txt)"
./.venv/bin/python -m pip install --quiet --upgrade pip
./.venv/bin/python -m pip install --quiet -r requirements-dev.txt

echo "==> [4/4] Run tests"
./.venv/bin/python -m pytest -q

echo ""
echo "==> Bootstrap complete. Activate with:  source .venv/bin/activate"
echo "==> Run the service with:               make run"
