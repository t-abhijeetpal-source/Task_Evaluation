"""Structured JSON logging for the D2 Jobs API.

Replaces uvicorn's default plain-text access lines with one machine-readable
JSON object per log record on stdout. Every request log carries:
  timestamp, level, logger, message, request_id, method, path,
  status_code, duration_ms — and, on failure, an `error` stack trace.

This mirrors the worker's structured-log convention so a single log pipeline
can ingest both services uniformly.
"""

import json
import logging
import sys
from datetime import UTC, datetime

# Extra fields we promote from `record` (set via `logger.info(..., extra={...})`).
_CONTEXT_FIELDS = (
    "request_id",
    "method",
    "path",
    "status_code",
    "duration_ms",
    "client",
)


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": datetime.fromtimestamp(record.created, tz=UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        for field in _CONTEXT_FIELDS:
            value = getattr(record, field, None)
            if value is not None:
                payload[field] = value
        if record.exc_info:
            payload["error"] = self.formatException(record.exc_info)
        return json.dumps(payload, default=str)


def configure_logging(level: str = "INFO") -> logging.Logger:
    """Install the JSON formatter on the root + uvicorn loggers."""
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())

    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(level)

    # Route uvicorn's own loggers through the same JSON handler; silence its
    # duplicate plain-text access log (we emit our own structured access line).
    for name in ("uvicorn", "uvicorn.error"):
        lg = logging.getLogger(name)
        lg.handlers = [handler]
        lg.propagate = False
    access = logging.getLogger("uvicorn.access")
    access.handlers = []
    access.propagate = False

    return logging.getLogger("d2")
