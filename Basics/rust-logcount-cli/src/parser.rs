//! Parsing layer — streaming line-by-line counting (constant memory).

use std::fs::File;
use std::io::{self, BufRead, BufReader};
use std::path::Path;

use crate::models::{LogCounts, LogLevel};

/// Count INFO/WARN/ERROR occurrences in already-loaded log content.
pub fn count_levels(content: &str) -> LogCounts {
    let mut counts = LogCounts::default();
    for line in content.lines() {
        if let Some(level) = LogLevel::from_line(line) {
            counts.record(level);
        }
    }
    counts
}

/// Incrementally count levels from any line iterator.
pub fn count_lines<I, S>(lines: I) -> LogCounts
where
    I: IntoIterator<Item = io::Result<S>>,
    S: AsRef<str>,
{
    let mut counts = LogCounts::default();
    for line in lines {
        let line = line.expect("read log line");
        if let Some(level) = LogLevel::from_line(line.as_ref()) {
            counts.record(level);
        }
    }
    counts
}

/// Stream a log file from disk and count its levels.
pub fn count_file(path: &Path) -> io::Result<LogCounts> {
    let file = File::open(path)?;
    Ok(count_lines(BufReader::new(file).lines()))
}

/// Stream stdin and count log levels.
pub fn count_stdin() -> io::Result<LogCounts> {
    Ok(count_lines(BufReader::new(io::stdin()).lines()))
}
