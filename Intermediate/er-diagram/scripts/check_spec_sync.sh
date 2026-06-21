#!/usr/bin/env bash
# check_spec_sync.sh — single-source-of-truth guard for the I1 ER-diagram agent spec.
#
# Canonical spec:  skills/tasks-er-diagram/SKILL.md
# Wrapper:         Intermediate/er-diagram/I1_agent.md (thin pointer + synced body)
#
# Both files share an identical body from the `## Role` heading to EOF. This script
# compares those bodies and fails (exit 1) if they drift, so CI catches an edit made
# to one copy but not the other. Each file's own preamble (skill frontmatter / agent
# wrapper note) lives ABOVE `## Role` and is intentionally ignored.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
I1_DIR="$(dirname "$SCRIPT_DIR")"                 # Intermediate/er-diagram
REPO_ROOT="$(cd "$I1_DIR/../.." && pwd)"          # repo root (Tasks/)

AGENT="$I1_DIR/I1_agent.md"
SKILL="$REPO_ROOT/skills/tasks-er-diagram/SKILL.md"
ANCHOR='^## Role'

for f in "$AGENT" "$SKILL"; do
  if [[ ! -f "$f" ]]; then
    echo "check_spec_sync: missing file: $f" >&2
    exit 1
  fi
done

tmp_agent="$(mktemp)"; tmp_skill="$(mktemp)"
trap 'rm -f "$tmp_agent" "$tmp_skill"' EXIT

# Extract the canonical body: everything from the `## Role` anchor to EOF.
extract_body() { awk -v a="$ANCHOR" '$0 ~ a {p=1} p' "$1"; }

extract_body "$AGENT" > "$tmp_agent"
extract_body "$SKILL" > "$tmp_skill"

if [[ ! -s "$tmp_agent" || ! -s "$tmp_skill" ]]; then
  echo "❌ check_spec_sync: '## Role' anchor not found in one of the spec files." >&2
  exit 1
fi

if diff -u "$tmp_skill" "$tmp_agent" > /tmp/i1-spec-sync.diff 2>&1; then
  echo "✅ check_spec_sync: I1_agent.md body is in sync with skills/tasks-er-diagram/SKILL.md"
  exit 0
else
  echo "❌ check_spec_sync: I1_agent.md has DRIFTED from skills/tasks-er-diagram/SKILL.md (canonical)." >&2
  echo "   Re-sync the body (from '## Role' to EOF) of Intermediate/er-diagram/I1_agent.md" >&2
  echo "   with skills/tasks-er-diagram/SKILL.md." >&2
  echo "   --- diff (canonical skill vs agent body) ---" >&2
  cat /tmp/i1-spec-sync.diff >&2
  exit 1
fi
