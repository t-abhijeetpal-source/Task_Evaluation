output "api_endpoint" {
  description = "Invoke URL for the HTTP API route (GET /hello)."
  value       = "${aws_apigatewayv2_api.http.api_endpoint}/hello"
}

output "s3_bucket_name" {
  description = "Name of the data bucket."
  value       = aws_s3_bucket.data.bucket
}

output "logs_bucket_name" {
  description = "Name of the S3 server-access-log bucket."
  value       = aws_s3_bucket.logs.bucket
}

output "lambda_function_name" {
  description = "Deployed Lambda function name."
  value       = aws_lambda_function.api.function_name
}

output "lambda_role_arn" {
  description = "Execution role ARN for the Lambda."
  value       = aws_iam_role.lambda.arn
}

output "kms_key_arn" {
  description = "ARN of the customer-managed KMS key encrypting the data bucket and Lambda env."
  value       = aws_kms_key.main.arn
}
