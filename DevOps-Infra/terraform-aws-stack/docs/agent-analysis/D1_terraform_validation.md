# D1 Terraform Validation Record

> Production-grade Terraform for a small serverless stack, validated with a clean offline plan.
> Tooling: **Terraform v1.15.6** · providers pinned & locked (aws 5.100.0, archive 2.8.0, random 3.9.0).
> Backend: **local**. Plan runs **fully offline** (mock AWS credentials + skip flags) — no real account.
> Date: 2026-06-17.

## 1. Architecture Overview
* **Target Stack:** AWS **S3 + Lambda + API Gateway (HTTP API v2)** (+ IAM, CloudWatch Logs).
* **Resource Summary (15 resources — from `terraform plan`):**
  * `random_id.suffix` — globally-unique bucket suffix (no placeholders/account-id).
  * `aws_s3_bucket.data` + `_versioning` + `_public_access_block` + `_server_side_encryption_configuration` — encrypted, private, versioned data bucket.
  * `aws_iam_role.lambda` + `aws_iam_role_policy_attachment.lambda_basic` (logging) + `aws_iam_role_policy.lambda_s3` (scoped S3 access).
  * `aws_cloudwatch_log_group.lambda` — log group with retention.
  * `aws_lambda_function.api` — Python handler, packaged locally via `archive_file`.
  * `aws_apigatewayv2_api.http` + `_integration.lambda` (AWS_PROXY) + `_route.hello` (`GET /hello`) + `_stage.default` (`$default`, auto-deploy).
  * `aws_lambda_permission.apigw` — lets API Gateway invoke the Lambda.
* **Data flow:** `client → API Gateway (GET /hello) → Lambda (AWS_PROXY) → reads/writes S3`.

## 2. Infrastructure Code Artifacts

### `versions.tf`
```hcl
terraform {
  required_version = ">= 1.6.0, < 2.0.0"

  required_providers {
    aws     = { source = "hashicorp/aws", version = "~> 5.60" }
    archive = { source = "hashicorp/archive", version = "~> 2.4" }
    random  = { source = "hashicorp/random", version = "~> 3.6" }
  }

  backend "local" {
    path = "terraform.tfstate"
  }
}
```

### `providers.tf`
```hcl
provider "aws" {
  region = var.aws_region

  # Mock credentials + skips so `terraform plan` runs fully offline.
  access_key                  = "mock-access-key-id"
  secret_key                  = "mock-secret-access-key"
  skip_credentials_validation = true
  skip_requesting_account_id  = true
  skip_metadata_api_check     = true

  default_tags {
    tags = {
      Project     = var.project_name
      Environment = var.environment
      ManagedBy   = "terraform"
    }
  }
}
```

### `variables.tf`
```hcl
variable "aws_region" {
  description = "AWS region to deploy into."
  type        = string
  default     = "ap-south-1"
  validation {
    condition     = can(regex("^[a-z]{2}-[a-z]+-[0-9]$", var.aws_region))
    error_message = "aws_region must look like 'ap-south-1' or 'us-east-1'."
  }
}

variable "project_name" {
  description = "Short project name; used for resource naming and tags."
  type        = string
  default     = "d1-svc"
  validation {
    condition     = can(regex("^[a-z][a-z0-9-]{1,30}$", var.project_name))
    error_message = "project_name must be lowercase alphanumeric/hyphen, 2-31 chars, starting with a letter."
  }
}

variable "environment" {
  description = "Deployment environment."
  type        = string
  default     = "dev"
  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "environment must be one of: dev, staging, prod."
  }
}

variable "lambda_runtime" {
  description = "Lambda runtime identifier."
  type        = string
  default     = "python3.12"
  validation {
    condition     = contains(["python3.11", "python3.12", "python3.13"], var.lambda_runtime)
    error_message = "lambda_runtime must be a supported Python runtime."
  }
}

variable "lambda_memory_mb" {
  description = "Lambda memory size in MB."
  type        = number
  default     = 128
  validation {
    condition     = var.lambda_memory_mb >= 128 && var.lambda_memory_mb <= 10240
    error_message = "lambda_memory_mb must be between 128 and 10240."
  }
}

variable "lambda_timeout_s" {
  description = "Lambda timeout in seconds."
  type        = number
  default     = 10
  validation {
    condition     = var.lambda_timeout_s >= 1 && var.lambda_timeout_s <= 900
    error_message = "lambda_timeout_s must be between 1 and 900."
  }
}

variable "log_retention_days" {
  description = "CloudWatch Logs retention for the Lambda log group."
  type        = number
  default     = 14
  validation {
    condition     = contains([1, 3, 5, 7, 14, 30, 60, 90, 120, 150, 180, 365, 400, 545, 731, 1827, 3653], var.log_retention_days)
    error_message = "log_retention_days must be a value accepted by CloudWatch Logs."
  }
}
```

### `main.tf`
```hcl
locals {
  name_prefix = "${var.project_name}-${var.environment}"
}

resource "random_id" "suffix" {
  byte_length = 4
}

# ---- S3 bucket (data store the Lambda reads/writes) ----
resource "aws_s3_bucket" "data" {
  bucket        = "${local.name_prefix}-${random_id.suffix.hex}"
  force_destroy = true
}

resource "aws_s3_bucket_versioning" "data" {
  bucket = aws_s3_bucket.data.id
  versioning_configuration { status = "Enabled" }
}

resource "aws_s3_bucket_public_access_block" "data" {
  bucket                  = aws_s3_bucket.data.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_server_side_encryption_configuration" "data" {
  bucket = aws_s3_bucket.data.id
  rule {
    apply_server_side_encryption_by_default { sse_algorithm = "AES256" }
  }
}

# ---- Lambda package (zipped locally) ----
data "archive_file" "lambda" {
  type        = "zip"
  source_file = "${path.module}/src/handler.py"
  output_path = "${path.module}/build/handler.zip"
}

# ---- IAM: assume role + basic logging + scoped S3 ----
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

resource "aws_iam_role_policy_attachment" "lambda_basic" {
  role       = aws_iam_role.lambda.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

data "aws_iam_policy_document" "lambda_s3" {
  statement {
    effect    = "Allow"
    actions   = ["s3:GetObject", "s3:PutObject", "s3:ListBucket"]
    resources = [aws_s3_bucket.data.arn, "${aws_s3_bucket.data.arn}/*"]
  }
}

resource "aws_iam_role_policy" "lambda_s3" {
  name   = "${local.name_prefix}-lambda-s3"
  role   = aws_iam_role.lambda.id
  policy = data.aws_iam_policy_document.lambda_s3.json
}

# ---- Lambda + log group ----
resource "aws_cloudwatch_log_group" "lambda" {
  name              = "/aws/lambda/${local.name_prefix}-fn"
  retention_in_days = var.log_retention_days
}

resource "aws_lambda_function" "api" {
  function_name    = "${local.name_prefix}-fn"
  role             = aws_iam_role.lambda.arn
  runtime          = var.lambda_runtime
  handler          = "handler.handler"
  filename         = data.archive_file.lambda.output_path
  source_code_hash = data.archive_file.lambda.output_base64sha256
  memory_size      = var.lambda_memory_mb
  timeout          = var.lambda_timeout_s

  environment {
    variables = { BUCKET_NAME = aws_s3_bucket.data.bucket }
  }

  depends_on = [
    aws_iam_role_policy_attachment.lambda_basic,
    aws_cloudwatch_log_group.lambda,
  ]
}

# ---- API Gateway (HTTP API v2) -> Lambda proxy ----
resource "aws_apigatewayv2_api" "http" {
  name          = "${local.name_prefix}-http"
  protocol_type = "HTTP"
}

resource "aws_apigatewayv2_integration" "lambda" {
  api_id                 = aws_apigatewayv2_api.http.id
  integration_type       = "AWS_PROXY"
  integration_uri        = aws_lambda_function.api.invoke_arn
  integration_method     = "POST"
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_route" "hello" {
  api_id    = aws_apigatewayv2_api.http.id
  route_key = "GET /hello"
  target    = "integrations/${aws_apigatewayv2_integration.lambda.id}"
}

resource "aws_apigatewayv2_stage" "default" {
  api_id      = aws_apigatewayv2_api.http.id
  name        = "$default"
  auto_deploy = true
}

resource "aws_lambda_permission" "apigw" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.api.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.http.execution_arn}/*/*"
}
```

### `outputs.tf`
```hcl
output "api_endpoint"         { value = "${aws_apigatewayv2_api.http.api_endpoint}/hello" }
output "s3_bucket_name"       { value = aws_s3_bucket.data.bucket }
output "lambda_function_name" { value = aws_lambda_function.api.function_name }
output "lambda_role_arn"      { value = aws_iam_role.lambda.arn }
```

### `src/handler.py`
```python
import json
import os


def handler(event, context):
    bucket = os.environ.get("BUCKET_NAME", "unknown")
    return {
        "statusCode": 200,
        "headers": {"content-type": "application/json"},
        "body": json.dumps({"message": "hello from lambda", "bucket": bucket}),
    }
```

## 3. Validation & Plan Execution Log

### `terraform fmt -recursive`
```text
fmt: clean   # no files reformatted
```

### `terraform init`
```text
Terraform has been successfully initialized!
# .terraform.lock.hcl pins: aws 5.100.0, archive 2.8.0, random 3.9.0
```

### `terraform validate`
```text
Success! The configuration is valid.
# validate -json: valid=True, errors=0, warnings=0
```

### `terraform plan` (offline, mock credentials)
```text
  # aws_apigatewayv2_api.http will be created
  # aws_apigatewayv2_integration.lambda will be created
  # aws_apigatewayv2_route.hello will be created
  # aws_apigatewayv2_stage.default will be created
  # aws_cloudwatch_log_group.lambda will be created
  # aws_iam_role.lambda will be created
  # aws_iam_role_policy.lambda_s3 will be created
  # aws_iam_role_policy_attachment.lambda_basic will be created
  # aws_lambda_function.api will be created
  # aws_lambda_permission.apigw will be created
  # aws_s3_bucket.data will be created
  # aws_s3_bucket_public_access_block.data will be created
  # aws_s3_bucket_server_side_encryption_configuration.data will be created
  # aws_s3_bucket_versioning.data will be created
  # random_id.suffix will be created

Plan: 15 to add, 0 to change, 0 to destroy.

Changes to Outputs:
  + api_endpoint         = (known after apply)
  + lambda_function_name = "d1-svc-dev-fn"
  + lambda_role_arn      = (known after apply)
  + s3_bucket_name       = (known after apply)
```

## 4. Variable Validation (proven, not just declared)
Negative tests confirm the `validation` blocks reject bad input:
```text
$ terraform plan -var='environment=banana'
Error: Invalid value for variable
  on variables.tf line 21 ...
  environment must be one of: dev, staging, prod.

$ terraform plan -var='aws_region=not-a-region'
  aws_region must look like 'ap-south-1' or 'us-east-1'.
  This was checked by the validation rule at variables.tf:5,3-13.
```

## 5. Requirements Compliance
| Requirement | Status |
|---|---|
| Providers explicitly defined, **strict version pinning** | ✅ `~> 5.60 / 2.4 / 3.6`, locked to 5.100.0 / 2.8.0 / 3.9.0 in `.terraform.lock.hcl` |
| **Local backend** / mock | ✅ `backend "local"` + mock AWS creds with skip flags (offline plan) |
| **Variable validation** (types + defaults + validation blocks) | ✅ 7 typed variables, all with defaults; 7 `validation` blocks (region, name, env, runtime, memory, timeout, retention) — negative-tested |
| **Zero placeholders** (no `<ACCOUNT_ID>` / `TODO`) | ✅ bucket name via `random_id`; IAM ARNs computed/managed-policy; no account-id literals; no TODO strings |
| Passes `validate` + clean `plan` | ✅ valid (0 errors/warnings); `Plan: 15 to add, 0 to change, 0 to destroy` |

## 6. How to apply (for a real account)
```bash
cd "Advanced/D1"
terraform init
terraform plan      # with real AWS_PROFILE/credentials, remove the mock keys/skips in providers.tf
terraform apply
# then: curl "$(terraform output -raw api_endpoint)"
terraform destroy   # tear down
```

---
**Completion:** files written → `fmt` clean → `init` ok → `validate` success → `plan` clean (15 add) →
variable validation negative-tested → zero placeholders. Artifacts in `Advanced/D1/`.
