"""Validation error handling.

FastAPI's default 422 body echoes the offending input under ``input``. When a
client sends a bare ``Infinity``/``NaN`` token (Python's JSON parser accepts
these non-standard tokens), that input is a non-finite float, and serialising it
back raises ``ValueError: Out of range float values are not JSON compliant`` —
turning a clean 422 into a 500. This handler sanitises non-finite floats so
invalid financial input always yields a well-formed 422.
"""

import math
from typing import Any

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


def _sanitize(value: Any) -> Any:
    """Recursively replace non-finite floats with their string form."""
    if isinstance(value, float) and not math.isfinite(value):
        return str(value)  # 'inf' / '-inf' / 'nan'
    if isinstance(value, dict):
        return {k: _sanitize(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_sanitize(v) for v in value]
    return value


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Return a JSON-safe 422 for any request-validation failure."""
    return JSONResponse(status_code=422, content={"detail": _sanitize(exc.errors())})
