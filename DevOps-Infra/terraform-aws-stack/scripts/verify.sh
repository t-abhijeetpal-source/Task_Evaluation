#!/usr/bin/env bash
# Offline verification for the D1 terraform-aws-stack:
#   terraform fmt -check -> init -backend=false -> validate -> plan (offline)
#   + Lambda handler unit tests (coverage-gated).
# Requires no AWS account. tflint/checkov run only if installed (parity with CI).
set -euo pipefail

cd "$(dirname "$0")/.."
ROOT="$(pwd)"
echo "== D1 verify (dir: $ROOT) =="

if ! command -v terraform >/dev/null 2>&1; then
  echo "ERROR: terraform not found on PATH (need >= 1.6)." >&2
  exit 1
fi

echo "-- terraform fmt -check --"
terraform fmt -check -recursive

echo "-- terraform init -backend=false --"
terraform init -backend=false -input=false >/dev/null

echo "-- terraform validate --"
terraform validate

echo "-- terraform plan (offline) --"
terraform plan -input=false -no-color | tee /tmp/d1-plan.txt | grep -E "^Plan:"

echo "-- tflint (if installed) --"
if command -v tflint >/dev/null 2>&1; then
  tflint --init >/dev/null && tflint -f compact && echo "tflint: clean"
else
  echo "tflint: not installed (skipped; runs in CI)"
fi

echo "-- checkov (if installed) --"
if command -v checkov >/dev/null 2>&1; then
  checkov -d . --config-file .checkov.yaml --compact | grep -E "Passed|Failed|Skipped checks" || true
else
  echo "checkov: not installed (skipped; runs in CI)"
fi

echo "-- handler unit tests --"
PY="${PYTHON:-python3}"
if "$PY" -c "import pytest" >/dev/null 2>&1; then
  "$PY" -m pytest
else
  echo "creating throwaway venv for tests..."
  VENV="$(mktemp -d)/venv"
  "$PY" -m venv "$VENV"
  "$VENV/bin/pip" install -q -r requirements-dev.txt
  "$VENV/bin/python" -m pytest
fi

echo "== ✅ D1 TERRAFORM-AWS-STACK VERIFIED =="
