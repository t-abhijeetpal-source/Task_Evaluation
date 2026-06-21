#!/usr/bin/env bash
# B2 route map gate — validates committed YAML and optionally diffs against a live repo.
#
# Usage:
#   bash Basics/scripts/b2-verify.sh                    # offline: YAML + script hygiene
#   REPO_ROOT=/path/to/android-monorepo bash ...        # also diff live extraction
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
EXTRACT="$ROOT/route-api-mapper/extract_routes.sh"
YAML="$ROOT/route-api-mapper/B2_routes.yaml"

fail() { echo "B2 FAIL: $1"; exit 1; }
pass() { echo "B2 PASS: $1"; }

[[ -x "$EXTRACT" ]] || fail "missing or non-executable: $EXTRACT"
[[ -f "$YAML" ]] || fail "missing committed artifact: $YAML"

# Script must not ship hardcoded developer home paths
if grep -qE '/Users/[^/]+/' "$EXTRACT"; then
  fail "extract_routes.sh contains hardcoded /Users/ path — use REPO_ROOT or argument"
fi
pass "extract_routes.sh is portable"

grep -q 'recovered_path_constants:' "$YAML" || fail "B2_routes.yaml missing meta.recovered_path_constants"
grep -q '^paths:' "$YAML" || fail "B2_routes.yaml missing paths section"
pass "committed B2_routes.yaml structure OK"

if [[ -n "${REPO_ROOT:-}" ]]; then
  [[ -d "$REPO_ROOT" ]] || fail "REPO_ROOT is not a directory: $REPO_ROOT"
  tmp="$(mktemp)"
  trap 'rm -f "$tmp"' EXIT
  bash "$EXTRACT" "$REPO_ROOT" > "$tmp"
  if diff -u "$YAML" "$tmp"; then
    pass "live extraction matches committed B2_routes.yaml"
  else
    fail "B2_routes.yaml drift — re-run: REPO_ROOT=$REPO_ROOT $EXTRACT > $YAML"
  fi
else
  echo "B2 SKIP: REPO_ROOT not set — offline validation only (committed YAML present)"
fi

pass "B2 route map gate complete"
