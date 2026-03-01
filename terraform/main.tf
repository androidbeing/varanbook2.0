################################################################################
# terraform/main.tf – Root Terraform configuration
#
# Deploys:
#   - Lightsail Container Service – FastAPI backend (Gunicorn + Uvicorn)
#   - S3 + CloudFront – Vue.js SPA frontend
#   - S3 bucket – media (photos, horoscope PDFs)
#
# Pre-requisites:
#   1. AWS CLI configured  (aws configure)
#   2. Docker Desktop running
#   3. Terraform >= 1.6    (winget install Hashicorp.Terraform)
#   4. An existing RDS PostgreSQL instance – fill in db_* in terraform.tfvars
#
# Usage:
#   cd terraform
#   terraform init
#   terraform apply -var-file="terraform.tfvars"
#
#   Then run from repo root:
#   .\scripts\deploy.ps1 -Bootstrap   # first time
#   .\scripts\deploy.ps1              # subsequent deploys
################################################################################

terraform {
  required_version = ">= 1.6"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  # Remote state (recommended for teams – uncomment after creating the bucket):
  # backend "s3" {
  #   bucket         = "varanbook-terraform-state"
  #   key            = "prod/terraform.tfstate"
  #   region         = "ap-south-1"
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

data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

################################################################################
# Media S3 Bucket (profile photos, horoscope PDFs, etc.)
################################################################################
module "s3_media" {
  source = "./modules/s3"

  environment  = var.environment
  bucket_name  = "${var.project_name}-media-${var.environment}"
  cors_origins = var.cors_origins
}

################################################################################
# FastAPI backend -> Lightsail Container Service
# Terraform creates the service; the deploy script pushes the image + configures env
################################################################################
module "lightsail" {
  source = "./modules/lightsail"

  project_name    = var.project_name
  environment     = var.environment
  lightsail_power = var.lightsail_power
  lightsail_scale = var.lightsail_scale
}

################################################################################
# Vue.js frontend -> S3 + CloudFront
################################################################################
module "frontend_cdn" {
  source = "./modules/frontend_cdn"

  project_name           = var.project_name
  environment            = var.environment
  bucket_name            = "${var.project_name}-frontend-${var.environment}"
  custom_domain          = var.frontend_custom_domain
  acm_certificate_arn    = var.frontend_acm_cert_arn
  cloudfront_price_class = var.cloudfront_price_class
}

################################################################################
# Push notification worker: SQS + Lambda (FCM delivery) – optional
################################################################################
module "sqs_lambda_notifier" {
  count  = var.enable_push_notifications ? 1 : 0
  source = "./modules/lambda"

  environment        = var.environment
  project_name       = var.project_name
  sqs_queue_name     = "${var.project_name}-notifications-${var.environment}"
  lambda_zip_path    = var.lambda_zip_path
  firebase_creds_arn = var.firebase_creds_secret_arn
  account_id         = data.aws_caller_identity.current.account_id
  region             = data.aws_region.current.name
}
