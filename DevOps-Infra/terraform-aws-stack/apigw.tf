# ===========================================================================
# API Gateway (HTTP API v2) -> Lambda (AWS_PROXY). Access logging to a
# dedicated CloudWatch log group; per-stage throttling caps request rate.
# ===========================================================================

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

# Public route by design: this is an unauthenticated "hello" demo endpoint and
# the README quickstart curls it directly. Gate it behind a JWT/IAM authorizer
# (var-toggle) before exposing anything sensitive.
resource "aws_apigatewayv2_route" "hello" {
  # checkov:skip=CKV_AWS_309:Intentionally public demo endpoint; add an authorizer before serving non-public data.
  api_id    = aws_apigatewayv2_api.http.id
  route_key = "GET /hello"
  target    = "integrations/${aws_apigatewayv2_integration.lambda.id}"
}

# Access logs for the stage (who called what, when, latency, status).
resource "aws_cloudwatch_log_group" "apigw" {
  # checkov:skip=CKV_AWS_158:CMK on log groups needs an account-scoped key policy; omitted to keep plan fully offline.
  # checkov:skip=CKV_AWS_338:Retention is configurable via var.log_retention_days; default kept short for demo cost (raise to 365 for compliance).
  name              = "/aws/apigateway/${local.name_prefix}-http"
  retention_in_days = var.log_retention_days
}

resource "aws_apigatewayv2_stage" "default" {
  api_id      = aws_apigatewayv2_api.http.id
  name        = "$default"
  auto_deploy = true

  access_log_settings {
    destination_arn = aws_cloudwatch_log_group.apigw.arn
    format = jsonencode({
      requestId       = "$context.requestId"
      ip              = "$context.identity.sourceIp"
      requestTime     = "$context.requestTime"
      httpMethod      = "$context.httpMethod"
      routeKey        = "$context.routeKey"
      status          = "$context.status"
      protocol        = "$context.protocol"
      responseLength  = "$context.responseLength"
      integrationErr  = "$context.integrationErrorMessage"
      responseLatency = "$context.responseLatency"
    })
  }

  default_route_settings {
    throttling_burst_limit = var.api_throttle_burst_limit
    throttling_rate_limit  = var.api_throttle_rate_limit
  }
}

resource "aws_lambda_permission" "apigw" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.api.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.http.execution_arn}/*/*"
}
