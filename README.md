# logcount (B6 — Rust CLI Greenfield)

A small command-line tool that reads a log file and counts how many lines are
`INFO`, `WARN`, and `ERROR`. Built in Rust with `cargo`.

> ✅ **Verification status:** built and verified with Rust 1.96.0 (installed via Homebrew).
> `cargo test` → **7 passed**; `cargo run -- sample.log` → `INFO: 2 / WARN: 1 / ERROR: 1`;
> missing file → exit code `1`.

---

## Project Structure

```text
B6/
├── src/
│   ├── main.rs      # CLI layer: argv parsing, output, exit codes
│   ├── parser.rs    # Parsing layer: text/file -> LogCounts
│   ├── models.rs    # Business logic: LogLevel + LogCounts (+ Display)
│   └── lib.rs       # Exposes modules so tests/ can use them
├── tests/
│   └── cli.rs       # Integration tests (cargo test)
├── sample.log       # Example input
├── Cargo.toml
└── README.md
```

Layering: **CLI (`main.rs`) → Parsing (`parser.rs`) → Business logic (`models.rs`).**

---

## Installation

Requires the Rust toolchain. Install via [rustup](https://rustup.rs):

```bash
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
# then restart your shell, or: source "$HOME/.cargo/env"
```

## Build

```bash
cd B6
cargo build --release      # binary at target/release/logcount
```

## Run

```bash
cargo run -- sample.log
# or, after build:
./target/release/logcount sample.log
```

## Test

```bash
cargo test
```

---

## Example Input (`sample.log`)

```text
INFO Application started
WARN Cache miss
INFO Request received
ERROR Database unavailable
```

## Example Output

```text
INFO: 2
WARN: 1
ERROR: 1
```

### Missing file

```bash
cargo run -- missing.log
```

```text
Error:
File not found: missing.log
```

Exits with a **non-zero** status code (`1`) and does **not** panic.

---

## How counting works

Each line is classified by its **first whitespace-separated token**. If that token is
`INFO`, `WARN`, or `ERROR`, the corresponding counter increments; any other line
(blank lines, `DEBUG`, free text) is ignored.
