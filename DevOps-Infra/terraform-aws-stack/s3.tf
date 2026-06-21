# ===========================================================================
# S3 — data bucket (CMK-encrypted, versioned, private, access-logged) plus a
# dedicated server-access-log bucket. ACLs are disabled (BucketOwnerEnforced)
# on both; TLS is enforced via bucket policy; lifecycle rules bound storage.
# ===========================================================================

# ---------------------------------------------------------------------------
# Access-log bucket — receives S3 server access logs for the data bucket.
# ---------------------------------------------------------------------------
resource "aws_s3_bucket" "logs" {
  # checkov:skip=CKV_AWS_145:Log-delivery target buckets cannot use a customer-managed CMK; AES256 (SSE-S3) is mandated by S3 access logging.
  # checkov:skip=CKV_AWS_144:Single-region reference stack; cross-region replication needs a destination bucket/region that is out of scope.
  # checkov:skip=CKV2_AWS_62:No event consumer exists in this stack; bucket notifications would have no target.
  bucket        = "${local.name_prefix}-logs-${random_id.suffix.hex}"
  force_destroy = var.force_destroy_buckets
}

resource "aws_s3_bucket_ownership_controls" "logs" {
  bucket = aws_s3_bucket.logs.id
  rule {
    object_ownership = "BucketOwnerEnforced" # ACLs disabled
  }
}

resource "aws_s3_bucket_public_access_block" "logs" {
  bucket                  = aws_s3_bucket.logs.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_versioning" "logs" {
  bucket = aws_s3_bucket.logs.id
  versioning_configuration {
    status = "Enabled"
  }
}

# SSE-S3 (AES256), NOT the CMK: S3 server-access-log delivery does not support
# a customer-managed KMS key on the *target* bucket, so AES256 is required here.
# (The CKV_AWS_145 exception is declared on the aws_s3_bucket.logs resource.)
resource "aws_s3_bucket_server_side_encryption_configuration" "logs" {
  bucket = aws_s3_bucket.logs.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
    bucket_key_enabled = true
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "logs" {
  bucket = aws_s3_bucket.logs.id
  rule {
    id     = "expire-access-logs"
    status = "Enabled"
    filter {}
    abort_incomplete_multipart_upload {
      days_after_initiation = 7
    }
    expiration {
      days = var.log_object_retention_days
    }
    noncurrent_version_expiration {
      noncurrent_days = 30
    }
  }
}

# Allow S3 log delivery to write here, and deny any non-TLS access.
# The log bucket has no server access logging of its own (would be circular).
data "aws_iam_policy_document" "logs_bucket" {
  statement {
    sid    = "AllowS3ServerAccessLogDelivery"
    effect = "Allow"
    principals {
      type        = "Service"
      identifiers = ["logging.s3.amazonaws.com"]
    }
    actions   = ["s3:PutObject"]
    resources = ["${aws_s3_bucket.logs.arn}/*"]
    condition {
      test     = "ArnLike"
      variable = "aws:SourceArn"
      values   = [aws_s3_bucket.data.arn]
    }
  }
  statement {
    sid       = "DenyInsecureTransport"
    effect    = "Deny"
    actions   = ["s3:*"]
    resources = [aws_s3_bucket.logs.arn, "${aws_s3_bucket.logs.arn}/*"]
    principals {
      type        = "AWS"
      identifiers = ["*"]
    }
    condition {
      test     = "Bool"
      variable = "aws:SecureTransport"
      values   = ["false"]
    }
  }
}

resource "aws_s3_bucket_policy" "logs" {
  bucket = aws_s3_bucket.logs.id
  policy = data.aws_iam_policy_document.logs_bucket.json
}

# ---------------------------------------------------------------------------
# Data bucket — what the Lambda actually reads and writes.
# ---------------------------------------------------------------------------
resource "aws_s3_bucket" "data" {
  # checkov:skip=CKV_AWS_144:Single-region reference stack; cross-region replication needs a destination bucket/region that is out of scope.
  # checkov:skip=CKV2_AWS_62:No event consumer exists in this stack; bucket notifications would have no target.
  bucket        = "${local.name_prefix}-${random_id.suffix.hex}"
  force_destroy = var.force_destroy_buckets
}

resource "aws_s3_bucket_ownership_controls" "data" {
  bucket = aws_s3_bucket.data.id
  rule {
    object_ownership = "BucketOwnerEnforced" # ACLs disabled
  }
}

resource "aws_s3_bucket_public_access_block" "data" {
  bucket                  = aws_s3_bucket.data.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_versioning" "data" {
  bucket = aws_s3_bucket.data.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "data" {
  bucket = aws_s3_bucket.data.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm     = "aws:kms"
      kms_master_key_id = aws_kms_key.main.arn
    }
    bucket_key_enabled = true # reduces KMS request cost
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "data" {
  bucket = aws_s3_bucket.data.id
  rule {
    id     = "manage-noncurrent-and-incomplete"
    status = "Enabled"
    filter {}
    abort_incomplete_multipart_upload {
      days_after_initiation = 7
    }
    noncurrent_version_expiration {
      noncurrent_days = var.noncurrent_version_retention_days
    }
  }
}

resource "aws_s3_bucket_logging" "data" {
  bucket        = aws_s3_bucket.data.id
  target_bucket = aws_s3_bucket.logs.id
  target_prefix = "s3-access/"
}

# Enforce TLS for all access to the data bucket.
data "aws_iam_policy_document" "data_bucket" {
  statement {
    sid       = "DenyInsecureTransport"
    effect    = "Deny"
    actions   = ["s3:*"]
    resources = [aws_s3_bucket.data.arn, "${aws_s3_bucket.data.arn}/*"]
    principals {
      type        = "AWS"
      identifiers = ["*"]
    }
    condition {
      test     = "Bool"
      variable = "aws:SecureTransport"
      values   = ["false"]
    }
  }
}

resource "aws_s3_bucket_policy" "data" {
  bucket = aws_s3_bucket.data.id
  policy = data.aws_iam_policy_document.data_bucket.json

  # The public access block must exist first so the policy can never widen access.
  depends_on = [aws_s3_bucket_public_access_block.data]
}
