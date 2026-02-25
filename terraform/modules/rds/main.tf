################################################################################
# terraform/modules/rds/main.tf – Amazon RDS PostgreSQL module
#
# Creates:
#   - DB subnet group (multi-AZ ready)
#   - Parameter group (tuned for multi-tenant with RLS)
#   - RDS PostgreSQL instance with encryption, backups, deletion protection
################################################################################

resource "aws_db_subnet_group" "this" {
  name       = "${var.project_name}-db-subnet-${var.environment}"
  subnet_ids = var.subnet_ids

  tags = {
    Name = "${var.project_name}-db-subnet-group"
  }
}

resource "aws_db_parameter_group" "this" {
  name   = "${var.project_name}-pg15-${var.environment}"
  family = "postgres15"

  # Allow SET LOCAL for RLS context variable
  parameter {
    name  = "pg_stat_statements.track"
    value = "ALL"
  }

  # Tune for shorter connection times (pgBouncer is recommended in front)
  parameter {
    name  = "idle_in_transaction_session_timeout"
    value = "30000"   # 30 seconds
  }

  tags = {
    Name = "${var.project_name}-parameter-group"
  }
}

resource "aws_db_instance" "this" {
  identifier              = "${var.project_name}-${var.environment}"
  engine                  = "postgres"
  engine_version          = "15.6"
  instance_class          = var.db_instance_class
  allocated_storage       = 20
  max_allocated_storage   = 500        # auto-scaling storage (stops at 500 GB)
  storage_type            = "gp3"
  storage_encrypted       = true       # AES-256 at rest

  db_name  = var.db_name
  username = var.db_username
  password = var.db_password

  db_subnet_group_name   = aws_db_subnet_group.this.name
  vpc_security_group_ids = var.vpc_security_group_ids
  parameter_group_name   = aws_db_parameter_group.this.name

  multi_az               = var.multi_az
  publicly_accessible    = false

  backup_retention_period = 7
  backup_window           = "02:00-03:00"  # UTC
  maintenance_window      = "sun:04:00-sun:05:00"

  deletion_protection     = var.environment == "production" ? true : false
  skip_final_snapshot     = var.environment != "production"
  final_snapshot_identifier = var.environment == "production" ? "${var.project_name}-final-snapshot" : null

  # Enable Performance Insights (free tier: 7 days retention)
  performance_insights_enabled = true
  performance_insights_retention_period = 7

  tags = {
    Name = "${var.project_name}-postgres-${var.environment}"
  }
}

################################################################################
# Variables
################################################################################
variable "environment"            { type = string }
variable "db_name"                { type = string }
variable "db_username"            { type = string }
variable "db_password"            { type = string; sensitive = true }
variable "db_instance_class"      { type = string }
variable "multi_az"               { type = bool }
variable "vpc_security_group_ids" { type = list(string) }
variable "subnet_ids"             { type = list(string) }
variable "project_name"           { type = string; default = "varanbook" }

################################################################################
# Outputs
################################################################################
output "db_endpoint" { value = aws_db_instance.this.endpoint }
output "db_port"     { value = aws_db_instance.this.port }
output "db_id"       { value = aws_db_instance.this.id }
