"""Signal-safe container entrypoint.

Reads ``PORT`` from the environment and execs uvicorn **in place**
(``os.execvp``), so uvicorn replaces this process and becomes PID 1. It then
receives ``SIGTERM``/``SIGINT`` directly from ``docker stop`` and shuts down
gracefully — unlike a ``sh -c "uvicorn ... --port $PORT"`` wrapper, where the
shell is PID 1 and may not forward signals to its child.
"""

import os


def build_argv() -> list:
    """Construct the uvicorn argv from the environment (testable, no side effects)."""
    port = os.environ.get("PORT", "8000")
    return ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", port]


def main() -> None:
    argv = build_argv()
    # Replace the current process image — uvicorn inherits PID 1 and its signals.
    os.execvp(argv[0], argv)


if __name__ == "__main__":
    main()
