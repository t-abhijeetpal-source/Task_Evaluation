//! CLI layer.
//!
//! Parses argv, invokes the parsing layer, prints the counts, and maps
//! errors to friendly messages + a non-zero exit code. No business logic
//! lives here.
//!
//! Usage:
//!     logcount [--json] <log-file>
//!     logcount [--json] -          # read from stdin
//!     logcount --help | --version

use std::env;
use std::io::ErrorKind;
use std::path::Path;
use std::process;

use logcount::parser;

const VERSION: &str = env!("CARGO_PKG_VERSION");

fn print_usage(program: &str) {
    eprintln!("Usage: {program} [--json] <log-file>");
    eprintln!("       {program} [--json] -          # read from stdin");
    eprintln!("       {program} --help | --version");
}

fn main() {
    let args: Vec<String> = env::args().collect();
    let program = args.first().map(String::as_str).unwrap_or("logcount");

    let mut json = false;
    let mut path: Option<&str> = None;

    for arg in &args[1..] {
        match arg.as_str() {
            "-h" | "--help" => {
                print_usage(program);
                process::exit(0);
            }
            "-V" | "--version" => {
                println!("logcount {VERSION}");
                process::exit(0);
            }
            "--json" => json = true,
            // A lone "-" means stdin; anything else starting with "-" is unknown.
            flag if flag.starts_with('-') && flag != "-" => {
                eprintln!("Error: unknown option: {flag}");
                print_usage(program);
                process::exit(2);
            }
            value => {
                if path.is_some() {
                    eprintln!("Error: too many arguments");
                    print_usage(program);
                    process::exit(2);
                }
                path = Some(value);
            }
        }
    }

    let source = match path {
        Some(p) => p,
        None => {
            eprintln!("Error: missing log file");
            print_usage(program);
            process::exit(2);
        }
    };

    let counts_result = if source == "-" {
        parser::count_stdin()
    } else {
        parser::count_file(Path::new(source))
    };

    match counts_result {
        Ok(counts) => {
            if json {
                println!("{}", counts.to_json());
            } else {
                println!("{counts}");
            }
        }
        Err(err) if err.kind() == ErrorKind::NotFound => {
            eprintln!("Error:");
            eprintln!("File not found: {source}");
            process::exit(1);
        }
        Err(err) => {
            eprintln!("Error:");
            eprintln!("Could not read {source}: {err}");
            process::exit(1);
        }
    }
}
