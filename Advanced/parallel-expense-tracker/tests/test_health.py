"""Deep health-check tests.

The health endpoint must reflect database reachability, not just process
liveness — a shallow 200 lets an orchestrator send traffic to an instance whose
datastore is dead.
"""

from app.database import get_db
from app.main import app


def test_health_ok_when_db_reachable(client):
    resp = client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_health_returns_503_when_db_unreachable(client):
    """If the DB round-trip fails, health must report 503, not 200."""

    class _BrokenSession:
        def execute(self, *args, **kwargs):
            raise RuntimeError("simulated database outage")

    def _broken_db():
        yield _BrokenSession()

    app.dependency_overrides[get_db] = _broken_db
    try:
        resp = client.get("/api/health")
        assert resp.status_code == 503
        assert resp.json()["status"] == "unavailable"
    finally:
        app.dependency_overrides.pop(get_db, None)
