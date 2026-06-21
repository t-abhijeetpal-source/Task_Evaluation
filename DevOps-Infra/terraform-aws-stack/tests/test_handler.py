"""Unit tests for the Lambda handler.

These run with no AWS access: a small in-memory fake stands in for the S3
client, so the tests exercise the handler's real control flow (record visit,
count visits, error handling, routing) deterministically.
"""

import importlib
import json
import sys
from pathlib import Path

import pytest

# Make src/handler.py importable.
SRC = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC))


class FakeS3:
    """Minimal in-memory stand-in for the boto3 S3 client."""

    def __init__(self):
        self.objects = {}

    def put_object(self, Bucket, Key, Body, ContentType=None):  # noqa: N803
        self.objects[(Bucket, Key)] = Body
        return {}

    def list_objects_v2(self, Bucket, Prefix="", ContinuationToken=None):  # noqa: N803
        keys = [k for (b, k) in self.objects if b == Bucket and k.startswith(Prefix)]
        return {"KeyCount": len(keys), "IsTruncated": False}


@pytest.fixture
def handler_mod(monkeypatch):
    monkeypatch.setenv("BUCKET_NAME", "test-bucket")
    monkeypatch.setenv("LOG_LEVEL", "INFO")
    mod = importlib.import_module("handler")
    importlib.reload(mod)
    fake = FakeS3()
    monkeypatch.setattr(mod, "_s3_client", fake)
    monkeypatch.setattr(mod, "_s3", lambda: fake)
    return mod, fake


def _body(resp):
    return json.loads(resp["body"])


def test_hello_records_visit_and_returns_count(handler_mod):
    mod, fake = handler_mod
    resp = mod.handler({"rawPath": "/hello"}, None)
    assert resp["statusCode"] == 200
    body = _body(resp)
    assert body["message"] == "hello from lambda"
    assert body["bucket"] == "test-bucket"
    assert body["visit_count"] == 1
    assert body["visit_key"].startswith("visits/")
    # The object was actually written to (the fake) S3.
    assert (("test-bucket", body["visit_key"]) in fake.objects)


def test_visit_count_increments(handler_mod):
    mod, _ = handler_mod
    mod.handler({"rawPath": "/hello"}, None)
    resp = mod.handler({"rawPath": "/hello"}, None)
    assert _body(resp)["visit_count"] == 2


def test_unknown_route_returns_404(handler_mod):
    mod, _ = handler_mod
    resp = mod.handler({"rawPath": "/nope"}, None)
    assert resp["statusCode"] == 404
    assert _body(resp)["error"] == "not found"


def test_missing_bucket_returns_500(handler_mod, monkeypatch):
    mod, _ = handler_mod
    monkeypatch.delenv("BUCKET_NAME", raising=False)
    resp = mod.handler({"rawPath": "/hello"}, None)
    assert resp["statusCode"] == 500


def test_storage_error_returns_502(handler_mod):
    mod, fake = handler_mod

    def boom(*a, **k):
        raise RuntimeError("s3 down")

    fake.put_object = boom
    resp = mod.handler({"rawPath": "/hello"}, None)
    assert resp["statusCode"] == 502
    assert _body(resp)["error"] == "storage error"


def test_response_shape_is_apigw_v2(handler_mod):
    mod, _ = handler_mod
    resp = mod.handler({"rawPath": "/hello"}, None)
    assert set(["statusCode", "headers", "body"]).issubset(resp.keys())
    assert resp["headers"]["content-type"] == "application/json"
