"""Storage layer — in-memory persistence with O(1) running balance."""

import threading
from typing import List, Optional

from app.models import Transaction, TransactionType
from app.money import to_cents


class InMemoryStorage:
    """Append-only in-memory transaction store."""

    def __init__(self) -> None:
        self._transactions: List[Transaction] = []
        self._next_id: int = 1
        self._balance_cents: int = 0
        self._lock = threading.Lock()

    def add(self, transaction: Transaction) -> Transaction:
        """Assign an id, persist, update running balance, return stored txn."""
        with self._lock:
            transaction.id = self._next_id
            self._next_id += 1
            self._transactions.append(transaction)
            cents = to_cents(transaction.amount)
            if transaction.type == TransactionType.CREDIT:
                self._balance_cents += cents
            else:
                self._balance_cents -= cents
            return transaction

    def list_all(self, limit: Optional[int] = None, offset: int = 0) -> List[Transaction]:
        """Return stored transactions with optional pagination."""
        with self._lock:
            start = max(0, offset)
            end = start + limit if limit is not None else None
            return list(self._transactions[start:end])

    def balance_cents(self) -> int:
        """Return the running ledger balance in integer minor units."""
        with self._lock:
            return self._balance_cents

    def clear(self) -> None:
        """Reset the store — used by tests for isolation."""
        with self._lock:
            self._transactions.clear()
            self._next_id = 1
            self._balance_cents = 0


storage = InMemoryStorage()
