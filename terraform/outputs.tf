################################################################################
# terraform/outputs.tf – Root module outputs for cross-stack references
################################################################################

output "rds_endpoint" {
  description = "RDS PostgreSQL connection endpoint"
  value       = module.rds.db_endpoint
  sensitive   = true
}

output "rds_port" {
  description = "RDS PostgreSQL port"
  value       = module.rds.db_port
}

output "s3_bucket_name" {
  description = "S3 media bucket name"
  value       = module.s3.bucket_name
}

output "s3_bucket_arn" {
  description = "S3 media bucket ARN"
  value       = module.s3.bucket_arn
}

output "sqs_queue_url" {
  description = "SQS notification queue URL (set as SQS_NOTIFICATION_QUEUE_URL in app)"
  value       = module.sqs_lambda.sqs_queue_url
}

output "sqs_queue_arn" {
  description = "SQS notification queue ARN"
  value       = module.sqs_lambda.sqs_queue_arn
}

output "lambda_function_name" {
  description = "Lambda function name for push notification delivery"
  value       = module.sqs_lambda.lambda_function_name
}

output "api_gateway_url" {
  description = "API Gateway invoke URL"
  value       = module.api_gateway.invoke_url
}

# ── Secrets Manager (Phase 2) ─────────────────────────────────────────────────
output "db_credentials_secret_arn" {
  description = "ARN of the DB credentials secret in Secrets Manager"
  value       = module.secrets_manager.db_credentials_secret_arn
  sensitive   = true
}

output "app_secrets_arn" {
  description = "ARN of the app secrets (JWT key, SMTP) in Secrets Manager"
  value       = module.secrets_manager.app_secrets_arn
  sensitive   = true
}

# ── SNS / EventBridge (Phase 2) ───────────────────────────────────────────────
output "event_bus_name" {
  description = "Custom EventBridge bus name"
  value       = module.sns_eventbridge.event_bus_name
}

output "event_bus_arn" {
  description = "Custom EventBridge bus ARN"
  value       = module.sns_eventbridge.event_bus_arn
}

output "sns_topic_arns" {
  description = "Map of profile event SNS topic ARNs"
  value       = module.sns_eventbridge.sns_topic_arns
}
