################################################################################
# terraform/modules/frontend_cdn/variables.tf
################################################################################

variable "project_name" {
  type = string
}

variable "environment" {
  type = string
}

variable "bucket_name" {
  description = "S3 bucket name for the frontend build artifacts"
  type        = string
}

variable "custom_domain" {
  description = "Optional custom domain (e.g. app.varanbook.in). Leave blank for *.cloudfront.net"
  type        = string
  default     = ""
}

variable "acm_certificate_arn" {
  description = "ACM certificate ARN (must be in us-east-1) for the custom domain. Leave blank to use the default CloudFront cert."
  type        = string
  default     = ""
}

variable "cloudfront_price_class" {
  description = "CloudFront price class. PriceClass_100 = US/EU only (cheapest). PriceClass_All = worldwide."
  type        = string
  default     = "PriceClass_All"

  validation {
    condition     = contains(["PriceClass_100", "PriceClass_200", "PriceClass_All"], var.cloudfront_price_class)
    error_message = "Must be PriceClass_100, PriceClass_200, or PriceClass_All."
  }
}
