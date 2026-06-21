from typing import List, Optional

from pydantic import BaseModel, Field


class TransactionIn(BaseModel):
    schema_version: str = "1.0"
    # Strict id: prevents path traversal in the queue filename (A5-1) and bounds storage.
    transaction_id: str = Field(..., pattern=r"^[A-Za-z0-9_-]{1,64}$")
    user_id: str = Field(..., min_length=1, max_length=128)
    amount: float
    country: str = Field(..., min_length=2, max_length=8)
    merchant_category: str = Field(..., min_length=1, max_length=64)
    timestamp: str = Field(..., max_length=64)


class ScoreResult(BaseModel):
    schema_version: str = "1.0"
    transaction_id: str = Field(..., pattern=r"^[A-Za-z0-9_-]{1,64}$")
    # Defense-in-depth bound (A5-13): the route also validates range + band, but
    # rejecting out-of-range scores at the schema layer closes the gap entirely.
    score: int = Field(..., ge=0, le=100)
    risk_level: str
    reasons: List[str]


class TransactionOut(BaseModel):
    transaction: dict
    score: Optional[int] = None
    risk_level: Optional[str] = None
    status: str
