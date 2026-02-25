################################################################################
# terraform/main.tf – Root Terraform configuration
#
# Provisions:
#   - VPC with public/private subnets (via AWS default VPC for simplicity)
#   - RDS PostgreSQL (multi-AZ optional)
#   - S3 bucket for media (photos, horoscope PDFs)
#   - SQS queue for push notification jobs
#   - Lambda function for FCM push notification delivery
#   - API Gateway (HTTP API) fronting the FastAPI app on ECS / EC2
#
# Usage:
#   terraform init
#   terraform plan -var-file="envs/production.tfvars"
#   terraform apply -var-file="envs/production.tfvars"
################################################################################

terraform {
  required_version = ">= 1.6"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  # Remote state – uncomment and configure for production
  # backend "s3" {
  #   bucket         = "varanbook-terraform-state"
  #   key            = "prod/terraform.tfstate"
  #   region         = "ap-south-1"
  #   dynamodb_table = "varanbook-tf-locks"
  #   encrypt        = true
  # }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = "Varanbook"
      Environment = var.environment
      ManagedBy   = "Terraform"
    }
  }
}

################################################################################
# Data sources
################################################################################
data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

################################################################################
# Modules
################################################################################

module "rds" {
  source = "./modules/rds"

  environment        = var.environment
  db_name            = var.db_name
  db_username        = var.db_username
  db_password        = var.db_password
  db_instance_class  = var.db_instance_class
  multi_az           = var.multi_az
  vpc_security_group_ids = [aws_security_group.rds.id]
  subnet_ids         = var.private_subnet_ids
}

module "s3" {
  source = "./modules/s3"

  environment  = var.environment
  bucket_name  = "${var.project_name}-media-${var.environment}"
  cors_origins = var.cors_origins
}

module "sqs_lambda" {
  source = "./modules/lambda"

  environment        = var.environment
  project_name       = var.project_name
  sqs_queue_name     = "${var.project_name}-notifications-${var.environment}"
  lambda_zip_path    = var.lambda_zip_path
  firebase_creds_arn = var.firebase_creds_secret_arn
  account_id         = data.aws_caller_identity.current.account_id
  region             = data.aws_region.current.name
}

module "api_gateway" {
  source = "./modules/api_gateway"

  environment       = var.environment
  project_name      = var.project_name
  # The FastAPI app is deployed elsewhere (ECS/EC2); configure its load balancer URL.
  backend_url       = var.fastapi_backend_url
}

module "secrets_manager" {
  source = "./modules/secrets_manager"

  app_name      = var.project_name
  environment   = var.environment
  db_username   = var.db_username
  db_password   = var.db_password
  db_host       = module.rds.endpoint
  db_name       = var.db_name
  secret_key    = var.app_secret_key
  smtp_password = var.smtp_password
  tags = {
    Project     = "Varanbook"
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
}

module "sns_eventbridge" {
  source = "./modules/sns_eventbridge"

  app_name    = var.project_name
  environment = var.environment
  tags = {
    Project     = "Varanbook"
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
}

################################################################################
# Security group: RDS (allow inbound from app tier only)
################################################################################
resource "aws_security_group" "rds" {
  name        = "${var.project_name}-rds-sg-${var.environment}"
  description = "Allow PostgreSQL access from app tier"
  vpc_id      = var.vpc_id

  ingress {
    description = "PostgreSQL from app tier"
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    cidr_blocks = var.app_tier_cidr_blocks
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}
