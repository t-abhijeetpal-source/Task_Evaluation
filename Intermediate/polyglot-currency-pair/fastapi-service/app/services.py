"""Service layer — currency conversion business logic.

Conversion logic lives here, NOT in the routes. Uses hardcoded rates.
Raises typed errors that the route layer maps to HTTP status codes.
"""

from typing import Dict, Tuple

SUPPORTED_CURRENCIES = {"USD", "INR", "EUR"}

# Hardcoded conversion rates, keyed by (from, to).
RATES: Dict[Tuple[str, str], float] = {
    ("USD", "INR"): 83,
    ("USD", "EUR"): 0.92,
    ("INR", "USD"): 0.012,
    ("EUR", "USD"): 1.08,
    ("INR", "EUR"): 0.011,
    ("EUR", "INR"): 90,
}


class InvalidAmountError(Exception):
    """Raised when the amount is not strictly positive."""


class UnsupportedCurrencyError(Exception):
    """Raised when a currency is not supported, or the pair has no rate."""


def _normalize_number(value: float):
    """Return an int when the value is integral, else a rounded float.

    Keeps `100 USD -> INR` rendering as `8300` (per the contract) while
    preserving fractional results like `1.2`.
    """
    rounded = round(value, 6)
    return int(rounded) if rounded == int(rounded) else rounded


def convert(amount: float, from_currency: str, to_currency: str):
    """Convert `amount` from one currency to another.

    Validation order matches the API contract:
      1. amount must be > 0          -> InvalidAmountError (HTTP 422)
      2. currencies must be supported -> UnsupportedCurrencyError (HTTP 400)
    """
    if amount <= 0:
        raise InvalidAmountError("Amount must be positive")

    frm = from_currency.upper()
    to = to_currency.upper()

    if frm not in SUPPORTED_CURRENCIES or to not in SUPPORTED_CURRENCIES:
        raise UnsupportedCurrencyError("Unsupported currency")

    if frm == to:
        rate = 1.0
    else:
        rate = RATES.get((frm, to))
        if rate is None:
            raise UnsupportedCurrencyError("Unsupported currency")

    return _normalize_number(amount * rate)
