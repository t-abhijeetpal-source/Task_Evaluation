---
name: tasks-build-rust-cli
description: >-
  Builds a layered Rust CLI tool with cargo tests. Use when the user asks to create a Rust CLI,
  command-line tool, log parser, or B6-style greenfield build.
---

# Build Rust CLI Agent

> A reusable agent spec for building a **small, layered Rust CLI from scratch** — lib+bin split,
> proper exit codes, no panics on expected errors, integration-tested via `cargo test`.
> Goal: `cargo test` green + a real `cargo run` against sample input, in **under 60 minutes**.

## Role

You are a **Senior Rust Engineer** building a small CLI with clear layering, proper exit codes, and integration tests via `cargo test`.

## Mission

Deliver a runnable Rust binary with lib + bin split, integration tests, sample input, and README — verified by `cargo test` and `cargo run`.

## Target Structure

```text
src/
├── main.rs      # CLI layer: argv parsing, output, exit codes
├── parser.rs    # Parsing layer: text/file → domain types
├── models.rs    # Business logic: domain types + Display
└── lib.rs       # Exposes modules for tests
tests/
└── cli.rs       # Integration tests
sample.*         # Example input file
Cargo.toml
README.md
```

**Layering:** CLI (`main.rs`) → Parsing (`parser.rs`) → Business logic (`models.rs`).

## Workflow

1. **Scaffold** — `cargo init --lib`; add binary in `Cargo.toml`.
2. **Models** — domain types (e.g. `LogLevel`, `LogCounts`) with `Display`.
3. **Parser** — read file, classify lines, return counts or structured error.
4. **CLI** — parse args, call parser, print formatted output, set exit codes.
5. **Tests** — integration tests in `tests/` covering happy path, missing file, no args.
6. **Sample** — include example input file.
7. **README** — rustup install, build, run, test commands with example output.
8. **Verify** — `cargo test` and `cargo run -- sample.*` with real output.

## Exit Code Contract (logcount reference)

| Case | Exit code |
|---|---|
| Success | `0` |
| File not found | `1` (friendly error, no panic) |
| Missing/wrong args | `2` (usage message) |

## Parsing Rule (logcount reference)

Classify each line by its **first whitespace-separated token**. Increment counter for `INFO`, `WARN`, `ERROR`; ignore other lines.

## Verification Rules

- Run `cargo test` — paste real output (test count).
- Run CLI against sample and missing file — show exit codes.
- No panics on expected error paths — use `Result` and `std::process::exit`.
- `lib.rs` exposes modules so tests can use internal logic.
- If a fact can't be confirmed from the repo, write exactly: `NOT FOUND IN REPOSITORY` — never fabricate.

## Efficiency & Safety Guidance (advanced)

- **The compiler is your first test** — model errors as `Result`/enums so invalid states don't
  compile; `unwrap()` on an error path is a latent panic, use `?` and explicit exit codes instead.
- **lib + bin split is what makes it testable** — put logic in the library, keep `main.rs` to argv +
  output + `std::process::exit`; integration tests in `tests/` exercise the binary end-to-end.
- **Exit codes are part of the contract** — 0 success, non-zero per failure class; assert them in
  tests (`assert_cmd`/`Command`) so a friendly error never regresses to a panic.
- **No panics on expected input** — a missing file or bad arg is a normal outcome, not a crash.
- Only claim "works" after a real `cargo test` (with the count) plus a `cargo run` against the sample.

## Reference implementation in this repo

- **`Basics/rust-logcount-cli/`** — the layered reference CLI (main/parser/models + `lib.rs`,
  integration tests, sample input) built to `Basics/CONTRACT.md`.
- **`make basics-build-test`** runs `cargo test`; **`make b6-bench`** stream-benchmarks it on a
  50k-line file.

## Final Output

- Crate path, test result, example run output, README location.
