//! CLI layer.
//!
//! Parses argv, invokes the parsing layer, prints the counts, and maps
//! errors to friendly messages + a non-zero exit code. No business logic
//! lives here.

use std::env;
use std::io::ErrorKind;
use std::path::Path;
use std::process;

use logcount::parser;

fn main() {
    let args: Vec<String> = env::args().collect();
    let program = args.first().map(String::as_str).unwrap_or("logcount");

    let path = match args.get(1) {
        Some(p) => p,
        None => {
            eprintln!("Error:");
            eprintln!("Usage: {program} <log-file>");
            process::exit(2);
        }
    };

    match parser::count_file(Path::new(path)) {
        Ok(counts) => {
            println!("{counts}");
        }
        Err(err) if err.kind() == ErrorKind::NotFound => {
            eprintln!("Error:");
            eprintln!("File not found: {path}");
            process::exit(1);
        }
        Err(err) => {
            eprintln!("Error:");
            eprintln!("Could not read {path}: {err}");
            process::exit(1);
        }
    }
}
