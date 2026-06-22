"""Endpoint tests for the D4 workload — run before building the image."""

import importlib

import pytest
from fastapi.testclient import TestClient


def test_health(client: TestClient) -> None:
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_ready(client: TestClient) -> None:
    r = client.get("/ready")
    assert r.status_code == 200
    assert r.json() == {"status": "ready"}


def test_root_surfaces_config(client: TestClient) -> None:
    r = client.get("/")
    assert r.status_code == 200
    body = r.json()
    assert body["service"] == "d4-sample"
    # env/greeting/version come from env (ConfigMap in-cluster, defaults locally).
    assert {"env", "greeting", "version"} <= body.keys()


def test_add_endpoint(client: TestClient) -> None:
    r = client.get("/add", params={"a": 2, "b": 3})
    assert r.status_code == 200
    assert r.json() == {"a": 2, "b": 3, "sum": 5, "even": False}


def test_add_endpoint_even_sum(client: TestClient) -> None:
    r = client.get("/add", params={"a": 2, "b": 2})
    assert r.status_code == 200
    assert r.json() == {"a": 2, "b": 2, "sum": 4, "even": True}


def test_add_validation_rejects_non_int(client: TestClient) -> None:
    r = client.get("/add", params={"a": "x", "b": 3})
    assert r.status_code == 422


def test_add_validation_requires_both_params(client: TestClient) -> None:
    r = client.get("/add", params={"a": 2})
    assert r.status_code == 422


def test_configmap_injection_observable_over_http(monkeypatch: pytest.MonkeyPatch) -> None:
    """Re-import the app with ConfigMap-style env set and assert it surfaces at GET /.

    This is the unit-level mirror of the in-cluster proof: the Deployment's
    ``envFrom: configMapRef: d4-config`` injects these vars, and GET / echoes
    them back. Here we set them in the environment and reload the module so the
    module-level reads pick them up — proving the wiring, not just the defaults.
    """
    monkeypatch.setenv("APP_ENV", "kind-local")
    monkeypatch.setenv("APP_GREETING", "hello from D4 on Kubernetes")
    monkeypatch.setenv("APP_VERSION", "9.9.9")

    import app.main as main

    main = importlib.reload(main)
    try:
        with TestClient(main.app) as client:
            body = client.get("/").json()
        assert body["env"] == "kind-local"
        assert body["greeting"] == "hello from D4 on Kubernetes"
        assert body["version"] == "9.9.9"
    finally:
        # Restore the module to its default-env state for the rest of the suite.
        monkeypatch.undo()
        importlib.reload(main)
