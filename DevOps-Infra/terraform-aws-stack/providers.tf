provider "aws" {
  region = var.aws_region

  # Offline mode (default): mock credentials + skip flags so `terraform plan`
  # runs fully offline — no real account, STS, or IMDS calls. For a real apply,
  # set -var='offline_mode=false' (the CI apply job does this) so Terraform
  # falls back to the standard credential chain (OIDC / profile / env).
  access_key                  = var.offline_mode ? "mock-access-key-id" : null
  secret_key                  = var.offline_mode ? "mock-secret-access-key" : null
  skip_credentials_validation = var.offline_mode
  skip_requesting_account_id  = var.offline_mode
  skip_metadata_api_check     = var.offline_mode

  default_tags {
    tags = local.common_tags
  }
}
