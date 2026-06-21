#!/usr/bin/env bash
#
# Simulate a fresh clone and prove the one-command bootstrap works end to end.
#
# Copies only git-tracked files (no .venv, no caches) into a throwaway temp dir,
# runs `make` there, and asserts: exit 0 + the pytest "N passed" summary line.
# This is the honest reproducibility proof — it cannot accidentally reuse this
# checkout's virtualenv or installed deps. Wired into CI and `make verify-fresh`.
set -euo pipefail

D5_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "${D5_DIR}"

work="$(mktemp -d "${TMPDIR:-/tmp}/d5-freshclone.XXXXXX")"
cleanup() { rm -rf "${work}"; }
trap cleanup EXIT

echo "== fresh-clone simulation =="
echo "source: ${D5_DIR}"
echo "temp:   ${work}"

# Mirror only git-tracked files into the temp dir (relative paths, NUL-safe).
git ls-files -z | rsync -a --files-from=- --from0 ./ "${work}/"

log="${work}/.make.log"
echo "== running 'make' in the simulated clone =="
set +e
( cd "${work}" && make ) 2>&1 | tee "${log}"
status="${PIPESTATUS[0]}"
set -e

if [[ "${status}" -ne 0 ]]; then
  echo "FRESH-CLONE VERIFY FAILED: 'make' exited ${status}" >&2
  exit 1
fi

# Assert the pytest summary is present (e.g. "12 passed" / "12 passed, 1 skipped").
if ! grep -Eq '[0-9]+ passed' "${log}"; then
  echo "FRESH-CLONE VERIFY FAILED: no pytest 'N passed' summary in output" >&2
  exit 1
fi

passed="$(grep -Eo '[0-9]+ passed' "${log}" | tail -n1)"
echo "✅ fresh-clone bootstrap succeeded — ${passed}"
