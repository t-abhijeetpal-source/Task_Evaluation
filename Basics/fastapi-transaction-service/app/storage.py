"""Storage layer — in-memory persistence.

A deliberately simple, thread-safe in-memory store with auto-incrementing
ids. Swapping this for a real database would not require changes to the
service or API layers, since they only depend on its public methods.
"""

import threading
from typing import List

from app.models import Transaction


class InMemoryStorage:
    """Append-only in-memory transaction store."""

    def __init__(self) -> None:
        self._transactions: List[Transaction] = []
        self._next_id: int = 1
        self._lock = threading.Lock()

    def add(self, transaction: Transaction) -> Transaction:
        """Assign an id, persist, and return the stored transaction."""
        with self._lock:
            transaction.id = self._next_id
            self._next_id += 1
            self._transactions.append(transaction)
            return transaction

    def list_all(self) -> List[Transaction]:
        """Return all stored transactions (a shallow copy)."""
        with self._lock:
            return list(self._transactions)

    def clear(self) -> None:
        """Reset the store — used by tests for isolation."""
        with self._lock:
            self._transactions.clear()
            self._next_id = 1


# Module-level singleton used by the running app.
storage = InMemoryStorage()
