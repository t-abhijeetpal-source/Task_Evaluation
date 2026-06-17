//! Parsing layer.
//!
//! Turns raw log text (or a file on disk) into `LogCounts`. File reading
//! returns a `Result` so the CLI can handle a missing file gracefully
//! instead of panicking.

use std::fs;
use std::io;
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

/// Read a log file from disk and count its levels.
///
/// Propagates `io::Error` (e.g. `NotFound`) to the caller — it does not panic.
pub fn count_file(path: &Path) -> io::Result<LogCounts> {
    let content = fs::read_to_string(path)?;
    Ok(count_levels(&content))
}
