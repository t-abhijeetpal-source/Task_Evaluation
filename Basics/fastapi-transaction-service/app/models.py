"""Domain models — the internal representation of a transaction.

This layer is storage-agnostic and HTTP-agnostic. It defines *what* a
transaction is, independent of how it is validated at the API boundary
(schemas.py) or how it is persisted (storage.py).
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class TransactionType(str, Enum):
    """The only two valid transaction types."""

    CREDIT = "credit"
    DEBIT = "debit"


@dataclass
class Transaction:
    """A single ledger entry.

    Attributes:
        id: Auto-incremented unique identifier assigned by storage.
        amount: Positive monetary amount (validation enforced at the API layer).
        type: credit or debit.
        description: Optional free-text note.
        timestamp: UTC creation time, assigned by the service layer.
    """

    id: int
    amount: float
    type: TransactionType
    description: str
    timestamp: datetime
