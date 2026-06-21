"""Tests for storage running balance and pagination."""

from datetime import datetime, timezone

import pytest

from app.models import Transaction, TransactionType
from app.storage import InMemoryStorage


def _txn(amount: float, txn_type: TransactionType) -> Transaction:
    return Transaction(
        id=0,
        amount=amount,
        type=txn_type,
        description="",
        timestamp=datetime.now(timezone.utc),
    )


@pytest.fixture
def store():
    s = InMemoryStorage()
    yield s
    s.clear()


def test_running_balance_on_add(store):
    store.add(_txn(100.0, TransactionType.CREDIT))
    store.add(_txn(40.0, TransactionType.DEBIT))
    assert store.balance_cents() == 6000


def test_list_all_pagination(store):
    for amount in (1.0, 2.0, 3.0):
        store.add(_txn(amount, TransactionType.CREDIT))
    assert len(store.list_all(limit=2, offset=1)) == 2
    assert store.list_all(limit=1, offset=1)[0].amount == 2.0
