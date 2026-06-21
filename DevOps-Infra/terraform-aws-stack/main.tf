locals {
  name_prefix = "${var.project_name}-${var.environment}"

  # Tags applied to every resource. provider-level default_tags handles
  # propagation; this local exists for resources/policies that reference tags
  # directly (e.g. cost attribution in conditions).
  common_tags = merge(
    {
      Project     = var.project_name
      Environment = var.environment
      ManagedBy   = "terraform"
    },
    var.tags,
  )
}

# Globally-unique suffix so the S3 bucket names are valid without hardcoding an
# account id or placeholder. random is a local provider (no AWS API calls).
resource "random_id" "suffix" {
  byte_length = 4
}

# ---------------------------------------------------------------------------
# Lambda deployment package — zipped locally (no upload needed to plan)
# ---------------------------------------------------------------------------
data "archive_file" "lambda" {
  type        = "zip"
  source_file = "${path.module}/src/handler.py"
  output_path = "${path.module}/build/handler.zip"
}
