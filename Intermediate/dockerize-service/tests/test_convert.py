"""Service tests for the dockerized FastAPI currency conversion service.

Ported from the I4 baseline (polyglot-currency-pair/fastapi-service) and extended
with a same-currency (rate=1.0) case. Uses TestClient, so no live server is needed.
"""

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


# --- Test 6: same-currency conversion uses rate 1.0 -----------------------
def test_same_currency_conversion(client):
    resp = client.post("/convert", json={"amount": 100, "from": "USD", "to": "USD"})
    assert resp.status_code == 200
    assert resp.json() == {"converted_amount": 100, "from": "USD", "to": "USD"}


# --- Decimal validation: non-finite amounts rejected at the schema (422) ---
def test_infinity_amount_rejected_as_number(client):
    # Python's json accepts the bare `Infinity` token; the Decimal schema rejects it.
    resp = client.post(
        "/convert",
        content='{"amount": Infinity, "from": "USD", "to": "INR"}',
        headers={"Content-Type": "application/json"},
    )
    assert resp.status_code == 422
    assert "detail" in resp.json()


def test_infinity_amount_rejected_as_string(client):
    resp = client.post("/convert", json={"amount": "Infinity", "from": "USD", "to": "INR"})
    assert resp.status_code == 422
    assert "detail" in resp.json()


def test_nan_amount_rejected(client):
    resp = client.post("/convert", json={"amount": "NaN", "from": "USD", "to": "INR"})
    assert resp.status_code == 422
    assert "detail" in resp.json()


def test_absurdly_large_amount_rejected(client):
    # 1e308 exceeds the 20-significant-digit bound -> structural 422.
    resp = client.post("/convert", json={"amount": 1e308, "from": "USD", "to": "INR"})
    assert resp.status_code == 422
    assert "detail" in resp.json()


# --- Decimal precision: small/large valid amounts -------------------------
def test_small_decimal_precision(client):
    # 0.01 USD -> INR = 0.01 * 83 = 0.83
    resp = client.post("/convert", json={"amount": "0.01", "from": "USD", "to": "INR"})
    assert resp.status_code == 200
    assert resp.json()["converted_amount"] == 0.83


def test_large_in_bounds_amount(client):
    # 1_000_000_000 USD -> INR = 83_000_000_000 (integral, within bounds)
    resp = client.post("/convert", json={"amount": 1000000000, "from": "USD", "to": "INR"})
    assert resp.status_code == 200
    assert resp.json()["converted_amount"] == 83000000000
