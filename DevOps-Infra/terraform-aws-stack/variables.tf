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

variable "offline_mode" {
  description = "When true, the AWS provider uses mock credentials + skip flags so `terraform plan` runs with no real account. Set false for a real apply (OIDC/profile/env credential chain)."
  type        = bool
  default     = true
}

variable "tags" {
  description = "Additional tags merged into the provider default_tags (e.g. owner, cost-center)."
  type        = map(string)
  default     = {}
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

variable "lambda_reserved_concurrency" {
  description = "Reserved concurrent executions for the Lambda. -1 leaves it unreserved (uses the account pool); a positive value caps blast radius."
  type        = number
  default     = -1
  validation {
    condition     = var.lambda_reserved_concurrency == -1 || (var.lambda_reserved_concurrency >= 1 && var.lambda_reserved_concurrency <= 1000)
    error_message = "lambda_reserved_concurrency must be -1 (unreserved) or between 1 and 1000."
  }
}

variable "lambda_log_level" {
  description = "LOG_LEVEL environment variable passed to the handler."
  type        = string
  default     = "INFO"
  validation {
    condition     = contains(["DEBUG", "INFO", "WARNING", "ERROR"], var.lambda_log_level)
    error_message = "lambda_log_level must be one of: DEBUG, INFO, WARNING, ERROR."
  }
}

variable "log_retention_days" {
  description = "CloudWatch Logs retention for the Lambda + API Gateway log groups."
  type        = number
  default     = 14
  validation {
    condition     = contains([1, 3, 5, 7, 14, 30, 60, 90, 120, 150, 180, 365, 400, 545, 731, 1827, 3653], var.log_retention_days)
    error_message = "log_retention_days must be a value accepted by CloudWatch Logs."
  }
}

variable "log_object_retention_days" {
  description = "Days to keep S3 server-access-log objects before expiry."
  type        = number
  default     = 90
  validation {
    condition     = var.log_object_retention_days >= 1 && var.log_object_retention_days <= 3653
    error_message = "log_object_retention_days must be between 1 and 3653."
  }
}

variable "noncurrent_version_retention_days" {
  description = "Days to keep noncurrent object versions in the data bucket before expiry."
  type        = number
  default     = 90
  validation {
    condition     = var.noncurrent_version_retention_days >= 1 && var.noncurrent_version_retention_days <= 3653
    error_message = "noncurrent_version_retention_days must be between 1 and 3653."
  }
}

variable "force_destroy_buckets" {
  description = "Allow `terraform destroy` to delete non-empty S3 buckets. Keep false in prod to prevent accidental data loss."
  type        = bool
  default     = false
}

variable "kms_deletion_window_days" {
  description = "Waiting period (days) before the KMS key is deleted after scheduling."
  type        = number
  default     = 30
  validation {
    condition     = var.kms_deletion_window_days >= 7 && var.kms_deletion_window_days <= 30
    error_message = "kms_deletion_window_days must be between 7 and 30."
  }
}

variable "api_throttle_burst_limit" {
  description = "API Gateway stage burst limit (concurrent requests)."
  type        = number
  default     = 50
  validation {
    condition     = var.api_throttle_burst_limit >= 1 && var.api_throttle_burst_limit <= 10000
    error_message = "api_throttle_burst_limit must be between 1 and 10000."
  }
}

variable "api_throttle_rate_limit" {
  description = "API Gateway stage steady-state rate limit (requests/sec)."
  type        = number
  default     = 100
  validation {
    condition     = var.api_throttle_rate_limit >= 1 && var.api_throttle_rate_limit <= 10000
    error_message = "api_throttle_rate_limit must be between 1 and 10000."
  }
}
