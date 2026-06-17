"""Minimal Lambda handler behind API Gateway (HTTP API, payload format v2.0)."""
import json
import os


def handler(event, context):
    bucket = os.environ.get("BUCKET_NAME", "unknown")
    return {
        "statusCode": 200,
        "headers": {"content-type": "application/json"},
        "body": json.dumps({"message": "hello from lambda", "bucket": bucket}),
    }
