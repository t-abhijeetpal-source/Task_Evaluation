"""Endpoint behaviour for the D2 Jobs API (DB faked)."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager

import app.main as main_module
import psycopg
import pytest
from fastapi.testclient import TestClient
from tests.conftest import JobStore


def test_health_ok(client: TestClient) -> None:
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok", "db": "up"}


def test_health_degraded_on_db_error(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    @contextmanager
    def boom() -> Iterator[object]:
        raise psycopg.OperationalError("connection refused")
        yield  # pragma: no cover

    monkeypatch.setattr(main_module, "db_connection", boom)
    r = client.get("/health")
    assert r.status_code == 503
    body = r.json()
    assert body["status"] == "degraded"
    assert body["db"] == "down"
    assert "connection refused" in body["error"]


def test_create_job_returns_pending(client: TestClient) -> None:
    r = client.post("/jobs", json={"payload": "hello-d2"})
    assert r.status_code == 201
    body = r.json()
    assert body == {"id": 1, "payload": "hello-d2", "status": "pending"}


def test_create_job_validation_error(client: TestClient) -> None:
    r = client.post("/jobs", json={})
    assert r.status_code == 422


def test_get_job_found(client: TestClient, store: JobStore) -> None:
    store.add_done("hello-d2", "HELLO-D2")
    r = client.get("/jobs/1")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "done"
    assert body["result"] == "HELLO-D2"
    assert body["processed_by"] == "worker-1"


def test_get_job_not_found(client: TestClient) -> None:
    r = client.get("/jobs/999")
    assert r.status_code == 404
    assert r.json()["detail"] == "job not found"


def test_list_jobs_orders_newest_first(client: TestClient, store: JobStore) -> None:
    store.insert("first")
    store.insert("second")
    r = client.get("/jobs")
    assert r.status_code == 200
    ids = [j["id"] for j in r.json()]
    assert ids == [2, 1]


def test_create_then_get_roundtrip(client: TestClient) -> None:
    created = client.post("/jobs", json={"payload": "roundtrip"}).json()
    fetched = client.get(f"/jobs/{created['id']}").json()
    assert fetched["id"] == created["id"]
    assert fetched["payload"] == "roundtrip"
    assert fetched["status"] == "pending"
