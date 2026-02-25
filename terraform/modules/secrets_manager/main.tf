###############################################################################
# terraform/modules/secrets_manager/main.tf
#
# Stores DB credentials and application secrets in AWS Secrets Manager.
# Secrets are referenced by the Lambda function via ${{ secrets.* }} env vars.
###############################################################################

terraform {
  required_providers {
    aws = { source = "hashicorp/aws", version = "~> 5.0" }
  }
}

# ── DB credentials ─────────────────────────────────────────────────────────────
resource "aws_secretsmanager_secret" "db_credentials" {
  name                    = "${var.app_name}/${var.environment}/db-credentials"
  description             = "PostgreSQL credentials for ${var.app_name}"
  recovery_window_in_days = var.environment == "production" ? 7 : 0

  tags = var.tags
}

resource "aws_secretsmanager_secret_version" "db_credentials" {
  secret_id = aws_secretsmanager_secret.db_credentials.id
  secret_string = jsonencode({
    username = var.db_username
    password = var.db_password
    host     = var.db_host
    port     = var.db_port
    dbname   = var.db_name
  })
}

# ── JWT + app secrets ──────────────────────────────────────────────────────────
resource "aws_secretsmanager_secret" "app_secrets" {
  name                    = "${var.app_name}/${var.environment}/app-secrets"
  description             = "JWT secret key and other app secrets for ${var.app_name}"
  recovery_window_in_days = var.environment == "production" ? 7 : 0

  tags = var.tags
}

resource "aws_secretsmanager_secret_version" "app_secrets" {
  secret_id = aws_secretsmanager_secret.app_secrets.id
  secret_string = jsonencode({
    SECRET_KEY    = var.secret_key
    SMTP_PASSWORD = var.smtp_password
  })
}

# ── IAM policy document (attached to Lambda role) ─────────────────────────────
data "aws_iam_policy_document" "read_secrets" {
  statement {
    sid    = "ReadAppSecrets"
    effect = "Allow"
    actions = [
      "secretsmanager:GetSecretValue",
      "secretsmanager:DescribeSecret",
    ]
    resources = [
      aws_secretsmanager_secret.db_credentials.arn,
      aws_secretsmanager_secret.app_secrets.arn,
    ]
  }
}

resource "aws_iam_policy" "read_secrets" {
  name        = "${var.app_name}-${var.environment}-read-secrets"
  description = "Allow Lambda to read application secrets from Secrets Manager"
  policy      = data.aws_iam_policy_document.read_secrets.json
  tags        = var.tags
}

# ── Outputs ───────────────────────────────────────────────────────────────────
output "db_credentials_secret_arn" {
  description = "ARN of the DB credentials secret"
  value       = aws_secretsmanager_secret.db_credentials.arn
}

output "app_secrets_arn" {
  description = "ARN of the app secrets secret"
  value       = aws_secretsmanager_secret.app_secrets.arn
}

output "lambda_secrets_policy_arn" {
  description = "IAM policy ARN to attach to the Lambda execution role"
  value       = aws_iam_policy.read_secrets.arn
}

# ── Variables ─────────────────────────────────────────────────────────────────
variable "app_name" { type = string }
variable "environment" { type = string }
variable "tags" { type = map(string); default = {} }
variable "db_username" { type = string; sensitive = true }
variable "db_password" { type = string; sensitive = true }
variable "db_host" { type = string }
variable "db_port" { type = number; default = 5432 }
variable "db_name" { type = string }
variable "secret_key" { type = string; sensitive = true }
variable "smtp_password" { type = string; sensitive = true; default = "" }
