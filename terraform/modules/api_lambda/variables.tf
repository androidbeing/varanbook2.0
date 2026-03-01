################################################################################
# terraform/modules/api_lambda/variables.tf
################################################################################

variable "project_name" {
  type = string
}

variable "environment" {
  type = string
}

variable "aws_region" {
  type    = string
  default = "ap-south-1"
}

variable "image_tag" {
  description = "ECR image tag to deploy (e.g. 'latest' or a git SHA)"
  type        = string
  default     = "latest"
}

variable "lambda_memory_mb" {
  description = "Lambda memory allocation in MB (also affects vCPU share)"
  type        = number
  default     = 512
}

# ── Database (existing RDS) ────────────────────────────────────────────────────
variable "db_host" {
  description = "RDS endpoint (e.g. mydb.xxxxxxxx.ap-south-1.rds.amazonaws.com)"
  type        = string
}

variable "db_port" {
  type    = number
  default = 5432
}

variable "db_name" {
  type = string
}

variable "db_username" {
  type      = string
  sensitive = true
}

variable "db_password" {
  type      = string
  sensitive = true
}

# ── App secrets ────────────────────────────────────────────────────────────────
variable "secret_key" {
  description = "JWT / app secret key"
  type        = string
  sensitive   = true
}

variable "secrets_manager_arn" {
  description = "Optional: ARN of Secrets Manager secret for the app (for policy scoping)"
  type        = string
  default     = ""
}

# ── Networking (optional – set if Lambda must be inside VPC to reach RDS) ──────
variable "vpc_id" {
  type    = string
  default = ""
}

variable "subnet_ids" {
  type    = list(string)
  default = []
}

variable "security_group_ids" {
  type    = list(string)
  default = []
}

# ── S3 media bucket ────────────────────────────────────────────────────────────
variable "media_bucket_name" {
  type = string
}

# ── CORS / Frontend ───────────────────────────────────────────────────────────
variable "allowed_origins" {
  description = "Comma-separated list of allowed CORS origins"
  type        = string
  default     = "http://localhost:5173"
}

variable "frontend_url" {
  description = "CloudFront / custom domain URL of the frontend"
  type        = string
  default     = ""
}

# ── SMTP ──────────────────────────────────────────────────────────────────────
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
