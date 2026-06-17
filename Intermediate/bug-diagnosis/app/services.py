"""Business layer — order total + bulk discount calculation.

Business rules: see SPEC.md.
"""

from typing import List

from app.schemas import Item

# A line item qualifies for the bulk discount at this quantity OR MORE (see SPEC.md rule 3).
BULK_QTY_THRESHOLD = 10
BULK_DISCOUNT_RATE = 0.10


def calculate_line_total(item: Item) -> float:
    """Return the total for one line item, applying the bulk discount if it qualifies."""
    line_total = item.price * item.qty
    if item.qty >= BULK_QTY_THRESHOLD:
        line_total = line_total * (1 - BULK_DISCOUNT_RATE)
    return line_total


def calculate_total(items: List[Item]) -> float:
    """Return the order total = sum of line totals (after discounts), rounded to 2 dp."""
    total = sum(calculate_line_total(item) for item in items)
    return round(total, 2)
