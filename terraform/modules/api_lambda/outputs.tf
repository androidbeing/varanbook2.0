################################################################################
# terraform/modules/api_lambda/outputs.tf
################################################################################

output "ecr_repository_url" {
  description = "ECR repository URL (push Docker images here)"
  value       = aws_ecr_repository.api.repository_url
}

output "lambda_function_name" {
  description = "Lambda function name (use in deploy script)"
  value       = aws_lambda_function.api.function_name
}

output "api_gateway_url" {
  description = "Base URL of the deployed API"
  value       = aws_apigatewayv2_stage.default.invoke_url
}

output "api_gateway_id" {
  description = "API Gateway ID"
  value       = aws_apigatewayv2_api.api.id
}
