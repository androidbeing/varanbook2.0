################################################################################
# terraform/modules/lambda/main.tf – SQS + Lambda push notification module
#
# Creates:
#   - SQS standard queue with dead-letter queue
#   - IAM role for Lambda with SQS + Secrets Manager permissions
#   - Lambda function (Node.js or Python) triggered by SQS
#   - SQS → Lambda event source mapping
################################################################################

# ── SQS Dead-Letter Queue ─────────────────────────────────────────────────────
resource "aws_sqs_queue" "dlq" {
  name                      = "${var.project_name}-notifications-dlq-${var.environment}"
  message_retention_seconds = 1209600  # 14 days

  tags = {
    Name    = "notification-dlq"
    Purpose = "failed-push-notifications"
  }
}

# ── SQS Main Queue ─────────────────────────────────────────────────────────────
resource "aws_sqs_queue" "notifications" {
  name                       = var.sqs_queue_name
  visibility_timeout_seconds = 90       # must be >= Lambda timeout
  message_retention_seconds  = 86400    # 24 hours
  delay_seconds              = 0
  receive_wait_time_seconds  = 20       # long polling

  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.dlq.arn
    maxReceiveCount     = 3             # retry 3 times before DLQ
  })

  tags = {
    Name = var.sqs_queue_name
  }
}

# ── IAM Role for Lambda ────────────────────────────────────────────────────────
resource "aws_iam_role" "lambda" {
  name = "${var.project_name}-notif-lambda-${var.environment}"

  assume_role_policy = jsonencode({
    Version   = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "lambda.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy" "lambda_sqs_policy" {
  name = "sqs-consume-policy"
  role = aws_iam_role.lambda.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        # Allow Lambda to read from the SQS queue
        Effect   = "Allow"
        Action   = [
          "sqs:ReceiveMessage",
          "sqs:DeleteMessage",
          "sqs:GetQueueAttributes",
          "sqs:ChangeMessageVisibility"
        ]
        Resource = aws_sqs_queue.notifications.arn
      },
      {
        # Allow reading Firebase credentials from Secrets Manager
        Effect   = "Allow"
        Action   = ["secretsmanager:GetSecretValue"]
        Resource = var.firebase_creds_arn != "" ? var.firebase_creds_arn : "*"
      },
      {
        # CloudWatch Logs
        Effect   = "Allow"
        Action   = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:${var.region}:${var.account_id}:*"
      }
    ]
  })
}

# ── Lambda Function ────────────────────────────────────────────────────────────
resource "aws_lambda_function" "notifier" {
  function_name    = "${var.project_name}-push-notifier-${var.environment}"
  role             = aws_iam_role.lambda.arn
  filename         = var.lambda_zip_path
  source_code_hash = filebase64sha256(var.lambda_zip_path)
  handler          = "index.handler"   # entry point in the ZIP
  runtime          = "nodejs20.x"
  timeout          = 60                # seconds
  memory_size      = 256               # MB

  environment {
    variables = {
      ENVIRONMENT            = var.environment
      FIREBASE_SECRET_ARN    = var.firebase_creds_arn
    }
  }

  # X-Ray tracing for production debugging
  tracing_config {
    mode = var.environment == "production" ? "Active" : "PassThrough"
  }

  tags = {
    Name = "push-notifier"
  }

  # Ignore if ZIP doesn't exist yet (first apply before deploying Lambda code)
  lifecycle {
    ignore_changes = [filename, source_code_hash]
  }
}

# ── SQS → Lambda event source mapping ─────────────────────────────────────────
resource "aws_lambda_event_source_mapping" "sqs_trigger" {
  event_source_arn                   = aws_sqs_queue.notifications.arn
  function_name                      = aws_lambda_function.notifier.arn
  batch_size                         = 10
  maximum_batching_window_in_seconds = 5
  enabled                            = true
}

# ── CloudWatch Log Group for Lambda ───────────────────────────────────────────
resource "aws_cloudwatch_log_group" "lambda" {
  name              = "/aws/lambda/${aws_lambda_function.notifier.function_name}"
  retention_in_days = 30
}

################################################################################
# Variables
################################################################################
variable "environment"        { type = string }
variable "project_name"       { type = string }
variable "sqs_queue_name"     { type = string }
variable "lambda_zip_path"    { type = string }
variable "firebase_creds_arn" { type = string; default = "" }
variable "account_id"         { type = string }
variable "region"             { type = string }

################################################################################
# Outputs
################################################################################
output "sqs_queue_url"        { value = aws_sqs_queue.notifications.url }
output "sqs_queue_arn"        { value = aws_sqs_queue.notifications.arn }
output "dlq_url"              { value = aws_sqs_queue.dlq.url }
output "lambda_function_name" { value = aws_lambda_function.notifier.function_name }
output "lambda_function_arn"  { value = aws_lambda_function.notifier.arn }
