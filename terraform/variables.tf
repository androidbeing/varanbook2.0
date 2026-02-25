################################################################################
# terraform/variables.tf – Input variable declarations
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
  description = "Short project name used as a resource prefix"
  type        = string
  default     = "varanbook"
}

# ── Network ───────────────────────────────────────────────────────────────────
variable "vpc_id" {
  description = "VPC ID where resources will be created"
  type        = string
}

variable "private_subnet_ids" {
  description = "Private subnet IDs for RDS (at least 2 AZs for multi-AZ)"
  type        = list(string)
}

variable "app_tier_cidr_blocks" {
  description = "CIDR blocks of the app tier (ECS tasks / EC2 ASG)"
  type        = list(string)
  default     = ["10.0.0.0/8"]
}

variable "fastapi_backend_url" {
  description = "URL of the FastAPI app's load balancer (for API Gateway integration)"
  type        = string
}

# ── RDS ───────────────────────────────────────────────────────────────────────
variable "db_name" {
  description = "PostgreSQL database name"
  type        = string
  default     = "varanbook"
}

variable "db_username" {
  description = "Master DB username"
  type        = string
  default     = "varanbook_admin"
}

variable "db_password" {
  description = "Master DB password (use AWS Secrets Manager in production)"
  type        = string
  sensitive   = true
}

variable "db_instance_class" {
  description = "RDS instance class"
  type        = string
  default     = "db.t3.medium"
}

variable "multi_az" {
  description = "Enable Multi-AZ deployment for RDS"
  type        = bool
  default     = false  # set true in production
}

# ── S3 ────────────────────────────────────────────────────────────────────────
variable "cors_origins" {
  description = "Allowed CORS origins for S3 bucket (for direct uploads)"
  type        = list(string)
  default     = ["https://*.varanbook.in"]
}

# ── Lambda ────────────────────────────────────────────────────────────────────
variable "lambda_zip_path" {
  description = "Local path to the Lambda deployment ZIP (FCM notifier)"
  type        = string
  default     = "lambda/notification_handler.zip"
}

variable "firebase_creds_secret_arn" {
  description = "ARN of the AWS Secrets Manager secret containing Firebase service account JSON"
  type        = string
  default     = ""
}

# ── Secrets Manager (Phase 2) ─────────────────────────────────────────────────
variable "app_secret_key" {
  description = "JWT / app secret key stored in Secrets Manager"
  type        = string
  sensitive   = true
  default     = ""  # override via tfvars or environment variable TF_VAR_app_secret_key
}

variable "smtp_password" {
  description = "SMTP password (SES SMTP secret) stored in Secrets Manager"
  type        = string
  sensitive   = true
  default     = ""
}
