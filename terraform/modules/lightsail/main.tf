################################################################################
# terraform/modules/lightsail/main.tf
#
# Provisions an AWS Lightsail Container Service to host the FastAPI backend.
#
# Why Lightsail over Lambda:
#   - Fixed monthly cost ($7–$25) vs Lambda per-invocation billing
#   - No cold starts – containers are always-warm
#   - Runs standard Gunicorn + Uvicorn workers (no ASGI adapter needed)
#   - Built-in HTTPS endpoint with a free TLS certificate
#   - Simpler ops – just push a Docker image to deploy
#
# Architecture:
#   Client → Lightsail Container Service (HTTPS) → FastAPI (Gunicorn/Uvicorn)
#             └─ connects to → Existing RDS PostgreSQL
################################################################################

resource "aws_lightsail_container_service" "api" {
  name        = "${var.project_name}-api-${var.environment}"
  power       = var.lightsail_power   # nano=$7, micro=$10, small=$25, medium=$50
  scale       = var.lightsail_scale   # number of running nodes (1 = single)
  is_disabled = false

  tags = {
    Name        = "${var.project_name}-api-${var.environment}"
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
}

################################################################################
# CloudWatch Log Group – Lightsail forwards container logs here
# (optional but useful for centralised log queries)
################################################################################
resource "aws_cloudwatch_log_group" "lightsail_api" {
  name              = "/lightsail/${var.project_name}-api-${var.environment}"
  retention_in_days = 14

  tags = {
    Environment = var.environment
  }
}
