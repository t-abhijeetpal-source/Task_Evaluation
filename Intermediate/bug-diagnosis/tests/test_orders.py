"""Tests for the orders service, encoding the SPEC.md rules.

`test_bulk_discount_applies_at_threshold_of_10` is the reproduction test for the
seeded bug (boundary at qty == 10).
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.schemas import Item
from app.services import calculate_total
from app.storage import store


@pytest.fixture(autouse=True)
def reset_store():
    store.clear()
    yield
    store.clear()


@pytest.fixture
def client():
    return TestClient(app)


# --- No discount below threshold (qty 9) ----------------------------------
def test_no_discount_below_threshold():
    assert calculate_total([Item(price=100, qty=9)]) == 900.0


# --- REPRODUCTION: discount must apply at exactly qty == 10 ---------------
def test_bulk_discount_applies_at_threshold_of_10():
    # SPEC rule 3: qty >= 10 qualifies. 10 * 100 = 1000, minus 10% = 900.
    assert calculate_total([Item(price=100, qty=10)]) == 900.0


# --- Discount above threshold (qty 11) ------------------------------------
def test_discount_above_threshold():
    assert calculate_total([Item(price=100, qty=11)]) == 990.0


# --- Mixed order ----------------------------------------------------------
def test_mixed_order_total():
    # 100*9 = 900 (no disc) + 50*10 = 500 -> 450 (disc) = 1350
    items = [Item(price=100, qty=9), Item(price=50, qty=10)]
    assert calculate_total(items) == 1350.0


# --- API integration: total endpoint reflects the discount ----------------
def test_api_order_total_at_threshold(client):
    created = client.post("/orders", json={"items": [{"price": 100, "qty": 10}]})
    assert created.status_code == 201
    oid = created.json()["id"]
    total = client.get(f"/orders/{oid}/total")
    assert total.status_code == 200
    assert total.json() == {"id": oid, "total": 900.0}
