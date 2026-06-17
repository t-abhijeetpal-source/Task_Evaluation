"""Automated tests for the transaction service.

Covers the three required scenarios (create, list, balance) plus bonus
validation-failure cases. The store is reset before each test for isolation.
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.storage import storage


@pytest.fixture(autouse=True)
def reset_storage():
    """Ensure each test starts with an empty store."""
    storage.clear()
    yield
    storage.clear()


@pytest.fixture
def client():
    return TestClient(app)


# --- Test 1: create transaction -------------------------------------------
def test_create_transaction(client):
    resp = client.post(
        "/transactions",
        json={"amount": 100, "type": "credit", "description": "salary"},
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body == {"id": 1}


# --- Test 2: list transactions --------------------------------------------
def test_list_transactions(client):
    client.post("/transactions", json={"amount": 100, "type": "credit"})
    client.post("/transactions", json={"amount": 40, "type": "debit", "description": "lunch"})

    resp = client.get("/transactions")
    assert resp.status_code == 200
    txns = resp.json()
    assert len(txns) == 2
    assert txns[0]["amount"] == 100
    assert txns[0]["type"] == "credit"
    assert txns[1]["type"] == "debit"
    # Each transaction carries the full shape.
    for txn in txns:
        assert {"id", "amount", "type", "description", "timestamp"} <= set(txn.keys())


# --- Test 3: balance calculation ------------------------------------------
def test_balance_calculation(client):
    client.post("/transactions", json={"amount": 1000, "type": "credit"})  # +1000
    client.post("/transactions", json={"amount": 300, "type": "debit"})   # -300
    client.post("/transactions", json={"amount": 200, "type": "debit"})   # -200

    resp = client.get("/balance")
    assert resp.status_code == 200
    assert resp.json() == {"balance": 500}


def test_balance_empty_is_zero(client):
    resp = client.get("/balance")
    assert resp.status_code == 200
    assert resp.json() == {"balance": 0}


# --- Bonus: validation failures -------------------------------------------
def test_rejects_non_positive_amount(client):
    resp = client.post("/transactions", json={"amount": 0, "type": "credit"})
    assert resp.status_code == 422  # Pydantic validation error


def test_rejects_invalid_type(client):
    resp = client.post(
        "/transactions",
        json={"amount": 50, "type": "transfer", "description": "nope"},
    )
    assert resp.status_code == 422
