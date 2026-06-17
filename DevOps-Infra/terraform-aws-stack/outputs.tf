output "api_endpoint" {
  description = "Invoke URL for the HTTP API route (GET /hello)."
  value       = "${aws_apigatewayv2_api.http.api_endpoint}/hello"
}

output "s3_bucket_name" {
  description = "Name of the data bucket."
  value       = aws_s3_bucket.data.bucket
}

output "lambda_function_name" {
  description = "Deployed Lambda function name."
  value       = aws_lambda_function.api.function_name
}

output "lambda_role_arn" {
  description = "Execution role ARN for the Lambda."
  value       = aws_iam_role.lambda.arn
}
