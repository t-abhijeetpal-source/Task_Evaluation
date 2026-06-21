#!/usr/bin/env bash
#
# Fail if the Python/Node pins drift between the repo-root toolchain files and
# this D5 folder. D5 declares no Rust, so Rust is intentionally root-only and not
# compared here. Runs locally (`make check-sync`) and in CI.
set -euo pipefail

D5_DIR="$(cd "$(dirname "$0")/.." && pwd)"
ROOT_DIR="$(cd "${D5_DIR}/../.." && pwd)"

fail=0
note() { printf '  %s\n' "$1"; }

# Extract `python = "X"` / `node = "X"` from a mise.toml (ignores commented lines).
mise_pin() {  # <file> <tool>
  grep -E "^[[:space:]]*$2[[:space:]]*=" "$1" 2>/dev/null \
    | head -n1 | sed -E 's/.*"([^"]+)".*/\1/'
}

# Extract a pin from a .tool-versions file (asdf uses `nodejs`, not `node`).
tv_pin() {  # <file> <key>
  grep -E "^$2[[:space:]]+" "$1" 2>/dev/null | head -n1 | awk '{print $2}'
}

# Canonical source of truth: the D5 mise.toml.
want_py="$(mise_pin "${D5_DIR}/mise.toml" python)"
want_node="$(mise_pin "${D5_DIR}/mise.toml" node)"

if [[ -z "${want_py}" || -z "${want_node}" ]]; then
  echo "ERROR: could not read python/node pins from ${D5_DIR}/mise.toml" >&2
  exit 2
fi

echo "== toolchain sync check =="
echo "canonical (D5 mise.toml): python=${want_py}  node=${want_node}"

check() {  # <label> <actual-python> <actual-node>
  local label="$1" py="$2" node="$3"
  if [[ "${py}" != "${want_py}" ]]; then
    note "✗ ${label}: python=${py:-<missing>} (expected ${want_py})"; fail=1
  fi
  if [[ "${node}" != "${want_node}" ]]; then
    note "✗ ${label}: node=${node:-<missing>} (expected ${want_node})"; fail=1
  fi
  if [[ "${py}" == "${want_py}" && "${node}" == "${want_node}" ]]; then
    note "✓ ${label}"
  fi
}

check "root mise.toml"      "$(mise_pin "${ROOT_DIR}/mise.toml" python)"   "$(mise_pin "${ROOT_DIR}/mise.toml" node)"
check "root .tool-versions" "$(tv_pin "${ROOT_DIR}/.tool-versions" python)" "$(tv_pin "${ROOT_DIR}/.tool-versions" nodejs)"
check "D5 .tool-versions"   "$(tv_pin "${D5_DIR}/.tool-versions" python)"  "$(tv_pin "${D5_DIR}/.tool-versions" nodejs)"

# D5 .python-version pins python only.
d5_pyver="$(head -n1 "${D5_DIR}/.python-version" 2>/dev/null | tr -d '[:space:]')"
if [[ "${d5_pyver}" != "${want_py}" ]]; then
  note "✗ D5 .python-version: ${d5_pyver:-<missing>} (expected ${want_py})"; fail=1
else
  note "✓ D5 .python-version"
fi

if [[ "${fail}" -ne 0 ]]; then
  echo "TOOLCHAIN SYNC FAILED — bump every file above together." >&2
  exit 1
fi
echo "✅ toolchain pins are in sync"
