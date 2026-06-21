//! Domain models — business logic layer.
//!
//! Defines the log levels we recognise and the result type that holds the
//! per-level counts. Pure data + classification logic; no I/O, no CLI concerns.

use std::fmt;

/// The three log levels this tool recognises.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum LogLevel {
    Info,
    Warn,
    Error,
}

impl LogLevel {
    /// Classify a log line by its first whitespace-separated token.
    ///
    /// Lines whose first token is not a recognised level (blank lines,
    /// continuations, etc.) return `None` and are not counted.
    pub fn from_line(line: &str) -> Option<LogLevel> {
        match line.split_whitespace().next()? {
            "INFO" => Some(LogLevel::Info),
            "WARN" => Some(LogLevel::Warn),
            "ERROR" => Some(LogLevel::Error),
            _ => Self::from_json_line(line),
        }
    }

    /// Recognise structured JSON log lines like `{"level":"ERROR",...}`.
    fn from_json_line(line: &str) -> Option<LogLevel> {
        let trimmed = line.trim();
        if !trimmed.starts_with('{') {
            return None;
        }
        for (needle, level) in [
            ("\"level\":\"INFO\"", LogLevel::Info),
            ("\"level\":\"WARN\"", LogLevel::Warn),
            ("\"level\":\"ERROR\"", LogLevel::Error),
            ("\"level\": \"INFO\"", LogLevel::Info),
            ("\"level\": \"WARN\"", LogLevel::Warn),
            ("\"level\": \"ERROR\"", LogLevel::Error),
        ] {
            if trimmed.contains(needle) {
                return Some(level);
            }
        }
        None
    }
}

/// Aggregate counts of each log level found in a file.
#[derive(Debug, Default, Clone, Copy, PartialEq, Eq)]
pub struct LogCounts {
    pub info: usize,
    pub warn: usize,
    pub error: usize,
}

impl LogCounts {
    /// Record one occurrence of the given level.
    pub fn record(&mut self, level: LogLevel) {
        match level {
            LogLevel::Info => self.info += 1,
            LogLevel::Warn => self.warn += 1,
            LogLevel::Error => self.error += 1,
        }
    }

    /// Render as a compact, machine-parseable JSON object (no deps).
    ///
    /// Counts are integers, so manual formatting is safe — there are no strings
    /// to escape.
    pub fn to_json(&self) -> String {
        format!(
            "{{\"info\":{},\"warn\":{},\"error\":{}}}",
            self.info, self.warn, self.error
        )
    }
}

impl fmt::Display for LogCounts {
    /// Renders as:
    /// ```text
    /// INFO: 2
    /// WARN: 1
    /// ERROR: 1
    /// ```
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        writeln!(f, "INFO: {}", self.info)?;
        writeln!(f, "WARN: {}", self.warn)?;
        write!(f, "ERROR: {}", self.error)
    }
}
