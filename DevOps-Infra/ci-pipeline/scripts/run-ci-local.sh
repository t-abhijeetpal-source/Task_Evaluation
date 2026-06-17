#!/usr/bin/env bash
# Local execution of the EXACT pipeline stages defined in .github/workflows/ci.yml,
# mirroring deterministic install + fail-fast ordering. Captures per-stage timing + exit codes.
set -uo pipefail
cd "$(dirname "$0")/.."
SHA="$(git rev-parse --short HEAD 2>/dev/null || echo local)"

run_stage() {
  local name="$1"; shift
  echo "===== [$(date '+%H:%M:%S')] STAGE: ${name} ====="
  local t0=$SECONDS
  "$@"
  local rc=$?
  echo "----- stage '${name}' exit=${rc} duration=$((SECONDS - t0))s -----"
  if [ "$rc" -ne 0 ]; then
    echo "❌ PIPELINE FAILED at stage: ${name} (exit ${rc}) — downstream stages skipped (fail-fast)"
    exit "$rc"
  fi
  echo ""
}

# Deterministic dependency install from the lockfile (mirrors CI).
[ -d .venv ] || python3 -m venv .venv
# shellcheck disable=SC1091
. .venv/bin/activate
pip install -q -r requirements-dev.txt

run_stage "1-lint"        bash -c "ruff check . && ruff format --check ."
run_stage "2-unit"        python -m pytest tests/test_unit.py -q
run_stage "3-integration" python -m pytest tests/test_integration.py -q
run_stage "4-build"       bash -c "python -m compileall -q app && printf '{\"commit\":\"%s\",\"built_at\":\"%s\"}\n' \"$SHA\" \"$(date -u +%FT%TZ)\" > build-info.json && zip -qr \"d3-app-${SHA}.zip\" app requirements.txt build-info.json && echo \"artifact: d3-app-${SHA}.zip\""
run_stage "5-container"   docker build -q -t "d3-sample:${SHA}" -t d3-sample:latest .

echo "✅ ALL STAGES PASSED (commit ${SHA})"
