//! Integration tests for the log-count tool.
//!
//! Exercises the public library API (parsing + counting + file errors).

use std::io::ErrorKind;
use std::path::Path;

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
