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


def test_full_callback_flow(client, auth):
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
    cb = client.post(
        "/internal/transactions/txn_001/score", json=score_payload, headers=auth
    )
    assert cb.status_code == 200
    assert cb.json() == {"ok": True}

    get = client.get("/transactions/txn_001")
    assert get.status_code == 200
    body = get.json()
    assert body["status"] == "scored"
    assert body["score"] == 60
    assert body["risk_level"] == "medium"
    assert body["transaction"]["transaction_id"] == "txn_001"


def test_score_unknown_404(client, auth):
    score_payload = {
        "schema_version": "1.0",
        "transaction_id": "nope",
        "score": 10,
        "risk_level": "low",
        "reasons": [],
    }
    resp = client.post(
        "/internal/transactions/nope/score", json=score_payload, headers=auth
    )
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


def _score(tid="txn_001", score=0, risk="low", reasons=None):
    return {
        "schema_version": "1.0",
        "transaction_id": tid,
        "score": score,
        "risk_level": risk,
        "reasons": reasons or [],
    }


def test_internal_score_requires_token(client, auth):
    """A5-2: /internal requires the matching token (401 without, 200 with)."""
    client.post("/transactions", json=_valid_txn())
    # no token -> 401
    assert (
        client.post("/internal/transactions/txn_001/score", json=_score()).status_code
        == 401
    )
    # wrong token -> 401
    assert (
        client.post(
            "/internal/transactions/txn_001/score",
            json=_score(),
            headers={"X-Internal-Token": "wrong"},
        ).status_code
        == 401
    )
    # correct token -> 200
    assert (
        client.post(
            "/internal/transactions/txn_001/score", json=_score(), headers=auth
        ).status_code
        == 200
    )


def test_internal_score_fail_closed_when_unconfigured(client, monkeypatch, auth):
    """A5-17: when no server token is configured, /internal denies ALL callers
    (503), never fails open. This is the regression for the v1 'optional token'
    fix that left the endpoint wide open in the default config."""
    from app import routes

    monkeypatch.setattr(routes, "_INTERNAL_TOKEN", None)
    client.post("/transactions", json=_valid_txn())
    # even with a header, an unconfigured server denies (deny-by-default).
    assert (
        client.post(
            "/internal/transactions/txn_001/score", json=_score(), headers=auth
        ).status_code
        == 503
    )
    # and certainly without one.
    assert (
        client.post("/internal/transactions/txn_001/score", json=_score()).status_code
        == 503
    )


def test_score_poisoning_out_of_range_rejected(client, auth):
    """A5-13: an impossible score (>100) must be rejected, not persisted."""
    client.post("/transactions", json=_valid_txn())
    resp = client.post(
        "/internal/transactions/txn_001/score",
        json=_score(score=999, risk="low"),
        headers=auth,
    )
    assert resp.status_code == 422
    assert client.get("/transactions/txn_001").json()["status"] == "pending"


def test_score_invalid_risk_level_rejected(client, auth):
    """A5-13: a risk_level outside low|medium|high is rejected."""
    client.post("/transactions", json=_valid_txn())
    resp = client.post(
        "/internal/transactions/txn_001/score",
        json=_score(score=10, risk="banana"),
        headers=auth,
    )
    assert resp.status_code == 422


def test_score_band_mismatch_rejected(client, auth):
    """A5-13: a risk_level inconsistent with the score band is rejected
    (e.g. score 90 but risk_level 'low')."""
    client.post("/transactions", json=_valid_txn())
    resp = client.post(
        "/internal/transactions/txn_001/score",
        json=_score(score=90, risk="low"),
        headers=auth,
    )
    assert resp.status_code == 422
    assert client.get("/transactions/txn_001").json()["status"] == "pending"


def test_score_path_body_id_mismatch_rejected(client, auth):
    """A5-15: the transaction_id in the body must match the path."""
    client.post("/transactions", json=_valid_txn())
    resp = client.post(
        "/internal/transactions/txn_001/score",
        json=_score(tid="some_other_id", score=90, risk="high"),
        headers=auth,
    )
    assert resp.status_code == 422


def test_callback_idempotent_replay(client, auth):
    """A5-14: re-posting the SAME score is an idempotent no-op (200)."""
    client.post("/transactions", json=_valid_txn())
    first = client.post(
        "/internal/transactions/txn_001/score",
        json=_score(score=90, risk="high"),
        headers=auth,
    )
    assert first.status_code == 200
    replay = client.post(
        "/internal/transactions/txn_001/score",
        json=_score(score=90, risk="high"),
        headers=auth,
    )
    assert replay.status_code == 200


def test_callback_overwrite_rejected(client, auth):
    """A5-14: a CONFLICTING re-score of an already-scored txn is refused (409),
    so a high-risk score cannot be silently flipped to low."""
    client.post("/transactions", json=_valid_txn())
    client.post(
        "/internal/transactions/txn_001/score",
        json=_score(score=90, risk="high"),
        headers=auth,
    )
    overwrite = client.post(
        "/internal/transactions/txn_001/score",
        json=_score(score=0, risk="low"),
        headers=auth,
    )
    assert overwrite.status_code == 409
    body = client.get("/transactions/txn_001").json()
    assert body["score"] == 90 and body["risk_level"] == "high"


def test_concurrent_duplicate_create_no_500(client, monkeypatch):
    """A5-16: when the idempotency pre-check races (TOCTOU) and misses, the PK
    violation on commit must be caught and returned as 409, never a 500."""
    import app.routes as routes_mod
    import sqlalchemy.orm as orm
    from app.models import Transaction

    client.post("/transactions", json=_valid_txn())

    real_get = orm.Session.get

    def racing_get(self, entity, ident, *a, **k):
        if entity is Transaction:
            return None  # simulate the row not being visible yet
        return real_get(self, entity, ident, *a, **k)

    monkeypatch.setattr(orm.Session, "get", racing_get)
    resp = client.post("/transactions", json=_valid_txn())
    assert resp.status_code == 409
