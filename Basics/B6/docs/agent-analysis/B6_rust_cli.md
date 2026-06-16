# B6 — Rust Log-Count CLI

> Build report for the `logcount` CLI.
> Status: **BUILT, TESTED, AND VERIFIED RUNNING.**
> Last verified: **2026-06-17** — Rust 1.96.0 (Homebrew); `cargo test` and `cargo run`
> executed with real output captured below. See also [`B6_verification.md`](../../B6_verification.md).

---

## Architecture

Three separated layers + a thin lib facade:

```text
argv
  │
  ▼
CLI            src/main.rs      parse args, print counts, map errors -> exit codes
  │
  ▼
Parsing        src/parser.rs    count_levels(&str) / count_file(&Path) -> io::Result
  │
  ▼
Business logic src/models.rs    LogLevel classification, LogCounts, Display formatting

Facade:        src/lib.rs       re-exports models + parser for the integration tests
```

> **Deviation from the suggested tree:** a `src/lib.rs` was added. Rust integration tests in
> `tests/` can only call into a *library* crate, so the logic is exposed as `lib.rs` and `main.rs`
> is a thin binary over it. This is the idiomatic Rust layout for a testable CLI.

---

## Parsing Logic

- Input is split into lines (`str::lines`).
- Each line is classified by its **first whitespace token** via `LogLevel::from_line`:
  - `"INFO"` → `Info`, `"WARN"` → `Warn`, `"ERROR"` → `Error`, anything else → `None` (ignored).
- `LogCounts::record` increments the matching counter.
- `count_levels(&str)` is pure (no I/O) → trivially testable.
- `count_file(&Path)` wraps `fs::read_to_string` and returns `io::Result<LogCounts>`.

Output formatting lives in `impl Display for LogCounts`:
```text
INFO: <n>
WARN: <n>
ERROR: <n>
```

---

## Error Handling

- `count_file` **propagates** `io::Error` rather than panicking.
- `main` matches on the error:
  - `ErrorKind::NotFound` → prints `Error:\nFile not found: <path>`, exits `1`.
  - any other I/O error → prints `Error:\nCould not read <path>: <err>`, exits `1`.
  - no path argument → usage message, exits `2`.
- No `unwrap`/`expect` on user-controlled input paths → **no panic** on a missing file.

---

## Test Results

**Command:** `cargo test` — **7 passed, 0 failed.**

```text
    Finished `test` profile [unoptimized + debuginfo] target(s) in 0.06s
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

| Test | Requirement covered |
|---|---|
| `counts_info_lines` | Test 1 — INFO counting |
| `counts_warn_lines` | Test 2 — WARN counting |
| `counts_error_lines` | Test 3 — ERROR counting |
| `missing_file_returns_not_found_error` | Test 4 — missing file handling (asserts `NotFound`) |
| `full_counts_match_expected` | combined `INFO:2 WARN:1 ERROR:1` |
| `ignores_unrecognised_and_blank_lines` | DEBUG/blank lines not counted |
| `display_format_is_correct` | output formatting |

---

## Execution Results

**Observed** (real runs):

```bash
$ cargo run -- sample.log
INFO: 2
WARN: 1
ERROR: 1
$ echo $?
0

$ cargo run -- missing.log
Error:
File not found: missing.log
$ echo $?
1

$ cargo run            # no args
Error:
Usage: target/debug/logcount <log-file>
$ echo $?
2
```

---

## Known Limitations

- **Level detection is first-token, case-sensitive** — `info` (lowercase) or levels embedded
  mid-line (`2026-01-01 INFO ...`) are not counted. Easy to extend if needed.
- **Whole-file read** (`read_to_string`) — loads the file into memory; for multi-GB logs a
  streaming `BufReader` line iterator would be better.
- **Only INFO/WARN/ERROR** — DEBUG/TRACE/FATAL are ignored by design.
- **No flags** (e.g. `--json`, multiple files) — single positional path argument only.

---

## Provenance

| Item | Status |
|---|---|
| Source (`src/`), tests, README, this doc | **AGENT GENERATED** |
| `cargo test` output (7 passed) | **VERIFIED** — 2026-06-17, Rust 1.96.0 (Homebrew) |
| `cargo run` output (sample / missing / no-args, exit 0/1/2) | **VERIFIED** — 2026-06-17, commands executed |
| `cargo build --release` + release binary run | **VERIFIED** — 2026-06-17 |

All output above is **observed execution**, not prediction.
