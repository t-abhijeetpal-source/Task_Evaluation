//! `fraud-engine` binary.
//!
//! Reads ONE transaction JSON from stdin, writes ONE score-result JSON to
//! stdout and exits 0 on success. On malformed/invalid input it writes an
//! error JSON to stderr and exits 1. It never panics on input.

use std::io::{self, Read, Write};
use std::process::ExitCode;

use fraud_engine::{score, Transaction};

fn main() -> ExitCode {
    let mut input = String::new();
    if let Err(e) = io::stdin().read_to_string(&mut input) {
        let _ = report_error(&format!("failed to read stdin: {}", e));
        return ExitCode::FAILURE;
    }

    let txn: Transaction = match serde_json::from_str(&input) {
        Ok(t) => t,
        Err(e) => {
            let _ = report_error(&format!("invalid transaction JSON: {}", e));
            return ExitCode::FAILURE;
        }
    };

    let result = score(&txn);

    let out = match serde_json::to_string(&result) {
        Ok(s) => s,
        Err(e) => {
            let _ = report_error(&format!("failed to serialize result: {}", e));
            return ExitCode::FAILURE;
        }
    };

    let stdout = io::stdout();
    let mut handle = stdout.lock();
    if writeln!(handle, "{}", out).is_err() {
        return ExitCode::FAILURE;
    }

    ExitCode::SUCCESS
}

/// Write a structured error JSON to stderr.
fn report_error(message: &str) -> io::Result<()> {
    let payload = serde_json::json!({ "error": message });
    let stderr = io::stderr();
    let mut handle = stderr.lock();
    writeln!(handle, "{}", payload)
}
