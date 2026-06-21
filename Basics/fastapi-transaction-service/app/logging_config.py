"""Structured JSON logging.

Emits one JSON object per log line so logs are machine-parseable by any
aggregator (CloudWatch, Loki, ELK) without a regex grok stage. A per-request
``request_id`` is threaded through via a contextvar so every log line emitted
while handling a request can be correlated.
"""

import json
import logging
from contextvars import ContextVar

# Set by the request-id middleware; read by the formatter. Empty outside a request.
request_id_ctx: ContextVar[str] = ContextVar("request_id", default="")


class JsonFormatter(logging.Formatter):
    """Render a LogRecord as a single-line JSON object."""

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "ts": self.formatTime(record, "%Y-%m-%dT%H:%M:%S%z"),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
        }
        rid = request_id_ctx.get()
        if rid:
            payload["request_id"] = rid
        # Allow callers to attach structured fields via logger.info(..., extra={"extra": {...}}).
        extra = getattr(record, "extra", None)
        if isinstance(extra, dict):
            payload.update(extra)
        if record.exc_info:
            payload["exc"] = self.formatException(record.exc_info)
        return json.dumps(payload)


def configure_logging(level: str) -> logging.Logger:
    """Install the JSON formatter on the app logger (idempotent)."""
    logger = logging.getLogger("app")
    logger.setLevel(level)
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(JsonFormatter())
        logger.addHandler(handler)
        logger.propagate = False
    return logger
