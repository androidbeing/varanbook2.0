################################################################################
# terraform/modules/api_gateway/main.tf – AWS HTTP API Gateway
#
# Creates an AWS API Gateway v2 (HTTP API) that proxies ALL routes
# to the FastAPI application load balancer.
#
# HTTP API is chosen over REST API for:
#   - Lower latency (~60 % cheaper than REST API)
#   - Built-in JWT authoriser support
#   - Simpler proxy integration
################################################################################

resource "aws_apigatewayv2_api" "this" {
  name          = "${var.project_name}-api-${var.environment}"
  protocol_type = "HTTP"
  description   = "Varanbook matrimonial SaaS API Gateway"

  # CORS handled by FastAPI; API GW passes through
  cors_configuration {
    allow_origins = ["*"]
    allow_methods = ["*"]
    allow_headers = ["*"]
    max_age       = 3600
  }
}

# ── Integration – forward all traffic to FastAPI ALB ──────────────────────────
resource "aws_apigatewayv2_integration" "fastapi" {
  api_id                 = aws_apigatewayv2_api.this.id
  integration_type       = "HTTP_PROXY"
  integration_method     = "ANY"
  integration_uri        = "${var.backend_url}/{proxy}"
  payload_format_version = "1.0"

  # Pass the original host header so FastAPI can resolve tenant from subdomain
  request_parameters = {
    "overwrite:header.host" = "$request.header.host"
  }
}

# ── Catch-all route ────────────────────────────────────────────────────────────
resource "aws_apigatewayv2_route" "proxy" {
  api_id    = aws_apigatewayv2_api.this.id
  route_key = "ANY /{proxy+}"
  target    = "integrations/${aws_apigatewayv2_integration.fastapi.id}"
}

resource "aws_apigatewayv2_route" "root" {
  api_id    = aws_apigatewayv2_api.this.id
  route_key = "ANY /"
  target    = "integrations/${aws_apigatewayv2_integration.fastapi.id}"
}

# ── Default stage with auto-deploy ────────────────────────────────────────────
resource "aws_apigatewayv2_stage" "default" {
  api_id      = aws_apigatewayv2_api.this.id
  name        = "$default"
  auto_deploy = true

  # Access logging to CloudWatch
  access_log_settings {
    destination_arn = aws_cloudwatch_log_group.api_gw.arn
  }

  default_route_settings {
    throttling_burst_limit = 1000
    throttling_rate_limit  = 500
  }
}

# ── CloudWatch log group ───────────────────────────────────────────────────────
resource "aws_cloudwatch_log_group" "api_gw" {
  name              = "/aws/apigateway/${var.project_name}-${var.environment}"
  retention_in_days = 30
}

# ── Custom domain (optional) ───────────────────────────────────────────────────
# Uncomment and supply an ACM certificate ARN + Route53 zone to enable.
#
# resource "aws_apigatewayv2_domain_name" "custom" {
#   domain_name = "api.${var.environment == "production" ? "varanbook.in" : "${var.environment}.varanbook.in"}"
#
#   domain_name_configuration {
#     certificate_arn = var.acm_cert_arn
#     endpoint_type   = "REGIONAL"
#     security_policy = "TLS_1_2"
#   }
# }

################################################################################
# Variables
################################################################################
variable "environment"   { type = string }
variable "project_name"  { type = string }
variable "backend_url"   { type = string }

################################################################################
# Outputs
################################################################################
output "invoke_url"  { value = aws_apigatewayv2_stage.default.invoke_url }
output "api_id"      { value = aws_apigatewayv2_api.this.id }
