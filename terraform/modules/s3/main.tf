################################################################################
# terraform/modules/s3/main.tf – S3 media bucket module
#
# Creates:
#   - Private S3 bucket with versioning and server-side encryption
#   - Lifecycle rules to move old objects to cheaper storage tiers
#   - CORS configuration for browser direct upload (pre-signed PUT)
#   - Bucket policy blocking public access
################################################################################

resource "aws_s3_bucket" "media" {
  bucket = var.bucket_name

  tags = {
    Name    = var.bucket_name
    Purpose = "matrimonial-media"
  }
}

# Block ALL public access at the bucket level
resource "aws_s3_bucket_public_access_block" "media" {
  bucket                  = aws_s3_bucket.media.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Server-side encryption (AES-256)
resource "aws_s3_bucket_server_side_encryption_configuration" "media" {
  bucket = aws_s3_bucket.media.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
    bucket_key_enabled = true
  }
}

# Versioning – allows recovery of accidentally overwritten media
resource "aws_s3_bucket_versioning" "media" {
  bucket = aws_s3_bucket.media.id
  versioning_configuration {
    status = "Enabled"
  }
}

# Lifecycle: move old versions to Glacier after 90 days, expire after 365
resource "aws_s3_bucket_lifecycle_configuration" "media" {
  bucket = aws_s3_bucket.media.id

  rule {
    id     = "archive-old-versions"
    status = "Enabled"

    noncurrent_version_transition {
      noncurrent_days = 90
      storage_class   = "GLACIER"
    }

    noncurrent_version_expiration {
      noncurrent_days = 365
    }
  }

  # Clean up failed multipart uploads
  rule {
    id     = "abort-incomplete-multipart"
    status = "Enabled"

    abort_incomplete_multipart_upload {
      days_after_initiation = 7
    }
  }
}

# CORS – allows browsers to PUT directly to S3 using pre-signed URLs
resource "aws_s3_bucket_cors_configuration" "media" {
  bucket = aws_s3_bucket.media.id

  cors_rule {
    allowed_headers = ["Content-Type", "Content-MD5", "x-amz-server-side-encryption"]
    allowed_methods = ["PUT", "GET"]
    allowed_origins = var.cors_origins
    max_age_seconds = 3600
  }
}

################################################################################
# Variables
################################################################################
variable "environment"  { type = string }
variable "bucket_name"  { type = string }
variable "cors_origins" { type = list(string); default = ["*"] }

################################################################################
# Outputs
################################################################################
output "bucket_name" { value = aws_s3_bucket.media.bucket }
output "bucket_arn"  { value = aws_s3_bucket.media.arn }
output "bucket_id"   { value = aws_s3_bucket.media.id }
