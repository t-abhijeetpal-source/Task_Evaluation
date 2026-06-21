"""Business layer — transaction logic and balance calculation.

All domain rules live here. Routes call into this layer and never compute
anything themselves. The service depends only on the storage interface.
"""

from datetime import datetime, timezone
from typing import List

from app.models import Transaction, TransactionType
from app.money import from_cents, to_cents
from app.schemas import TransactionCreate
from app.storage import InMemoryStorage


class TransactionService:
    """Encapsulates all transaction-related business operations."""

    def __init__(self, store: InMemoryStorage) -> None:
        self._store = store

    def create_transaction(self, payload: TransactionCreate) -> Transaction:
        """Build a domain Transaction from a validated request and persist it."""
        transaction = Transaction(
            id=0,  # replaced by storage on insert
            amount=payload.amount,
            type=payload.type,
            description=payload.description or "",
            timestamp=datetime.now(timezone.utc),
        )
        return self._store.add(transaction)

    def list_transactions(self) -> List[Transaction]:
        """Return every recorded transaction."""
        return self._store.list_all()

    def get_balance(self) -> float:
        """balance = sum(credits) - sum(debits).

        Summed in integer minor units (cents) so the result is exact — no
        binary-float drift (e.g. 0.1 + 0.2). Converted back to a 2-dp number
        only for the response.
        """
        balance_cents = 0
        for txn in self._store.list_all():
            cents = to_cents(txn.amount)
            if txn.type == TransactionType.CREDIT:
                balance_cents += cents
            else:
                balance_cents -= cents
        return from_cents(balance_cents)
