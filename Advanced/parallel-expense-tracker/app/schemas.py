"""Request/response models with strict, honest money validation.

Money arrives as a JSON number (or numeric string) and is parsed into a
``Decimal`` so we can reject the values that crash a naive float pipeline:
NaN, +/-Infinity, sub-cent precision, and out-of-range magnitudes. Positivity
is enforced in the route so the documented ``{"error": "amount must be
positive"}`` contract is preserved.
"""

from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, field_validator

# Bounds. 10 billion currency units keeps amount_cents well inside SQLite's
# signed 64-bit INTEGER range and rejects absurd/overflow inputs early.
MAX_AMOUNT = Decimal("10000000000")
MAX_CATEGORY_LEN = 64
MAX_NOTE_LEN = 255


class ExpenseCreate(BaseModel):
    amount: Decimal
    category: str
    note: Optional[str] = ""

    @field_validator("amount")
    @classmethod
    def _amount_must_be_finite_and_2dp(cls, value: Decimal) -> Decimal:
        # Reject NaN / +-Infinity before they ever reach the DB or JSON encoder.
        if not value.is_finite():
            raise ValueError("amount must be a finite number")
        # At most 2 decimal places — we store integer cents, no sub-cent money.
        exponent = value.as_tuple().exponent
        if isinstance(exponent, int) and exponent < -2:
            raise ValueError("amount supports at most 2 decimal places")
        if abs(value) > MAX_AMOUNT:
            raise ValueError(f"amount must be <= {MAX_AMOUNT}")
        return value

    @field_validator("category")
    @classmethod
    def _normalize_category(cls, value: str) -> str:
        normalized = value.strip().lower()
        if not normalized:
            raise ValueError("category must not be empty")
        if len(normalized) > MAX_CATEGORY_LEN:
            raise ValueError(f"category must be <= {MAX_CATEGORY_LEN} characters")
        return normalized

    @field_validator("note")
    @classmethod
    def _normalize_note(cls, value: Optional[str]) -> str:
        normalized = (value or "").strip()
        if len(normalized) > MAX_NOTE_LEN:
            raise ValueError(f"note must be <= {MAX_NOTE_LEN} characters")
        return normalized


class ExpenseOut(BaseModel):
    id: int
    amount: float  # 2-decimal wire value derived from integer cents
    category: str
    note: Optional[str] = ""
    created_at: str

    model_config = ConfigDict(from_attributes=True)


class Summary(BaseModel):
    total: float
    count: int
    by_category: dict
