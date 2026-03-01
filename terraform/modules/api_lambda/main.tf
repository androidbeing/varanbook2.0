################################################################################
# terraform/modules/api_lambda/main.tf
#
# Provisions the FastAPI backend as an AWS Lambda function (container image)
# fronted by an API Gateway v2 (HTTP API).
#
# Architecture:
#   Internet → API Gateway HTTP API → Lambda (Mangum + FastAPI) → RDS PostgreSQL
################################################################################

###############################################################################
# ECR Repository – stores the Lambda container image
###############################################################################
resource "aws_ecr_repository" "api" {
  name                 = "${var.project_name}-api-${var.environment}"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  tags = {
    Name = "${var.project_name}-api-${var.environment}"
  }
}

resource "aws_ecr_lifecycle_policy" "api" {
  repository = aws_ecr_repository.api.name

  policy = jsonencode({
    rules = [{
      rulePriority = 1
      description  = "Keep last 5 images"
      selection = {
        tagStatus   = "any"
        countType   = "imageCountMoreThan"
        countNumber = 5
      }
      action = { type = "expire" }
    }]
  })
}

###############################################################################
# IAM Role for Lambda
###############################################################################
resource "aws_iam_role" "api_lambda" {
  name = "${var.project_name}-api-lambda-role-${var.environment}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "lambda.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy_attachment" "basic_execution" {
  role       = aws_iam_role.api_lambda.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy" "api_lambda_policy" {
  name = "${var.project_name}-api-lambda-policy-${var.environment}"
  role = aws_iam_role.api_lambda.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        # S3 access for media uploads
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject",
          "s3:GeneratePresignedUrl"
        ]
        Resource = "arn:aws:s3:::${var.media_bucket_name}/*"
      },
      {
        Effect = "Allow"
        Action = ["s3:ListBucket"]
        Resource = "arn:aws:s3:::${var.media_bucket_name}"
      },
      {
        # SES for emails
        Effect   = "Allow"
        Action   = ["ses:SendEmail", "ses:SendRawEmail"]
        Resource = "*"
      },
      {
        # Secrets Manager – read app secrets
        Effect   = "Allow"
        Action   = ["secretsmanager:GetSecretValue"]
        Resource = var.secrets_manager_arn != "" ? var.secrets_manager_arn : "*"
      },
      {
        # CloudWatch Logs
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:*:*:*"
      }
    ]
  })
}

# VPC access if Lambda needs to be inside the VPC to reach RDS
resource "aws_iam_role_policy_attachment" "vpc_access" {
  count      = var.vpc_id != "" ? 1 : 0
  role       = aws_iam_role.api_lambda.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole"
}

###############################################################################
# Lambda Function (container image)
###############################################################################
resource "aws_lambda_function" "api" {
  function_name = "${var.project_name}-api-${var.environment}"
  role          = aws_iam_role.api_lambda.arn
  package_type  = "Image"
  image_uri     = "${aws_ecr_repository.api.repository_url}:${var.image_tag}"
  timeout       = 29   # API Gateway hard limit is 29 s
  memory_size   = var.lambda_memory_mb

  environment {
    variables = {
      APP_ENV                  = var.environment
      DEBUG                    = var.environment == "production" ? "false" : "true"
      SECRET_KEY               = var.secret_key
      DATABASE_URL             = "postgresql+asyncpg://${var.db_username}:${var.db_password}@${var.db_host}:${var.db_port}/${var.db_name}"
      DATABASE_POOL_SIZE       = "2"   # keep low for Lambda (ephemeral workers)
      DATABASE_MAX_OVERFLOW    = "2"
      AWS_REGION               = var.aws_region
      S3_BUCKET_NAME           = var.media_bucket_name
      ALLOWED_ORIGINS          = jsonencode(split(",", var.allowed_origins))
      APP_FRONTEND_URL         = var.frontend_url
      SMTP_HOST                = var.smtp_host
      SMTP_PORT                = tostring(var.smtp_port)
      SMTP_USERNAME            = var.smtp_username
      SMTP_PASSWORD            = var.smtp_password
      SMTP_FROM                = var.smtp_from
    }
  }

  dynamic "vpc_config" {
    for_each = var.vpc_id != "" ? [1] : []
    content {
      subnet_ids         = var.subnet_ids
      security_group_ids = var.security_group_ids
    }
  }

  tags = {
    Name = "${var.project_name}-api-${var.environment}"
  }

  # Terraform cannot create the function until the ECR image exists.
  # On fresh deploy: push the image first, then `terraform apply`.
  lifecycle {
    ignore_changes = [image_uri]   # updated via deploy script, not Terraform
  }
}

resource "aws_cloudwatch_log_group" "api_lambda" {
  name              = "/aws/lambda/${aws_lambda_function.api.function_name}"
  retention_in_days = 14
}

###############################################################################
# API Gateway v2 (HTTP API) → Lambda
###############################################################################
resource "aws_apigatewayv2_api" "api" {
  name          = "${var.project_name}-http-api-${var.environment}"
  protocol_type = "HTTP"
  description   = "Varanbook API Gateway → Lambda"

  cors_configuration {
    allow_origins     = split(",", var.allowed_origins)
    allow_methods     = ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"]
    allow_headers     = ["Content-Type", "Authorization", "X-Tenant-ID", "X-Request-ID"]
    expose_headers    = ["X-Request-ID"]
    allow_credentials = true
    max_age           = 3600
  }
}

resource "aws_apigatewayv2_integration" "lambda" {
  api_id                 = aws_apigatewayv2_api.api.id
  integration_type       = "AWS_PROXY"
  integration_uri        = aws_lambda_function.api.invoke_arn
  integration_method     = "POST"
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_route" "proxy" {
  api_id    = aws_apigatewayv2_api.api.id
  route_key = "ANY /{proxy+}"
  target    = "integrations/${aws_apigatewayv2_integration.lambda.id}"
}

resource "aws_apigatewayv2_route" "root" {
  api_id    = aws_apigatewayv2_api.api.id
  route_key = "ANY /"
  target    = "integrations/${aws_apigatewayv2_integration.lambda.id}"
}

resource "aws_apigatewayv2_stage" "default" {
  api_id      = aws_apigatewayv2_api.api.id
  name        = "$default"
  auto_deploy = true

  access_log_settings {
    destination_arn = aws_cloudwatch_log_group.apigw.arn
    format = jsonencode({
      requestId      = "$context.requestId"
      ip             = "$context.identity.sourceIp"
      requestTime    = "$context.requestTime"
      httpMethod     = "$context.httpMethod"
      routeKey       = "$context.routeKey"
      status         = "$context.status"
      protocol       = "$context.protocol"
      responseLength = "$context.responseLength"
    })
  }

  default_route_settings {
    throttling_burst_limit = 100
    throttling_rate_limit  = 50
  }
}

resource "aws_cloudwatch_log_group" "apigw" {
  name              = "/aws/apigateway/${var.project_name}-${var.environment}"
  retention_in_days = 14
}

# Allow API Gateway to invoke the Lambda function
resource "aws_lambda_permission" "apigw" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.api.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.api.execution_arn}/*/*"
}
