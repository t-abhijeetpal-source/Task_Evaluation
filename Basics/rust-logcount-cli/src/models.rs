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
            _ => None,
        }
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
