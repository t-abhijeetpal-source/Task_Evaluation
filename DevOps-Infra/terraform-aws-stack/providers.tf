provider "aws" {
  region = var.aws_region

  # Mock credentials + skips so `terraform plan` runs fully offline (no real
  # AWS account, STS, or IMDS calls). Replace/remove for a real apply.
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
