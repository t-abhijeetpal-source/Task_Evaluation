"""API-level unit tests for the Expense Tracker endpoints.

Each test exercises a single endpoint contract via the TestClient.
The autouse `_reset_database` fixture (conftest.py) gives every test a
fresh, empty schema.
"""


def test_health_returns_ok(client):
    """GET /api/health -> 200 {"status": "ok"}."""
    resp = client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_create_expense_returns_201_and_body(client):
    """POST /api/expenses creates an expense and echoes a complete body."""
    payload = {"amount": 42.5, "category": "food", "note": "lunch"}
    resp = client.post("/api/expenses", json=payload)

    assert resp.status_code == 201
    body = resp.json()
    assert body["id"] is not None
    assert body["amount"] == 42.5
    assert body["category"] == "food"
    assert body["note"] == "lunch"
    # created_at is server-generated and must be present.
    assert "created_at" in body and body["created_at"]


def test_create_expense_without_note_defaults_to_empty(client):
    """note is optional and defaults to an empty string."""
    resp = client.post(
        "/api/expenses", json={"amount": 10, "category": "transport"}
    )
    assert resp.status_code == 201
    assert resp.json()["note"] == ""


def test_create_expense_rejects_zero_amount(client):
    """amount == 0 is invalid -> 422 with the domain error message."""
    resp = client.post(
        "/api/expenses", json={"amount": 0, "category": "food"}
    )
    assert resp.status_code == 422
    assert resp.json() == {"error": "amount must be positive"}


def test_create_expense_rejects_negative_amount(client):
    """amount < 0 is invalid -> 422 with the domain error message."""
    resp = client.post(
        "/api/expenses", json={"amount": -5.0, "category": "food"}
    )
    assert resp.status_code == 422
    assert resp.json() == {"error": "amount must be positive"}


def test_create_expense_rejects_missing_amount(client):
    """Missing required field 'amount' -> 422 pydantic validation error."""
    resp = client.post("/api/expenses", json={"category": "food"})
    assert resp.status_code == 422


def test_create_expense_rejects_missing_category(client):
    """Missing required field 'category' -> 422 pydantic validation error."""
    resp = client.post("/api/expenses", json={"amount": 12.0})
    assert resp.status_code == 422


def test_create_expense_rejects_bad_amount_type(client):
    """Non-numeric 'amount' -> 422 pydantic validation error."""
    resp = client.post(
        "/api/expenses", json={"amount": "not-a-number", "category": "food"}
    )
    assert resp.status_code == 422


def test_list_expenses_empty(client):
    """With no data the list endpoint returns an empty array."""
    resp = client.get("/api/expenses")
    assert resp.status_code == 200
    assert resp.json() == []


def test_list_expenses_newest_first(client):
    """GET /api/expenses returns expenses newest-first (descending id)."""
    client.post("/api/expenses", json={"amount": 1, "category": "a"})
    client.post("/api/expenses", json={"amount": 2, "category": "b"})
    client.post("/api/expenses", json={"amount": 3, "category": "c"})

    resp = client.get("/api/expenses")
    assert resp.status_code == 200
    body = resp.json()
    assert len(body) == 3
    # Most recently created (amount 3) must be first.
    assert [row["amount"] for row in body] == [3, 2, 1]
    assert [row["category"] for row in body] == ["c", "b", "a"]


def test_summary_empty(client):
    """Summary over an empty DB: zero total/count, empty by_category."""
    resp = client.get("/api/summary")
    assert resp.status_code == 200
    assert resp.json() == {"total": 0, "count": 0, "by_category": {}}


def test_summary_computes_totals_and_by_category(client):
    """Summary aggregates total, count, and per-category sums correctly."""
    # food: 10 + 5 = 15 ; transport: 20 ; total = 35 over 3 records.
    client.post("/api/expenses", json={"amount": 10, "category": "food"})
    client.post("/api/expenses", json={"amount": 20, "category": "transport"})
    client.post("/api/expenses", json={"amount": 5, "category": "food"})

    resp = client.get("/api/summary")
    assert resp.status_code == 200
    body = resp.json()
    assert body["count"] == 3
    assert body["total"] == 35
    assert body["by_category"] == {"food": 15, "transport": 20}
