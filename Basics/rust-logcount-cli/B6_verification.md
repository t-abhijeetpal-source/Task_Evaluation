# B6 — Verification Report: logcount Rust CLI

**Project:** `Basics/rust-logcount-cli` (`logcount` crate)  
**Agent run date:** 2026-06-17  
**Toolchain:** rustc 1.96.0 / cargo 1.96.0 (Homebrew)

---

## Summary

| Check | Result |
|-------|--------|
| `cargo test` | **PASS** — 7 integration tests, 0 failures |
| `cargo run -- sample.log` | **PASS** — `INFO: 2 / WARN: 1 / ERROR: 1`, exit `0` |
| `cargo run -- missing.log` | **PASS** — friendly error, exit `1` |
| `cargo run` (no args) | **PASS** — usage message, exit `2` |
| `cargo build --release` | **PASS** — release binary runs correctly |

**Verdict:** All commands from the README succeed. The CLI meets its stated requirements.

---

## Toolchain

```bash
$ rustc --version
rustc 1.96.0 (ac68faa20 2026-05-25) (Homebrew)

$ cargo --version
cargo 1.96.0 (30a34c682 2026-05-25) (Homebrew)
```

---

## Test Execution

**Command:**

```bash
cd Basics/rust-logcount-cli
cargo test
```

**Output (observed):**

```text
    Finished `test` profile [unoptimized + debuginfo] target(s) in 0.06s
     Running unittests src/lib.rs (target/debug/deps/logcount-bd48c2c1c78e031e)

running 0 tests

test result: ok. 0 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 0.00s

     Running unittests src/main.rs (target/debug/deps/logcount-a734813237d8c944)

running 0 tests

test result: ok. 0 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 0.00s

     Running tests/cli.rs (target/debug/deps/cli-f8ec1f9e90532d66)

running 7 tests
test counts_error_lines ... ok
test counts_info_lines ... ok
test display_format_is_correct ... ok
test full_counts_match_expected ... ok
test missing_file_returns_not_found_error ... ok
test ignores_unrecognised_and_blank_lines ... ok
test counts_warn_lines ... ok

test result: ok. 7 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 0.00s
```

| Test | Requirement |
|------|-------------|
| `counts_info_lines` | INFO line counting |
| `counts_warn_lines` | WARN line counting |
| `counts_error_lines` | ERROR line counting |
| `missing_file_returns_not_found_error` | Missing file → `NotFound` error (no panic) |
| `full_counts_match_expected` | Combined counts on sample input |
| `ignores_unrecognised_and_blank_lines` | DEBUG/blank lines ignored |
| `display_format_is_correct` | Output format `INFO: n\nWARN: n\nERROR: n` |

---

## CLI Execution

### Happy path — `sample.log`

```bash
cargo run -- sample.log
```

```text
INFO: 2
WARN: 1
ERROR: 1
```

Exit code: **0**

### Missing file

```bash
cargo run -- missing.log
```

```text
Error:
File not found: missing.log
```

Exit code: **1**

### No arguments

```bash
cargo run
```

```text
Error:
Usage: target/debug/logcount <log-file>
```

Exit code: **2**

### Release build

```bash
cargo build --release
./target/release/logcount sample.log
```

```text
   Compiling logcount v1.0.0 (/Users/abhijeetpal/Desktop/workspace/Tasks/Basics/rust-logcount-cli)
    Finished `release` profile [optimized] target(s) in 4.51s
INFO: 2
WARN: 1
ERROR: 1
```

---

## Architecture (verified by inspection)

```text
CLI            src/main.rs      argv, print counts, map errors → exit codes
  │
  ▼
Parsing        src/parser.rs    count_levels(&str) / count_file(&Path)
  │
  ▼
Business logic src/models.rs    LogLevel, LogCounts, Display

Facade:        src/lib.rs       re-exports for integration tests in tests/cli.rs
```

Layering matches README: CLI → Parsing → Business logic. No `unwrap` on user-controlled file paths in `main.rs`.

---

## Provenance

| Item | Status |
|------|--------|
| Source, tests, README | Present in repo |
| `cargo test` (7 passed) | **VERIFIED** — command executed 2026-06-17 |
| `cargo run` (sample / missing / no-args) | **VERIFIED** — output and exit codes captured |
| `cargo build --release` | **VERIFIED** — release binary runs on `sample.log` |

All output above is **observed execution**, not prediction.
