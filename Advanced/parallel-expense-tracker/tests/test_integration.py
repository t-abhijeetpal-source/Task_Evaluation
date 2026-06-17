"""Full-stack-ish integration tests driven through the TestClient.

These cross the boundaries the unit tests treat in isolation: the static
frontend mount at "/" and a write-then-read round trip across the
create / list / summary endpoints sharing the same database.
"""


def test_root_serves_html_page(client):
    """GET / serves the static SPA shell as HTML.

    The StaticFiles mount (html=True) returns static/index.html. We assert a
    successful HTML response that looks like the app shell rather than
    pinning exact markup, so the test survives minor frontend tweaks.
    """
    resp = client.get("/")
    assert resp.status_code == 200

    content_type = resp.headers.get("content-type", "")
    assert "text/html" in content_type

    html = resp.text.lower()
    # The page should contain recognizable app shell markup.
    assert "<html" in html
    assert ("<form" in html) or ("<title" in html) or ("expense" in html)


def test_create_then_appears_in_list(client):
    """A created expense round-trips into the list endpoint."""
    create = client.post(
        "/api/expenses",
        json={"amount": 99.0, "category": "books", "note": "novel"},
    )
    assert create.status_code == 201
    created_id = create.json()["id"]

    listing = client.get("/api/expenses")
    assert listing.status_code == 200
    rows = listing.json()
    assert any(row["id"] == created_id for row in rows)

    match = next(row for row in rows if row["id"] == created_id)
    assert match["amount"] == 99.0
    assert match["category"] == "books"
    assert match["note"] == "novel"


def test_create_then_reflected_in_summary(client):
    """Created expenses are reflected in the aggregated summary."""
    client.post("/api/expenses", json={"amount": 30, "category": "food"})
    client.post("/api/expenses", json={"amount": 70, "category": "rent"})

    summary = client.get("/api/summary")
    assert summary.status_code == 200
    body = summary.json()
    assert body["count"] == 2
    assert body["total"] == 100
    assert body["by_category"] == {"food": 30, "rent": 70}


def test_full_round_trip_create_list_summary(client):
    """End-to-end: create several, verify newest-first list and summary."""
    client.post("/api/expenses", json={"amount": 15, "category": "food"})
    client.post("/api/expenses", json={"amount": 25, "category": "food"})
    client.post("/api/expenses", json={"amount": 60, "category": "travel"})

    rows = client.get("/api/expenses").json()
    assert [r["amount"] for r in rows] == [60, 25, 15]  # newest first

    body = client.get("/api/summary").json()
    assert body["count"] == 3
    assert body["total"] == 100
    assert body["by_category"] == {"food": 40, "travel": 60}
