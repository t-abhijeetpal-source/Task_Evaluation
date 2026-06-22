"""Optional OpenTelemetry distributed tracing (feature-flagged).

Tracing is **off by default** and adds zero runtime cost unless enabled:

  * ``OTEL_ENABLED=true``  installs a real ``TracerProvider`` exporting spans
    over OTLP/HTTP to ``OTEL_EXPORTER_OTLP_ENDPOINT`` (default the Jaeger
    all-in-one collector from ``compose.tracing.yml``).
  * When disabled, :func:`span` is a no-op context manager and
    :func:`current_ids` returns ``(None, None)`` — the OpenTelemetry packages
    are only imported lazily inside :func:`init_tracing`, so the service runs
    even if they are not installed.

When enabled, the active ``trace_id`` / ``span_id`` are injected into every
structured access log line, so logs and traces correlate one-to-one.
"""

from __future__ import annotations

import os
from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from typing import Any

_ENABLED: bool = False
_tracer: Any = None


def _truthy(value: str | None) -> bool:
    return (value or "").strip().lower() in ("1", "true", "yes", "on")


def _service_name() -> str:
    return os.getenv("OTEL_SERVICE_NAME", "d6-sample")


def is_enabled() -> bool:
    """Whether tracing is currently active."""
    return _ENABLED


def init_tracing(force: bool | None = None) -> bool:
    """Install the global tracer provider when enabled.

    ``force`` overrides the ``OTEL_ENABLED`` env var (used by tests). Returns
    ``True`` when tracing ends up active.
    """
    global _ENABLED, _tracer

    enabled = force if force is not None else _truthy(os.getenv("OTEL_ENABLED"))
    if not enabled:
        _ENABLED = False
        return False

    # Imported lazily: the OTel packages are only needed when tracing is on.
    from opentelemetry import trace  # pragma: no cover
    from opentelemetry.exporter.otlp.proto.http.trace_exporter import (  # pragma: no cover
        OTLPSpanExporter,
    )
    from opentelemetry.sdk.resources import Resource  # pragma: no cover
    from opentelemetry.sdk.trace import TracerProvider  # pragma: no cover
    from opentelemetry.sdk.trace.export import BatchSpanProcessor  # pragma: no cover

    endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://jaeger:4318").rstrip(
        "/"
    )  # pragma: no cover
    provider = TracerProvider(  # pragma: no cover
        resource=Resource.create({"service.name": _service_name()})
    )
    provider.add_span_processor(  # pragma: no cover
        BatchSpanProcessor(OTLPSpanExporter(endpoint=f"{endpoint}/v1/traces"))
    )
    trace.set_tracer_provider(provider)  # pragma: no cover
    _tracer = provider.get_tracer("d6")  # pragma: no cover
    _ENABLED = True  # pragma: no cover
    return True  # pragma: no cover


@contextmanager
def span(name: str, attributes: Mapping[str, Any] | None = None) -> Iterator[Any]:
    """Start a span as the current span when tracing is active; else a no-op."""
    if not _ENABLED or _tracer is None:
        yield None
        return
    with _tracer.start_as_current_span(name, attributes=dict(attributes or {})) as active:
        yield active


def current_ids() -> tuple[str | None, str | None]:
    """Return the active ``(trace_id, span_id)`` as zero-padded hex, or
    ``(None, None)`` when tracing is disabled or no span is recording."""
    if not _ENABLED:
        return None, None
    from opentelemetry import trace

    ctx = trace.get_current_span().get_span_context()
    if not ctx.is_valid:
        return None, None
    return format(ctx.trace_id, "032x"), format(ctx.span_id, "016x")


def install_in_memory_tracer() -> Any:
    """Test helper: install an in-memory-exporting provider and return the
    ``InMemorySpanExporter`` so a test can assert spans were produced.

    Avoids ``set_tracer_provider`` (a process-global that can only be set once)
    by wiring :data:`_tracer` directly.
    """
    global _ENABLED, _tracer
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import SimpleSpanProcessor
    from opentelemetry.sdk.trace.export.in_memory_span_exporter import (
        InMemorySpanExporter,
    )

    exporter = InMemorySpanExporter()
    provider = TracerProvider(resource=Resource.create({"service.name": _service_name()}))
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    _tracer = provider.get_tracer("d6")
    _ENABLED = True
    return exporter


def reset() -> None:
    """Test helper: disable tracing and drop the tracer reference."""
    global _ENABLED, _tracer
    _ENABLED = False
    _tracer = None
