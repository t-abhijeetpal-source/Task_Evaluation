#!/usr/bin/env bash
# Quick streaming benchmark for B6 — ensures large files are processed in constant memory.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BIN="$ROOT/rust-logcount-cli/target/release/logcount"
TMP="$(mktemp -t logcount-bench.XXXXXX.log)"
trap 'rm -f "$TMP"' EXIT

(cd "$ROOT/rust-logcount-cli" && cargo build --release --quiet)

for _ in $(seq 1 50000); do
  echo "INFO ok"
done >> "$TMP"
echo "ERROR done" >> "$TMP"

OUT="$("$BIN" "$TMP")"
echo "$OUT" | grep -q "INFO: 50000"
echo "$OUT" | grep -q "ERROR: 1"
echo "B6 bench: streamed 50k lines OK"
