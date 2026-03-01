################################################################################
# terraform/modules/lightsail/outputs.tf
################################################################################

output "service_name" {
  description = "Lightsail container service name (used by deploy script to push images)"
  value       = aws_lightsail_container_service.api.name
}

output "service_url" {
  description = "Built-in HTTPS URL of the Lightsail container service"
  value       = trimsuffix(aws_lightsail_container_service.api.url, "/")
}

output "service_arn" {
  value = aws_lightsail_container_service.api.arn
}
