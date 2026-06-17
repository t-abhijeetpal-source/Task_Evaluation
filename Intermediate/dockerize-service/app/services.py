"""Service layer — currency conversion business logic (hardcoded rates)."""

from typing import Dict, Tuple

SUPPORTED_CURRENCIES = {"USD", "INR", "EUR"}

RATES: Dict[Tuple[str, str], float] = {
    ("USD", "INR"): 83,
    ("USD", "EUR"): 0.92,
    ("INR", "USD"): 0.012,
    ("EUR", "USD"): 1.08,
    ("INR", "EUR"): 0.011,
    ("EUR", "INR"): 90,
}


class InvalidAmountError(Exception):
    """Raised when amount is not strictly positive."""


class UnsupportedCurrencyError(Exception):
    """Raised when a currency or pair is unsupported."""


def _normalize_number(value: float):
    rounded = round(value, 6)
    return int(rounded) if rounded == int(rounded) else rounded


def convert(amount: float, from_currency: str, to_currency: str):
    if amount <= 0:
        raise InvalidAmountError("Amount must be positive")
    frm, to = from_currency.upper(), to_currency.upper()
    if frm not in SUPPORTED_CURRENCIES or to not in SUPPORTED_CURRENCIES:
        raise UnsupportedCurrencyError("Unsupported currency")
    if frm == to:
        rate = 1.0
    else:
        rate = RATES.get((frm, to))
        if rate is None:
            raise UnsupportedCurrencyError("Unsupported currency")
    return _normalize_number(amount * rate)
