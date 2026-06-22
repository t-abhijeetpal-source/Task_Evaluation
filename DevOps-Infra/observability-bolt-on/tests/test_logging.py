"""Tests for the structured JSON logging layer."""

import json
import logging
import sys

import pytest
from fastapi.testclient import TestClient

from app.logging_setup import JsonFormatter


def _format(record: logging.LogRecord) -> dict[str, object]:
    return json.loads(JsonFormatter().format(record))


def test_formatter_emits_core_fields() -> None:
    record = logging.LogRecord(
        name="d6",
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
    record.duration_ms = 0.5

    payload = _format(record)
    assert payload["level"] == "INFO"
    assert payload["logger"] == "d6"
    assert payload["message"] == "request_completed"
    assert payload["request_id"] == "abc123"
    assert payload["status_code"] == 200
    # A valid ISO-8601 timestamp is always present.
    assert "T" in str(payload["timestamp"])


def test_formatter_omits_absent_context_fields() -> None:
    record = logging.LogRecord(
        name="d6",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="bare",
        args=(),
        exc_info=None,
    )
    payload = _format(record)
    assert "request_id" not in payload
    assert "trace_id" not in payload


def test_formatter_includes_stack_trace_on_exception() -> None:
    try:
        raise RuntimeError("boom")
    except RuntimeError:
        record = logging.LogRecord(
            name="d6",
            level=logging.ERROR,
            pathname=__file__,
            lineno=1,
            msg="request_failed",
            args=(),
            exc_info=True,
        )
        record.exc_info = sys.exc_info()

    payload = _format(record)
    assert "error" in payload
    assert "RuntimeError: boom" in str(payload["error"])
    assert "Traceback" in str(payload["error"])


def test_error_request_logs_stack_trace(
    client: TestClient, caplog: pytest.LogCaptureFixture
) -> None:
    with caplog.at_level(logging.ERROR):
        r = client.get("/error")
    assert r.status_code == 500
    failed = [rec for rec in caplog.records if rec.getMessage() == "request_failed"]
    assert failed, "expected a request_failed log record"
    record = failed[0]
    assert record.exc_info is not None
    assert record.status_code == 500  # type: ignore[attr-defined]
    assert record.path == "/error"  # type: ignore[attr-defined]
