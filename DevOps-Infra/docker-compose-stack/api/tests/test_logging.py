"""JSON log formatter."""

from __future__ import annotations

import json
import logging

from app.logging_setup import JsonFormatter, configure_logging


def _record(**extra: object) -> logging.LogRecord:
    record = logging.LogRecord(
        name="d2",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="request_completed",
        args=(),
        exc_info=None,
    )
    for key, value in extra.items():
        setattr(record, key, value)
    return record


def test_formatter_emits_valid_json_with_core_fields() -> None:
    line = JsonFormatter().format(
        _record(request_id="abc", method="GET", path="/health", status_code=200)
    )
    payload = json.loads(line)
    assert payload["level"] == "INFO"
    assert payload["message"] == "request_completed"
    assert payload["request_id"] == "abc"
    assert payload["status_code"] == 200
    assert "timestamp" in payload


def test_formatter_omits_absent_context_fields() -> None:
    payload = json.loads(JsonFormatter().format(_record()))
    assert "request_id" not in payload
    assert "duration_ms" not in payload


def test_formatter_includes_error_stack_on_exc_info() -> None:
    try:
        raise ValueError("boom")
    except ValueError:
        import sys

        record = logging.LogRecord(
            name="d2",
            level=logging.ERROR,
            pathname=__file__,
            lineno=1,
            msg="request_failed",
            args=(),
            exc_info=sys.exc_info(),
        )
    payload = json.loads(JsonFormatter().format(record))
    assert "error" in payload
    assert "ValueError: boom" in payload["error"]


def test_configure_logging_installs_json_handler() -> None:
    logger = configure_logging("INFO")
    assert logger.name == "d2"
    root_handler = logging.getLogger().handlers[0]
    assert isinstance(root_handler.formatter, JsonFormatter)
    # uvicorn.access is silenced (we emit our own structured access line).
    assert logging.getLogger("uvicorn.access").handlers == []
