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

# ACM certificates used by CloudFront must reside in us-east-1.
provider "aws" {
  alias  = "us_east_1"
  region = "us-east-1"

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
  # When domain_name is set, use it; otherwise fall back to the legacy tfvars variables.
  custom_domain          = var.domain_name != "" ? var.domain_name : var.frontend_custom_domain
  acm_certificate_arn    = try(aws_acm_certificate_validation.cloudfront[0].certificate_arn, var.frontend_acm_cert_arn)
  cloudfront_price_class = var.cloudfront_price_class
}

################################################################################
# Custom Domain – Route 53 + ACM + API CloudFront
# Only provisioned when var.domain_name is set (e.g. "varanbook.in")
################################################################################

# Look up the hosted zone created when the domain was registered in Route 53.
data "aws_route53_zone" "main" {
  count        = var.domain_name != "" ? 1 : 0
  name         = var.domain_name
  private_zone = false
}

# ACM certificate covering apex + wildcard (must be in us-east-1 for CloudFront).
resource "aws_acm_certificate" "cloudfront" {
  provider                  = aws.us_east_1
  count                     = var.domain_name != "" ? 1 : 0
  domain_name               = var.domain_name
  subject_alternative_names = ["*.${var.domain_name}"]
  validation_method         = "DNS"

  lifecycle {
    create_before_destroy = true
  }
}

# Route 53 CNAME records used by ACM to prove domain ownership.
resource "aws_route53_record" "acm_validation" {
  for_each = var.domain_name != "" ? {
    for dvo in aws_acm_certificate.cloudfront[0].domain_validation_options :
    dvo.domain_name => {
      name   = dvo.resource_record_name
      record = dvo.resource_record_value
      type   = dvo.resource_record_type
    }
  } : {}

  zone_id         = data.aws_route53_zone.main[0].zone_id
  name            = each.value.name
  type            = each.value.type
  records         = [each.value.record]
  ttl             = 300
  allow_overwrite = true
}

# Block until ACM confirms the cert is ISSUED.
resource "aws_acm_certificate_validation" "cloudfront" {
  provider                = aws.us_east_1
  count                   = var.domain_name != "" ? 1 : 0
  certificate_arn         = aws_acm_certificate.cloudfront[0].arn
  validation_record_fqdns = [for r in aws_route53_record.acm_validation : r.fqdn]
}

# CloudFront distribution for api.varanbook.in → Lightsail.
# Using CloudFront (rather than a raw CNAME) lets us terminate TLS with a
# proper ACM cert, cache-disable all requests, and forward everything to the
# Lightsail origin over its existing HTTPS endpoint.
resource "aws_cloudfront_distribution" "api" {
  count               = var.domain_name != "" ? 1 : 0
  enabled             = true
  is_ipv6_enabled     = true
  comment             = "${var.project_name} API (${var.environment})"
  aliases             = ["api.${var.domain_name}"]
  price_class         = var.cloudfront_price_class

  origin {
    # Strip the "https://" prefix – CloudFront needs just the hostname.
    domain_name = replace(module.lightsail.service_url, "https://", "")
    origin_id   = "lightsail-api"

    custom_origin_config {
      http_port              = 80
      https_port             = 443
      origin_protocol_policy = "https-only"
      origin_ssl_protocols   = ["TLSv1.2"]
    }
  }

  default_cache_behavior {
    allowed_methods        = ["DELETE", "GET", "HEAD", "OPTIONS", "PATCH", "POST", "PUT"]
    cached_methods         = ["GET", "HEAD"]
    target_origin_id       = "lightsail-api"
    viewer_protocol_policy = "redirect-to-https"
    compress               = true

    # CachingDisabled – every API request reaches Lightsail.
    cache_policy_id = "4135ea2d-6df8-44a3-9df3-4b5a84be39ad"
    # AllViewerExceptHostHeader – forwards cookies, query strings, and all
    # headers except Host (CloudFront sets Host to the origin domain).
    origin_request_policy_id = "b689b0a8-53d0-40ab-baf2-68738e2966ac"
  }

  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  viewer_certificate {
    acm_certificate_arn      = aws_acm_certificate_validation.cloudfront[0].certificate_arn
    ssl_support_method       = "sni-only"
    minimum_protocol_version = "TLSv1.2_2021"
  }

  tags = {
    Name = "${var.project_name}-api-cdn-${var.environment}"
  }
}

# ── Route 53 records ──────────────────────────────────────────────────────────

# varanbook.in  →  frontend CloudFront  (A Alias; apex cannot be a CNAME)
resource "aws_route53_record" "frontend_apex" {
  count   = var.domain_name != "" ? 1 : 0
  zone_id = data.aws_route53_zone.main[0].zone_id
  name    = var.domain_name
  type    = "A"

  alias {
    name                   = module.frontend_cdn.cloudfront_domain_name
    zone_id                = "Z2FDTNDATAQYW2" # CloudFront's fixed hosted zone ID
    evaluate_target_health = false
  }
}

# www.varanbook.in  →  frontend CloudFront  (CNAME)
resource "aws_route53_record" "frontend_www" {
  count   = var.domain_name != "" ? 1 : 0
  zone_id = data.aws_route53_zone.main[0].zone_id
  name    = "www.${var.domain_name}"
  type    = "CNAME"
  records = [module.frontend_cdn.cloudfront_domain_name]
  ttl     = 300
}

# api.varanbook.in  →  API CloudFront  (A Alias)
resource "aws_route53_record" "api" {
  count   = var.domain_name != "" ? 1 : 0
  zone_id = data.aws_route53_zone.main[0].zone_id
  name    = "api.${var.domain_name}"
  type    = "A"

  alias {
    name                   = aws_cloudfront_distribution.api[0].domain_name
    zone_id                = "Z2FDTNDATAQYW2"
    evaluate_target_health = false
  }
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
