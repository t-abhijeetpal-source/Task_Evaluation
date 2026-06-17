"""Service tests for the FastAPI currency conversion service."""

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    return TestClient(app)


# --- Test 1: valid conversion USD -> INR ----------------------------------
def test_valid_conversion_usd_to_inr(client):
    resp = client.post("/convert", json={"amount": 100, "from": "USD", "to": "INR"})
    assert resp.status_code == 200
    assert resp.json() == {"converted_amount": 8300, "from": "USD", "to": "INR"}


# --- Test 2: unsupported currency -> 400 ----------------------------------
def test_unsupported_currency(client):
    resp = client.post("/convert", json={"amount": 100, "from": "USD", "to": "GBP"})
    assert resp.status_code == 400
    assert resp.json() == {"error": "Unsupported currency"}


# --- Test 3: negative / non-positive amount -> 422 ------------------------
def test_negative_amount(client):
    resp = client.post("/convert", json={"amount": -5, "from": "USD", "to": "INR"})
    assert resp.status_code == 422
    assert resp.json() == {"error": "Amount must be positive"}


def test_zero_amount(client):
    resp = client.post("/convert", json={"amount": 0, "from": "USD", "to": "INR"})
    assert resp.status_code == 422
    assert resp.json() == {"error": "Amount must be positive"}


# --- Test 4: malformed request -> 422 with validation details -------------
def test_malformed_request_missing_field(client):
    resp = client.post("/convert", json={"from": "USD", "to": "INR"})  # no amount
    assert resp.status_code == 422
    # FastAPI's default validation error envelope.
    assert "detail" in resp.json()


def test_malformed_request_non_numeric_amount(client):
    resp = client.post("/convert", json={"amount": "abc", "from": "USD", "to": "INR"})
    assert resp.status_code == 422
    assert "detail" in resp.json()


# --- Test 5: successful API response structure ----------------------------
def test_response_structure(client):
    resp = client.post("/convert", json={"amount": 50, "from": "EUR", "to": "USD"})
    assert resp.status_code == 200
    body = resp.json()
    assert set(body.keys()) == {"converted_amount", "from", "to"}
    assert body["from"] == "EUR"
    assert body["to"] == "USD"
    assert body["converted_amount"] == 54  # 50 * 1.08 = 54.0 -> 54
