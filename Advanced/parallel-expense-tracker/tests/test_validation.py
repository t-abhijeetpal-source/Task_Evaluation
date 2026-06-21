"""Input-validation, normalization, and pagination tests."""


def test_category_is_trimmed_and_lowercased(client):
    resp = client.post(
        "/api/expenses", json={"amount": 5, "category": "  FOOD  "}
    )
    assert resp.status_code == 201
    assert resp.json()["category"] == "food"


def test_empty_category_rejected(client):
    resp = client.post(
        "/api/expenses", json={"amount": 5, "category": "   "}
    )
    assert resp.status_code == 422


def test_overlong_category_rejected(client):
    resp = client.post(
        "/api/expenses", json={"amount": 5, "category": "x" * 100}
    )
    assert resp.status_code == 422


def test_note_is_trimmed(client):
    resp = client.post(
        "/api/expenses",
        json={"amount": 5, "category": "food", "note": "  hello  "},
    )
    assert resp.status_code == 201
    assert resp.json()["note"] == "hello"


def test_overlong_note_rejected(client):
    resp = client.post(
        "/api/expenses",
        json={"amount": 5, "category": "food", "note": "n" * 300},
    )
    assert resp.status_code == 422


def test_list_respects_limit(client):
    for i in range(5):
        client.post("/api/expenses", json={"amount": i + 1, "category": "c"})
    rows = client.get("/api/expenses?limit=2").json()
    assert len(rows) == 2
    # Newest-first: the two highest amounts.
    assert [r["amount"] for r in rows] == [5, 4]


def test_list_respects_offset(client):
    for i in range(5):
        client.post("/api/expenses", json={"amount": i + 1, "category": "c"})
    rows = client.get("/api/expenses?limit=2&offset=2").json()
    assert [r["amount"] for r in rows] == [3, 2]


def test_list_rejects_out_of_range_limit(client):
    assert client.get("/api/expenses?limit=0").status_code == 422
    assert client.get("/api/expenses?limit=5000").status_code == 422


def test_list_rejects_negative_offset(client):
    assert client.get("/api/expenses?offset=-1").status_code == 422
