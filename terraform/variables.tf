################################################################################
# terraform/variables.tf
################################################################################

variable "aws_region" {
  description = "AWS region for all resources"
  type        = string
  default     = "ap-south-1"
}

variable "environment" {
  description = "Deployment environment (development | staging | production)"
  type        = string
  validation {
    condition     = contains(["development", "staging", "production"], var.environment)
    error_message = "Must be development, staging, or production."
  }
}

variable "project_name" {
  type    = string
  default = "varanbook"
}

################################################################################
# Existing RDS PostgreSQL
################################################################################
variable "db_host" {
  description = "RDS endpoint (e.g. mydb.xxxx.ap-south-1.rds.amazonaws.com)"
  type        = string
}

variable "db_port" {
  type    = number
  default = 5432
}

variable "db_name" {
  type    = string
  default = "varanbook"
}

variable "db_username" {
  type = string
}

variable "db_password" {
  type      = string
  sensitive = true
}

################################################################################
# Lightsail Container Service
################################################################################
variable "lightsail_power" {
  description = "Lightsail power level: nano=$7/mo, micro=$10, small=$25, medium=$50"
  type        = string
  default     = "micro"
}

variable "lightsail_scale" {
  description = "Number of compute nodes (1 = single, 2+ = HA)"
  type        = number
  default     = 1
}

################################################################################
# App secrets
################################################################################
variable "app_secret_key" {
  description = "JWT secret key (min 32 chars). Generate: python -c \"import secrets; print(secrets.token_hex(32))\""
  type        = string
  sensitive   = true
}

################################################################################
# S3 / CORS
################################################################################
variable "cors_origins" {
  description = "Allowed CORS origins for the media bucket and API"
  type        = list(string)
  default     = ["http://localhost:5173"]
}

################################################################################
# Frontend (S3 + CloudFront)
################################################################################
variable "frontend_custom_domain" {
  description = "Optional custom domain (e.g. app.varanbook.in). Leave empty for *.cloudfront.net."
  type        = string
  default     = ""
}

variable "frontend_acm_cert_arn" {
  description = "ACM cert ARN in us-east-1 for the custom frontend domain."
  type        = string
  default     = ""
}

variable "cloudfront_price_class" {
  type    = string
  default = "PriceClass_All"
}

################################################################################
# SMTP / SES
################################################################################
variable "smtp_host" {
  type    = string
  default = ""
}

variable "smtp_port" {
  type    = number
  default = 587
}

variable "smtp_username" {
  type      = string
  default   = ""
  sensitive = true
}

variable "smtp_password" {
  type      = string
  default   = ""
  sensitive = true
}

variable "smtp_from" {
  type    = string
  default = "noreply@varanbook.in"
}

################################################################################
# Push notification Lambda (FCM) – optional
################################################################################
variable "enable_push_notifications" {
  description = "Deploy the FCM push-notification Lambda. Requires lambda_zip_path to exist."
  type        = bool
  default     = false
}

variable "lambda_zip_path" {
  type    = string
  default = "lambda/notification_handler.zip"
}

variable "firebase_creds_secret_arn" {
  type    = string
  default = ""
}
