# ===========================================================================
# Lambda function + its CloudWatch log group.
# ===========================================================================

# Pre-create the log group so retention/lifecycle is managed by Terraform
# (rather than auto-created by Lambda with never-expire retention).
#
# Log groups are encrypted at rest with an AWS-managed key by default. A
# customer-managed CMK is intentionally omitted: it requires an explicit key
# policy granting the CloudWatch Logs service principal, which in turn needs
# the account id — unavailable while `terraform plan` runs fully offline. Set
# kms_key_id + the corresponding key policy when applying to a real account.
resource "aws_cloudwatch_log_group" "lambda" {
  # checkov:skip=CKV_AWS_158:CMK on log groups needs an account-scoped key policy; omitted to keep plan fully offline.
  # checkov:skip=CKV_AWS_338:Retention is configurable via var.log_retention_days; default kept short for demo cost (raise to 365 for compliance).
  name              = "/aws/lambda/${local.name_prefix}-fn"
  retention_in_days = var.log_retention_days
}

# Function is invoked synchronously by API Gateway, so a dead-letter queue
# (which only captures *async* failures) would never receive traffic.
# X-Ray tracing is omitted because xray:PutTraceSegments only supports
# resource "*", which would violate this stack's no-wildcard-resource rule.
resource "aws_lambda_function" "api" {
  # checkov:skip=CKV_AWS_116:Synchronous (API Gateway) invocation — a DLQ only captures async failures.
  # checkov:skip=CKV_AWS_50:X-Ray requires an IAM wildcard resource; omitted to preserve least-privilege (no wildcard) guarantee.
  # checkov:skip=CKV_AWS_117:No VPC resources to reach; the function only calls regional S3/CloudWatch endpoints, so a VPC + NAT/endpoints would add cost with no isolation benefit.
  # checkov:skip=CKV_AWS_272:Code signing is out of scope for this reference stack.
  function_name = "${local.name_prefix}-fn"
  role          = aws_iam_role.lambda.arn
  runtime       = var.lambda_runtime
  handler       = "handler.handler"
  filename      = data.archive_file.lambda.output_path
  # Triggers redeploy only when the packaged code actually changes.
  source_code_hash               = data.archive_file.lambda.output_base64sha256
  memory_size                    = var.lambda_memory_mb
  timeout                        = var.lambda_timeout_s
  reserved_concurrent_executions = var.lambda_reserved_concurrency

  # Encrypt environment variables at rest with the customer-managed CMK.
  kms_key_arn = aws_kms_key.main.arn

  environment {
    variables = {
      BUCKET_NAME = aws_s3_bucket.data.bucket
      LOG_LEVEL   = var.lambda_log_level
    }
  }

  depends_on = [
    aws_iam_role_policy.lambda,
    aws_cloudwatch_log_group.lambda,
  ]
}
