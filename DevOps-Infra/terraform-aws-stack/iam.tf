# ===========================================================================
# IAM — least-privilege execution role for the Lambda. No AWS managed policies
# and no wildcard actions/resources: logging is scoped to this function's log
# group, S3 to the data bucket, and KMS to the single CMK.
# ===========================================================================

data "aws_iam_policy_document" "lambda_assume" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "lambda" {
  name               = "${local.name_prefix}-lambda-role"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume.json
}

# Single inline policy: CloudWatch Logs + S3 + KMS, each scoped to the exact
# ARN it needs. This replaces the broad AWSLambdaBasicExecutionRole managed
# policy (which grants logs:* on "*") with a tightly-scoped equivalent.
data "aws_iam_policy_document" "lambda" {
  statement {
    sid    = "ScopedCloudWatchLogs"
    effect = "Allow"
    actions = [
      "logs:CreateLogStream",
      "logs:PutLogEvents",
    ]
    # Log group is pre-created (see lambda.tf); grant writes to its streams only.
    resources = ["${aws_cloudwatch_log_group.lambda.arn}:*"]
  }

  statement {
    sid       = "ReadWriteDataBucketObjects"
    effect    = "Allow"
    actions   = ["s3:GetObject", "s3:PutObject"]
    resources = ["${aws_s3_bucket.data.arn}/*"]
  }

  statement {
    sid       = "ListDataBucket"
    effect    = "Allow"
    actions   = ["s3:ListBucket"]
    resources = [aws_s3_bucket.data.arn]
  }

  statement {
    sid    = "UseCmkForS3AndEnv"
    effect = "Allow"
    actions = [
      "kms:Decrypt",
      "kms:Encrypt",
      "kms:GenerateDataKey",
      "kms:DescribeKey",
    ]
    resources = [aws_kms_key.main.arn]
  }
}

resource "aws_iam_role_policy" "lambda" {
  name   = "${local.name_prefix}-lambda-policy"
  role   = aws_iam_role.lambda.id
  policy = data.aws_iam_policy_document.lambda.json
}
