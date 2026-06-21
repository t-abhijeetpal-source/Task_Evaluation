"""Lambda handler behind API Gateway (HTTP API, payload format v2.0).

Routes:
  GET /hello   -> records a visit object in S3 and returns a greeting plus the
                  running visit count (read back from the bucket).

The handler actually exercises the S3 permissions the IAM role grants
(PutObject / ListBucket), so the infrastructure and the code agree.
"""

from __future__ import annotations

import json
import logging
import os
import uuid
from datetime import datetime, timezone

import boto3

logger = logging.getLogger()
logger.setLevel(os.environ.get("LOG_LEVEL", "INFO"))

_VISITS_PREFIX = "visits/"

# Reuse the client across warm invocations (created lazily so unit tests can
# patch boto3 / inject a stub before the first call).
_s3_client = None


def _s3():
    global _s3_client
    if _s3_client is None:
        _s3_client = boto3.client("s3")
    return _s3_client


def _response(status: int, body: dict) -> dict:
    return {
        "statusCode": status,
        "headers": {"content-type": "application/json"},
        "body": json.dumps(body),
    }


def _record_visit(bucket: str) -> str:
    """Write a visit marker object and return its key."""
    now = datetime.now(timezone.utc)
    key = f"{_VISITS_PREFIX}{now:%Y/%m/%d}/{uuid.uuid4().hex}.json"
    _s3().put_object(
        Bucket=bucket,
        Key=key,
        Body=json.dumps({"visited_at": now.isoformat()}).encode("utf-8"),
        ContentType="application/json",
    )
    return key


def _count_visits(bucket: str) -> int:
    """Count visit objects currently stored (paginated)."""
    total = 0
    token = None
    while True:
        kwargs = {"Bucket": bucket, "Prefix": _VISITS_PREFIX}
        if token:
            kwargs["ContinuationToken"] = token
        page = _s3().list_objects_v2(**kwargs)
        total += page.get("KeyCount", 0)
        if not page.get("IsTruncated"):
            break
        token = page.get("NextContinuationToken")
    return total


def handler(event, context):
    route = (event or {}).get("rawPath", "/")
    bucket = os.environ.get("BUCKET_NAME")

    if not bucket:
        logger.error("BUCKET_NAME is not configured")
        return _response(500, {"error": "bucket not configured"})

    if route != "/hello":
        return _response(404, {"error": "not found", "path": route})

    try:
        key = _record_visit(bucket)
        count = _count_visits(bucket)
    except Exception:  # surface as 500 rather than leaking a stack trace
        logger.exception("failed to record/count visit in bucket %s", bucket)
        return _response(502, {"error": "storage error"})

    return _response(
        200,
        {
            "message": "hello from lambda",
            "bucket": bucket,
            "visit_key": key,
            "visit_count": count,
        },
    )
