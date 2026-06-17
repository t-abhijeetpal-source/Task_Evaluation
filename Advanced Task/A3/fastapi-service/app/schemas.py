from typing import List, Optional

from pydantic import BaseModel


class TransactionIn(BaseModel):
    schema_version: str = "1.0"
    transaction_id: str
    user_id: str
    amount: float
    country: str
    merchant_category: str
    timestamp: str


class ScoreResult(BaseModel):
    schema_version: str = "1.0"
    transaction_id: str
    score: int
    risk_level: str
    reasons: List[str]


class TransactionOut(BaseModel):
    transaction: dict
    score: Optional[int] = None
    risk_level: Optional[str] = None
    status: str
