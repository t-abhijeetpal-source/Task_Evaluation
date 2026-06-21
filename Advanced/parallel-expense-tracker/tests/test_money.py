"""Regression tests for money correctness.

These pin the behaviours that a naive ``float`` pipeline got wrong:
  * non-finite amounts (NaN / +-Infinity) must be rejected with 422, never 500;
  * money must aggregate exactly (no 0.1 + 0.2 == 0.30000000000000004);
  * sub-cent and out-of-range magnitudes are rejected.
"""

import json

HEADERS = {"Content-Type": "application/json"}


def _post_raw(client, raw_body: str):
    """POST a raw JSON string so we can send literals httpx would refuse."""
    return client.post("/api/expenses", content=raw_body, headers=HEADERS)


def test_nan_amount_returns_422_not_500(client):
    """A JSON ``NaN`` literal must be rejected with 422 (regression: was 500)."""
    resp = _post_raw(client, '{"amount": NaN, "category": "food"}')
    assert resp.status_code == 422
    # The body must be JSON-serializable and must NOT echo the raw NaN.
    body = resp.json()
    assert "nan" not in json.dumps(body).lower()


def test_positive_infinity_returns_422(client):
    resp = _post_raw(client, '{"amount": Infinity, "category": "food"}')
    assert resp.status_code == 422


def test_negative_infinity_returns_422(client):
    resp = _post_raw(client, '{"amount": -Infinity, "category": "food"}')
    assert resp.status_code == 422


def test_sub_cent_amount_rejected(client):
    """More than 2 decimal places is sub-cent precision we do not store."""
    resp = client.post(
        "/api/expenses", json={"amount": 12.555, "category": "food"}
    )
    assert resp.status_code == 422


def test_absurdly_large_amount_rejected(client):
    """Out-of-range magnitudes are rejected before they reach the DB."""
    resp = client.post(
        "/api/expenses", json={"amount": 1e20, "category": "food"}
    )
    assert resp.status_code == 422


def test_classic_float_sum_is_exact(client):
    """0.1 + 0.2 must equal exactly 0.30 in the summary, not 0.30000000000004."""
    client.post("/api/expenses", json={"amount": 0.1, "category": "p"})
    client.post("/api/expenses", json={"amount": 0.2, "category": "p"})

    body = client.get("/api/summary").json()
    assert body["by_category"]["p"] == 0.30
    assert body["total"] == 0.30


def test_many_small_amounts_aggregate_exactly(client):
    """Summing 100 x 0.01 must be exactly 1.00 (integer-cent aggregation)."""
    for _ in range(100):
        client.post("/api/expenses", json={"amount": 0.01, "category": "c"})

    body = client.get("/api/summary").json()
    assert body["count"] == 100
    assert body["total"] == 1.00
    assert body["by_category"]["c"] == 1.00


def test_amount_string_input_accepted(client):
    """Amount may arrive as a numeric string and round-trips precisely."""
    resp = client.post(
        "/api/expenses", json={"amount": "42.50", "category": "food"}
    )
    assert resp.status_code == 201
    assert resp.json()["amount"] == 42.5


def test_two_decimal_amount_stored_exactly(client):
    """A 2-dp amount round-trips without drift."""
    resp = client.post(
        "/api/expenses", json={"amount": 19.99, "category": "food"}
    )
    assert resp.status_code == 201
    assert resp.json()["amount"] == 19.99
