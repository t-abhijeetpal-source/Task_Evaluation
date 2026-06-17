//! Library crate for the log-count CLI.
//!
//! Exposing the logic as a library lets the integration tests in `tests/`
//! exercise parsing and counting directly, while `main.rs` stays a thin
//! CLI shell over the same code.

pub mod models;
pub mod parser;
