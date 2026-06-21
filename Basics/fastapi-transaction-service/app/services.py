"""Business layer — transaction logic and balance calculation."""

from datetime import datetime, timezone
from typing import List

from app.models import Transaction
from app.money import from_cents
from app.schemas import TransactionCreate
from app.storage import InMemoryStorage


class TransactionService:
    """Encapsulates all transaction-related business operations."""

    def __init__(self, store: InMemoryStorage) -> None:
        self._store = store

    def create_transaction(self, payload: TransactionCreate) -> Transaction:
        """Build a domain Transaction from a validated request and persist it."""
        transaction = Transaction(
            id=0,
            amount=payload.amount,
            type=payload.type,
            description=payload.description or "",
            timestamp=datetime.now(timezone.utc),
        )
        return self._store.add(transaction)

    def list_transactions(self, limit: int = 100, offset: int = 0) -> List[Transaction]:
        """Return a paginated slice of recorded transactions."""
        return self._store.list_all(limit=limit, offset=offset)

    def get_balance(self) -> float:
        """Return the current balance using the store's O(1) running total."""
        return from_cents(self._store.balance_cents())
