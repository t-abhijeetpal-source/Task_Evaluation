"""Shared contract conformance — B4 must satisfy Basics/fixtures/transaction-vectors.json."""

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.routes import get_store
from app.storage import InMemoryStorage

VECTORS = json.loads(
    (Path(__file__).resolve().parents[2] / "fixtures" / "transaction-vectors.json").read_text()
)


@pytest.fixture
def store():
    return InMemoryStorage()


@pytest.fixture
def client(store):
    app.dependency_overrides[get_store] = lambda: store
    yield TestClient(app)
    app.dependency_overrides.clear()


def _body(raw: dict) -> dict:
    body = dict(raw)
    desc = body.get("description")
    if desc == "REPEAT_X_501":
        body["description"] = "x" * 501
    return body


def _run_steps(client: TestClient, steps: list) -> None:
    for step in steps:
        method = step["method"].upper()
        path = step["path"]
        body = _body(step.get("body", {}))
        headers = step.get("headers") or {}

        if method == "GET":
            resp = client.get(path, headers=headers)
        elif method == "POST":
            resp = client.post(path, json=body, headers=headers)
        else:
            raise AssertionError(f"unsupported method: {method}")

        assert resp.status_code == step["expectStatus"], (
            f"{method} {path}: expected {step['expectStatus']}, got {resp.status_code}: {resp.text}"
        )

        if "expectBody" in step:
            assert resp.json() == step["expectBody"]

        if "expectLength" in step:
            assert len(resp.json()) == step["expectLength"]

        if "expectFirst" in step:
            for key, value in step["expectFirst"].items():
                assert resp.json()[0][key] == value

        if "expectSecond" in step:
            for key, value in step["expectSecond"].items():
                assert resp.json()[1][key] == value

        if "expectBodyKeys" in step:
            for key in step["expectBodyKeys"]:
                assert key in resp.json()

        if "expectHeader" in step:
            for key, value in step["expectHeader"].items():
                assert resp.headers.get(key) == value


@pytest.mark.parametrize("scenario", VECTORS["scenarios"], ids=lambda s: s["name"])
def test_contract_scenario(client, scenario):
    _run_steps(client, scenario["steps"])


@pytest.mark.parametrize(
    "case", VECTORS["validationFailures"], ids=lambda c: c["name"]
)
def test_contract_validation_failure(client, case):
    resp = client.post("/transactions", json=_body(case["body"]))
    assert resp.status_code == case["expectStatus"]


@pytest.mark.parametrize(
    "case", VECTORS["observability"], ids=lambda c: c["name"]
)
def test_contract_observability(client, case):
    headers = case.get("headers") or {}
    resp = client.request(case["method"], case["path"], headers=headers)
    assert resp.status_code == case["expectStatus"]

    if "expectBodyKeys" in case:
        for key in case["expectBodyKeys"]:
            assert key in resp.json()

    if "expectHeader" in case:
        for key, value in case["expectHeader"].items():
            assert resp.headers.get(key) == value
