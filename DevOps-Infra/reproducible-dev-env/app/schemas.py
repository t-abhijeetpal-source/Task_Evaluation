"""Request/response models for the D5 service.

The operands are *bounded* (``OPERAND_LIMIT``) so the public API cannot be
coerced into unbounded arithmetic, and ``extra='forbid'`` rejects unknown keys
instead of silently ignoring them. Out-of-range or unknown input therefore
fails validation at the boundary with a 422 — see ``tests/test_app.py``.
"""

from pydantic import BaseModel, ConfigDict, Field

# Largest magnitude operand the public API accepts on either side.
OPERAND_LIMIT = 1_000_000_000


class AddRequest(BaseModel):
    """Bounded inputs for the canonical ``POST /v1/add`` endpoint."""

    model_config = ConfigDict(extra="forbid")

    a: int = Field(..., ge=-OPERAND_LIMIT, le=OPERAND_LIMIT, description="First operand.")
    b: int = Field(..., ge=-OPERAND_LIMIT, le=OPERAND_LIMIT, description="Second operand.")


class AddResponse(BaseModel):
    """Result of an addition."""

    a: int
    b: int
    sum: int
    even: bool


class HealthResponse(BaseModel):
    """Liveness payload — echoes the live runtime so the pinned version is visible."""

    status: str
    python: str
    app_env: str
    version: str
