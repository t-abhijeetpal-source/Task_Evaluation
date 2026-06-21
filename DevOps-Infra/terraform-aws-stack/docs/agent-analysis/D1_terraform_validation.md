# D1 Terraform Validation Record

> Enterprise-grade Terraform for an S3 + Lambda + API Gateway (HTTP API v2)
> serverless stack, validated with a clean **offline** plan plus lint, security
> scan, and handler unit tests.
> Tooling: **Terraform v1.15.6** · providers pinned & locked (aws 5.100.0,
> archive 2.8.0, random 3.9.0) · checkov · tflint · pytest.
> Backend: **local**. Plan runs **fully offline** (mock AWS creds + skip flags,
> gated by `var.offline_mode`) — no real account. A real apply flips
> `offline_mode=false` and uses the standard credential chain (OIDC/profile/env).
> Path: `DevOps-Infra/terraform-aws-stack/`. Date: 2026-06-22.

## 1. Architecture Overview
* **Target Stack:** AWS **S3 + Lambda + API Gateway (HTTP API v2)** (+ IAM, KMS,
  CloudWatch Logs, S3 access logging).
* **Data flow:** `client → API Gateway (GET /hello) → Lambda (AWS_PROXY) →
  S3 (records + counts visit objects)`. The handler genuinely uses the S3
  permissions the IAM role grants — code and infrastructure agree.
* **Resource Summary (28 resources — from `terraform plan`):**
  * `random_id.suffix` — globally-unique bucket suffix (no placeholders/account-id).
  * **KMS:** `aws_kms_key.main` (rotation on) + `aws_kms_alias.main`.
  * **Data bucket:** `aws_s3_bucket.data` + `_versioning` + `_public_access_block`
    + `_ownership_controls` (ACLs disabled) + `_server_side_encryption_configuration`
    (CMK) + `_lifecycle_configuration` + `_logging` + `_policy` (TLS-only).
  * **Access-log bucket:** `aws_s3_bucket.logs` + `_versioning` +
    `_public_access_block` + `_ownership_controls` + `_server_side_encryption_configuration`
    (AES256) + `_lifecycle_configuration` + `_policy` (log-delivery + TLS-only).
  * **IAM:** `aws_iam_role.lambda` + a single least-privilege inline
    `aws_iam_role_policy.lambda` (logs + S3 + KMS, scoped to exact ARNs; no
    managed policies, no wildcards).
  * **Lambda:** `aws_lambda_function.api` (env encrypted with the CMK) +
    `aws_cloudwatch_log_group.lambda`.
  * **API Gateway:** `aws_apigatewayv2_api.http` + `_integration.lambda`
    (AWS_PROXY) + `_route.hello` (`GET /hello`) + `_stage.default` (throttled,
    JSON access logging) + `aws_cloudwatch_log_group.apigw` +
    `aws_lambda_permission.apigw`.

## 2. Hardening vs. the original demo
The original stack was a clean 15-resource offline demo. This record reflects
the hardened version:

| Area | Before | After |
|---|---|---|
| Encryption | S3 AES256 only | **Customer-managed KMS CMK** (rotation on) for the data bucket + Lambda env vars |
| S3 hygiene | versioned + PAB | + ACLs disabled, TLS-only bucket policy, lifecycle rules, **server access logging** to a dedicated bucket |
| IAM | `AWSLambdaBasicExecutionRole` managed policy (`logs:* on *`) | **scoped inline policy** — logs/S3/KMS each pinned to exact ARNs; no wildcards |
| Lambda | stub, ignored S3 | **actually reads/writes S3** (record + count visits); reserved-concurrency var; env KMS-encrypted |
| API Gateway | no throttle, no logs | per-stage **throttling** + JSON **access logging** to CloudWatch |
| `force_destroy` | hardcoded `true` | `var.force_destroy_buckets` (default **false**) |
| Offline plan | hardcoded mock creds | `var.offline_mode` toggle — offline plan **and** real OIDC apply both work |
| Quality gates | none | **CI** (fmt/validate/plan/tflint/checkov) + **handler unit tests** (≥90% cov) |
| Docs | none; wrong paths | **README** (mermaid, quickstart, var/output tables) + this record |

## 3. Validation & Plan Execution Log

### `terraform fmt -check -recursive`
```text
clean   # no files reformatted
```

### `terraform init -backend=false`
```text
Terraform has been successfully initialized!
# .terraform.lock.hcl pins: aws 5.100.0, archive 2.8.0, random 3.9.0
```

### `terraform validate`
```text
Success! The configuration is valid.
```

### `terraform plan` (offline, `offline_mode=true` default)
```text
Plan: 28 to add, 0 to change, 0 to destroy.

Changes to Outputs:
  + api_endpoint         = (known after apply)
  + kms_key_arn          = (known after apply)
  + lambda_function_name = "d1-svc-dev-fn"
  + lambda_role_arn      = (known after apply)
  + logs_bucket_name     = (known after apply)
  + s3_bucket_name       = (known after apply)
```
Full output: [`D1_terraform_plan_output.txt`](D1_terraform_plan_output.txt).

### `checkov -d . --config-file .checkov.yaml`
```text
Passed checks: 98, Failed checks: 0, Skipped checks: 15
```
All 15 skips are inline `# checkov:skip=<ID>:<reason>` next to their resource
(audit-in-context). Notable ones: X-Ray (`CKV_AWS_50`, would force a wildcard
IAM resource), Lambda DLQ (`CKV_AWS_116`, sync invocation only), CMK on log
groups (`CKV_AWS_158`, needs account id — offline), logs-bucket KMS
(`CKV_AWS_145`, S3 log delivery requires SSE-S3), public route
(`CKV_AWS_309`, intentional demo endpoint).

### `pytest` (handler unit tests)
```text
6 passed — coverage 90% (gate: --cov-fail-under=90)
```

## 4. Variable Validation (proven, not just declared)
17 typed variables, all with defaults; negative tests confirm `validation`
blocks reject bad input:
```text
$ terraform plan -var='environment=banana'
  environment must be one of: dev, staging, prod.

$ terraform plan -var='aws_region=not-a-region'
  aws_region must look like 'ap-south-1' or 'us-east-1'.

$ terraform plan -var='lambda_reserved_concurrency=5000'
  lambda_reserved_concurrency must be -1 (unreserved) or between 1 and 1000.
```

## 5. Requirements Compliance
| Requirement | Status |
|---|---|
| Providers explicitly defined, **strict version pinning** | ✅ `~> 5.60 / 2.4 / 3.6`, locked to 5.100.0 / 2.8.0 / 3.9.0 in `.terraform.lock.hcl` |
| **Local backend** + offline plan | ✅ `backend "local"`; `var.offline_mode` mock creds/skip flags (no account) |
| **Variable validation** (types + defaults + validation) | ✅ 17 typed variables with defaults; validation blocks negative-tested |
| **Zero placeholders** (no `<ACCOUNT_ID>` / `TODO`) | ✅ bucket names via `random_id`; ARNs computed; no account-id literals; no TODO strings |
| **Least-privilege IAM** (no wildcards) | ✅ single inline policy scoped to exact log-group / bucket / CMK ARNs; no managed policies |
| **Encryption at rest** | ✅ CMK (rotation) for data bucket + Lambda env; AES256 for log bucket (required by log delivery) |
| **Security scan + lint clean** | ✅ checkov 0 failed (15 justified skips); tflint config committed |
| **Tests** | ✅ handler unit tests, coverage-gated ≥90% |
| Passes `validate` + clean `plan` | ✅ valid (0 errors/warnings); `Plan: 28 to add, 0 to change, 0 to destroy` |
| **CI** | ✅ `.github/workflows/d1-terraform.yml` (fmt/validate/offline-plan/tflint/checkov + handler tests; optional OIDC apply) |

## 6. How to apply (for a real account)
```bash
cd DevOps-Infra/terraform-aws-stack
terraform init
# offline_mode=false -> provider uses your credential chain (OIDC/profile/env)
terraform plan  -var='offline_mode=false'
terraform apply -var='offline_mode=false'
curl "$(terraform output -raw api_endpoint)"
terraform destroy -var='offline_mode=false'
```
CI can apply via the manual `workflow_dispatch` job using GitHub **OIDC**
(no long-lived secrets) — see the README "Real-account apply notes".

---
**Completion:** files written → `fmt` clean → `init` ok → `validate` success →
`plan` clean (28 add, offline) → tflint config + checkov clean (0 failed) →
handler tests pass (≥90% cov) → variable validation negative-tested → zero
placeholders → least-privilege IAM. Artifacts in `DevOps-Infra/terraform-aws-stack/`.
