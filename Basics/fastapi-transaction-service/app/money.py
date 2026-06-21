"""Money utilities — exact arithmetic for a 2-decimal currency.

Floating-point is unsafe for money (``0.1 + 0.2 != 0.3``). This service keeps
the *public* API in plain JSON numbers for simplicity, but performs all
summation in integer minor units (cents) so balances are exact and free of
binary-float drift. A production system would push this further to a DB
``NUMERIC`` column / ``Decimal`` end-to-end; for an in-memory service this
guarantees correctness at the boundary where it matters: aggregation.
"""

from decimal import ROUND_HALF_UP, Decimal

CENTS = Decimal("0.01")


def to_cents(amount: float) -> int:
    """Convert a 2-dp amount to integer minor units, exactly.

    Goes via ``Decimal(str(...))`` (not ``Decimal(float)``) to avoid importing
    binary-float error into the conversion.
    """
    return int((Decimal(str(amount)) / CENTS).to_integral_value(rounding=ROUND_HALF_UP))


def from_cents(cents: int) -> float:
    """Convert integer minor units back to a 2-dp float for the API response."""
    return float((Decimal(cents) * CENTS).quantize(CENTS))
