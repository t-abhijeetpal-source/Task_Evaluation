"""Automated tests for the transaction service."""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.routes import get_store
from app.storage import InMemoryStorage


@pytest.fixture
def store():
    return InMemoryStorage()


@pytest.fixture
def client(store):
    app.dependency_overrides[get_store] = lambda: store
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_create_transaction(client):
    resp = client.post(
        "/transactions",
        json={"amount": 100, "type": "credit", "description": "salary"},
    )
    assert resp.status_code == 201
    assert resp.json() == {"id": 1}


def test_list_transactions(client):
    client.post("/transactions", json={"amount": 100, "type": "credit"})
    client.post("/transactions", json={"amount": 40, "type": "debit", "description": "lunch"})

    resp = client.get("/transactions")
    assert resp.status_code == 200
    txns = resp.json()
    assert len(txns) == 2
    assert txns[0]["amount"] == 100
    assert txns[1]["type"] == "debit"
    for txn in txns:
        assert {"id", "amount", "type", "description", "timestamp"} <= set(txn.keys())


def test_list_transactions_pagination(client):
    client.post("/transactions", json={"amount": 1, "type": "credit"})
    client.post("/transactions", json={"amount": 2, "type": "credit"})
    client.post("/transactions", json={"amount": 3, "type": "credit"})

    resp = client.get("/transactions?limit=1&offset=1")
    assert resp.status_code == 200
    assert resp.json() == [
        {
            "id": 2,
            "amount": 2,
            "type": "credit",
            "description": "",
            "timestamp": resp.json()[0]["timestamp"],
        }
    ]


def test_balance_calculation(client):
    client.post("/transactions", json={"amount": 1000, "type": "credit"})
    client.post("/transactions", json={"amount": 300, "type": "debit"})
    client.post("/transactions", json={"amount": 200, "type": "debit"})

    resp = client.get("/balance")
    assert resp.status_code == 200
    assert resp.json() == {"balance": 500}


def test_balance_empty_is_zero(client):
    resp = client.get("/balance")
    assert resp.status_code == 200
    assert resp.json() == {"balance": 0}


def test_rejects_non_positive_amount(client):
    resp = client.post("/transactions", json={"amount": 0, "type": "credit"})
    assert resp.status_code == 422


def test_rejects_invalid_type(client):
    resp = client.post(
        "/transactions",
        json={"amount": 50, "type": "transfer", "description": "nope"},
    )
    assert resp.status_code == 422


def test_rejects_sub_cent_precision(client):
    resp = client.post("/transactions", json={"amount": 9.999, "type": "credit"})
    assert resp.status_code == 422


def test_rejects_non_finite_amount(client):
    resp = client.post(
        "/transactions",
        content='{"amount": 1e500, "type": "credit"}',
        headers={"content-type": "application/json"},
    )
    assert resp.status_code == 422


def test_rejects_amount_over_max(client):
    resp = client.post(
        "/transactions", json={"amount": 1_000_000_001, "type": "credit"}
    )
    assert resp.status_code == 422


def test_balance_is_exact_no_float_drift(client):
    client.post("/transactions", json={"amount": 0.1, "type": "credit"})
    client.post("/transactions", json={"amount": 0.2, "type": "credit"})

    resp = client.get("/balance")
    assert resp.status_code == 200
    assert resp.json() == {"balance": 0.3}


def test_balance_mixed_decimals_exact(client):
    client.post("/transactions", json={"amount": 100.10, "type": "credit"})
    client.post("/transactions", json={"amount": 0.05, "type": "debit"})
    client.post("/transactions", json={"amount": 0.05, "type": "debit"})

    resp = client.get("/balance")
    assert resp.json() == {"balance": 100.0}


def test_validation_error_envelope_is_consistent(client):
    resp = client.post("/transactions", json={"amount": -5, "type": "credit"})
    assert resp.status_code == 422
    body = resp.json()
    assert body["error"] == "validation_failed"
    assert isinstance(body["detail"], list)


def test_description_too_long_rejected(client):
    resp = client.post(
        "/transactions",
        json={"amount": 5, "type": "credit", "description": "x" * 501},
    )
    assert resp.status_code == 422


def test_health_reports_version(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert "version" in body


def test_request_id_is_echoed(client):
    resp = client.get("/health")
    assert resp.headers.get("x-request-id")


def test_supplied_request_id_is_preserved(client):
    resp = client.get("/health", headers={"x-request-id": "trace-123"})
    assert resp.headers.get("x-request-id") == "trace-123"
