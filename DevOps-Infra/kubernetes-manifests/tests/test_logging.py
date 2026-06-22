"""Tests for structured JSON logging."""

import json
import logging

from app.logging_setup import JsonFormatter, configure_logging


def test_json_formatter_emits_valid_json() -> None:
    formatter = JsonFormatter()
    record = logging.LogRecord(
        name="d4",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="request_completed",
        args=(),
        exc_info=None,
    )
    record.request_id = "abc123"
    record.method = "GET"
    record.path = "/health"
    record.status_code = 200
    record.duration_ms = 1.23

    payload = json.loads(formatter.format(record))
    assert payload["message"] == "request_completed"
    assert payload["level"] == "INFO"
    assert payload["request_id"] == "abc123"
    assert payload["method"] == "GET"
    assert payload["path"] == "/health"
    assert payload["status_code"] == 200
    assert payload["duration_ms"] == 1.23
    assert "timestamp" in payload


def test_json_formatter_includes_stack_trace_on_error() -> None:
    formatter = JsonFormatter()
    try:
        raise ValueError("boom")
    except ValueError:
        import sys

        record = logging.LogRecord(
            name="d4",
            level=logging.ERROR,
            pathname=__file__,
            lineno=1,
            msg="request_failed",
            args=(),
            exc_info=sys.exc_info(),
        )
    payload = json.loads(formatter.format(record))
    assert "error" in payload
    assert "ValueError: boom" in payload["error"]


def test_configure_logging_installs_json_handler() -> None:
    logger = configure_logging("INFO")
    assert logger.name == "d4"
    root = logging.getLogger()
    assert len(root.handlers) == 1
    assert isinstance(root.handlers[0].formatter, JsonFormatter)
    # uvicorn.access is silenced so we don't double-log requests.
    assert logging.getLogger("uvicorn.access").handlers == []
