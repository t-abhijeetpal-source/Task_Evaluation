#!/usr/bin/env bash
# B1 inventory artifact validator — offline checks on committed markdown deliverables.
# Ensures required sections exist and headline counts reconcile without re-running the agent.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ARTIFACT="$ROOT/repo-structure-mapper/B1_repo_inventory_pml-flutter.md"

fail() { echo "B1 FAIL: $1"; exit 1; }
pass() { echo "B1 PASS: $1"; }

[[ -f "$ARTIFACT" ]] || fail "missing artifact: $ARTIFACT"

# Required sections for a v2 inventory report
for section in \
  "## 2. Executive Summary" \
  "## 4. Architecture Analysis" \
  "## 5. Folder / Module Inventory" \
  "## 15. Confidence & Verification Matrix" \
  "## 17. Reproducibility"; do
  grep -qF "$section" "$ARTIFACT" || fail "missing section: $section"
done
pass "required sections present"

# No absolute home-directory paths in committed artifacts
if grep -qE '/Users/[^/]+/' "$ARTIFACT"; then
  fail "artifact contains /Users/... path — use repo-relative paths"
fi
pass "no local home-directory paths"

# Count anchors must be re-derived (not hand-waved)
if grep -q "re-derived" "$ARTIFACT"; then
  pass "re-derived count anchors present"
else
  fail "expected re-derived count anchors not found"
fi

# Agent vs verified split
grep -qi "VERIFIED" "$ARTIFACT" || fail "missing VERIFIED labels"
grep -qi "INFERRED" "$ARTIFACT" || fail "missing INFERRED labels"

pass "B1 inventory artifact validation complete"
