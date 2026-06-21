"""Structured JSON logging via ``logging.config.dictConfig``.

Emits one machine-readable JSON object per record on stdout (12-factor friendly,
works under the non-root Docker user). Request logs carry request_id / method /
path / status_code / duration_ms. Request *bodies* are never logged — they may
contain financial data — only metadata.
"""

import json
import logging
import logging.config
from datetime import datetime, timezone

# Context fields promoted from `extra={...}` onto the JSON record when present.
_CONTEXT_FIELDS = ("request_id", "method", "path", "status_code", "duration_ms", "client")


class JsonFormatter(logging.Formatter):
    """Render a log record as a single-line JSON object."""

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": datetime.fromtimestamp(
                record.created, tz=timezone.utc
            ).isoformat(),
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
    """Install the JSON formatter on the root + uvicorn loggers via dictConfig."""
    logging.config.dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {"json": {"()": "app.logging_config.JsonFormatter"}},
            "handlers": {
                "stdout": {
                    "class": "logging.StreamHandler",
                    "formatter": "json",
                    "stream": "ext://sys.stdout",
                }
            },
            "root": {"handlers": ["stdout"], "level": level},
            "loggers": {
                # Route uvicorn through the JSON handler; drop its plain-text
                # access log (we emit our own structured access line).
                "uvicorn": {"handlers": ["stdout"], "level": level, "propagate": False},
                "uvicorn.error": {
                    "handlers": ["stdout"],
                    "level": level,
                    "propagate": False,
                },
                "uvicorn.access": {"handlers": [], "level": level, "propagate": False},
            },
        }
    )
    return logging.getLogger("currency-service")
