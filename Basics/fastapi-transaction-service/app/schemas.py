"""Pydantic schemas — the API boundary contract.

These models validate incoming requests and shape outgoing responses.
All input validation (positive amount, valid type, optional description)
lives here so that routes and services can trust their inputs.
"""

import math
from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.config import settings
from app.models import TransactionType


class TransactionCreate(BaseModel):
    """Request body for POST /transactions."""

    amount: float = Field(..., gt=0, description="Positive, at most 2 decimal places")
    type: TransactionType = Field(..., description="credit or debit")
    description: Optional[str] = Field(
        default="", max_length=500, description="Optional free-text note"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {"amount": 100, "type": "credit", "description": "salary"}
        }
    )

    @field_validator("amount")
    @classmethod
    def _amount_is_sane_money(cls, v: float) -> float:
        """Reject the float traps that ``gt=0`` alone lets through.

        ``Field(gt=0)`` still accepts ``inf`` and sub-cent precision like
        ``9.999``. Money must be finite, bounded, and at most 2 decimals.
        """
        if not math.isfinite(v):
            raise ValueError("amount must be a finite number")
        if v > settings.max_amount:
            raise ValueError(f"amount must not exceed {settings.max_amount}")
        # Decimal(str(v)) avoids binary-float artefacts when checking precision.
        exponent = Decimal(str(v)).normalize().as_tuple().exponent
        if isinstance(exponent, int) and exponent < -2:
            raise ValueError("amount must have at most 2 decimal places")
        return v


class TransactionOut(BaseModel):
    """A transaction as returned by GET /transactions."""

    id: int
    amount: float
    type: TransactionType
    description: str
    timestamp: datetime


class CreateResponse(BaseModel):
    """Response body for POST /transactions."""

    id: int


class BalanceResponse(BaseModel):
    """Response body for GET /balance."""

    balance: float
