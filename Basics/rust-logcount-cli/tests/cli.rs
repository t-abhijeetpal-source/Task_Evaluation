//! Integration tests for the log-count tool.
//!
//! Exercises the public library API (parsing + counting + file errors) and
//! the compiled binary end-to-end (stdin, --json, flags, exit codes).

use std::io::{ErrorKind, Write};
use std::path::Path;
use std::process::{Command, Stdio};

use logcount::models::LogCounts;
use logcount::parser::{count_file, count_levels};

const SAMPLE: &str = "\
INFO Application started
WARN Cache miss
INFO Request received
ERROR Database unavailable
";

// --- Test 1: INFO counting -------------------------------------------------
#[test]
fn counts_info_lines() {
    let counts = count_levels(SAMPLE);
    assert_eq!(counts.info, 2);
}

// --- Test 2: WARN counting -------------------------------------------------
#[test]
fn counts_warn_lines() {
    let counts = count_levels(SAMPLE);
    assert_eq!(counts.warn, 1);
}

// --- Test 3: ERROR counting ------------------------------------------------
#[test]
fn counts_error_lines() {
    let counts = count_levels(SAMPLE);
    assert_eq!(counts.error, 1);
}

#[test]
fn full_counts_match_expected() {
    let counts = count_levels(SAMPLE);
    assert_eq!(counts, LogCounts { info: 2, warn: 1, error: 1 });
}

#[test]
fn ignores_unrecognised_and_blank_lines() {
    let input = "DEBUG noise\n\nINFO ok\nrandom text\n";
    let counts = count_levels(input);
    assert_eq!(counts, LogCounts { info: 1, warn: 0, error: 0 });
}

#[test]
fn display_format_is_correct() {
    let counts = LogCounts { info: 2, warn: 1, error: 1 };
    assert_eq!(format!("{counts}"), "INFO: 2\nWARN: 1\nERROR: 1");
}

// --- Test 4: missing file handling ----------------------------------------
#[test]
fn missing_file_returns_not_found_error() {
    let result = count_file(Path::new("definitely_missing_file_12345.log"));
    assert!(result.is_err(), "expected an error for a missing file");
    assert_eq!(result.unwrap_err().kind(), ErrorKind::NotFound);
}

#[test]
fn json_output_is_well_formed() {
    let counts = LogCounts { info: 2, warn: 1, error: 1 };
    assert_eq!(counts.to_json(), r#"{"info":2,"warn":1,"error":1}"#);
}

#[test]
fn classification_is_case_sensitive() {
    // Lowercase "info" is not a recognised level token.
    let counts = count_levels("info lower\nINFO upper\n");
    assert_eq!(counts, LogCounts { info: 1, warn: 0, error: 0 });
}

// --- End-to-end: drive the actual compiled binary -------------------------
// `CARGO_BIN_EXE_logcount` is injected by cargo for integration tests.
const BIN: &str = env!("CARGO_BIN_EXE_logcount");

#[test]
fn reads_from_stdin_with_dash() {
    let mut child = Command::new(BIN)
        .arg("-")
        .stdin(Stdio::piped())
        .stdout(Stdio::piped())
        .spawn()
        .expect("spawn");
    child
        .stdin
        .take()
        .unwrap()
        .write_all(b"INFO a\nERROR b\nINFO c\n")
        .unwrap();
    let out = child.wait_with_output().unwrap();
    assert!(out.status.success());
    let stdout = String::from_utf8(out.stdout).unwrap();
    assert_eq!(stdout, "INFO: 2\nWARN: 0\nERROR: 1\n");
}

#[test]
fn json_flag_over_stdin() {
    let mut child = Command::new(BIN)
        .args(["--json", "-"])
        .stdin(Stdio::piped())
        .stdout(Stdio::piped())
        .spawn()
        .expect("spawn");
    child
        .stdin
        .take()
        .unwrap()
        .write_all(b"WARN x\nWARN y\n")
        .unwrap();
    let out = child.wait_with_output().unwrap();
    assert!(out.status.success());
    let stdout = String::from_utf8(out.stdout).unwrap();
    assert_eq!(stdout.trim(), r#"{"info":0,"warn":2,"error":0}"#);
}

#[test]
fn version_flag_prints_version_and_exits_zero() {
    let out = Command::new(BIN).arg("--version").output().unwrap();
    assert!(out.status.success());
    let stdout = String::from_utf8(out.stdout).unwrap();
    assert!(stdout.starts_with("logcount "), "got: {stdout}");
}

#[test]
fn unknown_flag_exits_with_code_2() {
    let out = Command::new(BIN).arg("--nope").output().unwrap();
    assert_eq!(out.status.code(), Some(2));
}

#[test]
fn missing_argument_exits_with_code_2() {
    let out = Command::new(BIN).output().unwrap();
    assert_eq!(out.status.code(), Some(2));
}

#[test]
fn missing_file_exits_with_code_1() {
    let out = Command::new(BIN)
        .arg("definitely_missing_98765.log")
        .output()
        .unwrap();
    assert_eq!(out.status.code(), Some(1));
}
