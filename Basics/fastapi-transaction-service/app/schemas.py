"""Pydantic schemas — the API boundary contract.

These models validate incoming requests and shape outgoing responses.
All input validation (positive amount, valid type, optional description)
lives here so that routes and services can trust their inputs.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models import TransactionType


class TransactionCreate(BaseModel):
    """Request body for POST /transactions."""

    amount: float = Field(..., gt=0, description="Must be greater than 0")
    type: TransactionType = Field(..., description="credit or debit")
    description: Optional[str] = Field(default="", description="Optional free-text note")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {"amount": 100, "type": "credit", "description": "salary"}
        }
    )


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
