################################################################################
# terraform/outputs.tf
################################################################################

# Backend (Lightsail)
output "api_url" {
  description = "HTTPS URL of the FastAPI backend (custom domain when set, Lightsail default otherwise)"
  value       = var.domain_name != "" ? "https://api.${var.domain_name}" : module.lightsail.service_url
}

output "lightsail_service_name" {
  description = "Lightsail service name (used by deploy script to push the image)"
  value       = module.lightsail.service_name
}

# Frontend (S3 + CloudFront)
output "frontend_url" {
  description = "Public HTTPS URL of the Vue.js frontend"
  value       = var.domain_name != "" ? "https://${var.domain_name}" : module.frontend_cdn.frontend_url
}

output "cloudfront_distribution_id" {
  description = "CloudFront distribution ID (for cache invalidation)"
  value       = module.frontend_cdn.cloudfront_distribution_id
}

output "frontend_bucket_name" {
  description = "S3 bucket where frontend build artifacts are deployed"
  value       = module.frontend_cdn.bucket_name
}

# Media S3
output "media_bucket_name" {
  description = "S3 bucket for user media (photos, PDFs)"
  value       = module.s3_media.bucket_name
}
