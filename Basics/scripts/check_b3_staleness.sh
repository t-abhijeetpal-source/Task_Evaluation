#!/usr/bin/env bash
# B3 test-discovery staleness guard — checks committed deliverables for anchors that age well.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ARTIFACT="$ROOT/test-discovery/B3_test_discovery_paytmmoney.md"

fail() { echo "B3 FAIL: $1"; exit 1; }
pass() { echo "B3 PASS: $1"; }

[[ -f "$ARTIFACT" ]] || fail "missing artifact: $ARTIFACT"

for section in \
  "Agent Findings" \
  "Verified Findings" \
  "Canonical CI test command" \
  "Reproduce this update"; do
  grep -qi "$section" "$ARTIFACT" || fail "missing section/anchor: $section"
done
pass "required sections present"

# Must document the paytmmoney → android-monorepo consolidation (staleness lesson)
grep -qi "android-monorepo" "$ARTIFACT" || fail "missing re-anchored repo name (android-monorepo)"
grep -Eiq 'commit|HEAD|[0-9a-f]{7,}' "$ARTIFACT" || fail "missing commit/HEAD anchor"

# Canonical test command documented
grep -qE '(gradle|pytest|npm test|make test)' "$ARTIFACT" || fail "missing canonical test command"

pass "B3 staleness anchors present"
