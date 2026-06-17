import json
import os


def _valid_txn():
    return {
        "schema_version": "1.0",
        "transaction_id": "txn_001",
        "user_id": "user_123",
        "amount": 5000,
        "country": "IN",
        "merchant_category": "electronics",
        "timestamp": "2026-06-17T10:00:00Z",
    }


def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_post_valid_creates_queue_file(client, queue_dir):
    txn = _valid_txn()
    resp = client.post("/transactions", json=txn)

    assert resp.status_code == 201
    body = resp.json()
    assert body["transaction_id"] == "txn_001"
    assert body["status"] == "pending"
    assert body["request_id"]

    queue_path = os.path.join(queue_dir, "txn_001.json")
    assert os.path.exists(queue_path)

    with open(queue_path, encoding="utf-8") as f:
        written = json.load(f)
    assert written["transaction_id"] == "txn_001"
    assert written["user_id"] == "user_123"
    assert written["amount"] == 5000
    assert written["country"] == "IN"
    assert written["merchant_category"] == "electronics"
    assert written["timestamp"] == "2026-06-17T10:00:00Z"


def test_post_non_positive_amount(client):
    txn = _valid_txn()
    txn["amount"] = 0
    resp = client.post("/transactions", json=txn)
    assert resp.status_code == 422
    assert resp.json() == {"error": "amount must be positive"}

    txn["amount"] = -10
    resp = client.post("/transactions", json=txn)
    assert resp.status_code == 422
    assert resp.json() == {"error": "amount must be positive"}


def test_post_missing_field(client):
    txn = _valid_txn()
    del txn["user_id"]
    resp = client.post("/transactions", json=txn)
    assert resp.status_code == 422


def test_get_unknown_404(client):
    resp = client.get("/transactions/does_not_exist")
    assert resp.status_code == 404


def test_full_callback_flow(client):
    txn = _valid_txn()
    create = client.post("/transactions", json=txn)
    assert create.status_code == 201

    score_payload = {
        "schema_version": "1.0",
        "transaction_id": "txn_001",
        "score": 60,
        "risk_level": "medium",
        "reasons": ["high_amount", "foreign_country"],
    }
    cb = client.post("/internal/transactions/txn_001/score", json=score_payload)
    assert cb.status_code == 200
    assert cb.json() == {"ok": True}

    get = client.get("/transactions/txn_001")
    assert get.status_code == 200
    body = get.json()
    assert body["status"] == "scored"
    assert body["score"] == 60
    assert body["risk_level"] == "medium"
    assert body["transaction"]["transaction_id"] == "txn_001"


def test_score_unknown_404(client):
    score_payload = {
        "schema_version": "1.0",
        "transaction_id": "nope",
        "score": 10,
        "risk_level": "low",
        "reasons": [],
    }
    resp = client.post("/internal/transactions/nope/score", json=score_payload)
    assert resp.status_code == 404


# --- A5 hardening regression tests (path traversal, idempotency, internal auth) ---

def test_path_traversal_transaction_id_rejected(client, queue_dir):
    """A5-1: a traversal id must be rejected (422), not written outside queue/."""
    txn = _valid_txn()
    txn["transaction_id"] = "../A5_PWNED"
    resp = client.post("/transactions", json=txn)
    assert resp.status_code == 422
    # nothing escaped the queue dir
    parent = os.path.dirname(os.path.abspath(queue_dir))
    assert not os.path.exists(os.path.join(parent, "A5_PWNED.json"))


def test_duplicate_transaction_id_returns_409(client):
    """A5-3: a duplicate id is idempotent-safe (409), never a 500."""
    txn = _valid_txn()
    first = client.post("/transactions", json=txn)
    assert first.status_code == 201
    second = client.post("/transactions", json=txn)
    assert second.status_code == 409


def test_internal_score_requires_token_when_configured(client, monkeypatch):
    """A5-2: when A3_INTERNAL_TOKEN is set, /internal requires the matching header."""
    from app import routes
    monkeypatch.setattr(routes, "_INTERNAL_TOKEN", "s3cret")
    client.post("/transactions", json=_valid_txn())
    score = {
        "schema_version": "1.0",
        "transaction_id": "txn_001",
        "score": 0,
        "risk_level": "low",
        "reasons": [],
    }
    # no token -> 401
    assert client.post("/internal/transactions/txn_001/score", json=score).status_code == 401
    # correct token -> 200
    ok = client.post(
        "/internal/transactions/txn_001/score",
        json=score,
        headers={"X-Internal-Token": "s3cret"},
    )
    assert ok.status_code == 200
