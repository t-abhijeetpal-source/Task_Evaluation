"""Tests for the optional OpenTelemetry tracing layer."""

import logging
from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from app import tracing

# Tracing is optional; skip cleanly if the OTel SDK is not installed.
pytest.importorskip("opentelemetry.sdk.trace")


@pytest.fixture
def in_memory_tracing() -> Iterator[object]:
    exporter = tracing.install_in_memory_tracer()
    try:
        yield exporter
    finally:
        tracing.reset()


def test_disabled_by_default() -> None:
    tracing.reset()
    assert tracing.is_enabled() is False
    with tracing.span("noop") as s:
        assert s is None
    assert tracing.current_ids() == (None, None)


def test_span_created_when_enabled(
    client: TestClient, in_memory_tracing: object, caplog: pytest.LogCaptureFixture
) -> None:
    assert tracing.is_enabled() is True
    with caplog.at_level(logging.INFO):
        r = client.get("/health")
    assert r.status_code == 200

    # A span was recorded and exported to the in-memory store.
    spans = in_memory_tracing.get_finished_spans()  # type: ignore[attr-defined]
    assert spans, "expected at least one exported span"
    assert any(span.name == "GET /health" for span in spans)

    # The structured log line carries the correlated trace/span ids.
    completed = [rec for rec in caplog.records if rec.getMessage() == "request_completed"]
    assert completed
    trace_id = getattr(completed[-1], "trace_id", None)
    assert isinstance(trace_id, str) and len(trace_id) == 32
