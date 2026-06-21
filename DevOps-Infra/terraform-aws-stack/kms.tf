# ---------------------------------------------------------------------------
# Customer-managed KMS key (CMK) — encrypts the S3 data bucket and the Lambda
# environment variables. Key rotation is enabled; deletion is windowed.
#
# The key policy is left to the AWS default (account root + IAM-governed
# access) on purpose: an explicit policy would need the account id, which is
# unavailable while `terraform plan` runs fully offline (skip_requesting_
# account_id = true, no STS call). Access is therefore granted via the
# scoped IAM policy on the Lambda role (see iam.tf), which is least-privilege.
# ---------------------------------------------------------------------------
resource "aws_kms_key" "main" {
  # checkov:skip=CKV2_AWS_64:An explicit key policy needs the account id (arn:aws:iam::<acct>:root); omitted to keep plan fully offline. The AWS default policy + scoped IAM (iam.tf) governs access.
  description             = "${local.name_prefix} CMK for S3 data + Lambda env encryption"
  deletion_window_in_days = var.kms_deletion_window_days
  enable_key_rotation     = true
}

resource "aws_kms_alias" "main" {
  name          = "alias/${local.name_prefix}"
  target_key_id = aws_kms_key.main.key_id
}
