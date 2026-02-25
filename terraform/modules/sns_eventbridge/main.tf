###############################################################################
# terraform/modules/sns_eventbridge/main.tf
#
# Provisions:
#   - SNS topics for profile events (shortlisted, accepted, viewed)
#   - EventBridge event bus + rules routing to Lambda / SNS
#   - SQS dead-letter queues for failed deliveries
###############################################################################

terraform {
  required_providers {
    aws = { source = "hashicorp/aws", version = "~> 5.0" }
  }
}

# ── SNS Topics ─────────────────────────────────────────────────────────────────
locals {
  event_types = ["profile-shortlisted", "profile-accepted", "profile-viewed", "profile-updated"]
}

resource "aws_sns_topic" "profile_events" {
  for_each = toset(local.event_types)

  name              = "${var.app_name}-${var.environment}-${each.key}"
  kms_master_key_id = "alias/aws/sns"
  tags              = var.tags
}

# ── SQS Dead-letter queues ─────────────────────────────────────────────────────
resource "aws_sqs_queue" "dlq" {
  for_each = toset(local.event_types)

  name                       = "${var.app_name}-${var.environment}-${each.key}-dlq"
  message_retention_seconds  = 1_209_600  # 14 days
  kms_master_key_id          = "alias/aws/sqs"
  tags                       = var.tags
}

resource "aws_sns_topic_subscription" "to_dlq" {
  for_each = toset(local.event_types)

  topic_arn = aws_sns_topic.profile_events[each.key].arn
  protocol  = "sqs"
  endpoint  = aws_sqs_queue.dlq[each.key].arn

  filter_policy = jsonencode({ delivery = ["failed"] })
}

# ── Custom EventBridge bus ────────────────────────────────────────────────────
resource "aws_cloudwatch_event_bus" "main" {
  name = "${var.app_name}-${var.environment}"
  tags = var.tags
}

# ── EventBridge rules → SNS ───────────────────────────────────────────────────
resource "aws_cloudwatch_event_rule" "profile_shortlisted" {
  name           = "${var.app_name}-${var.environment}-profile-shortlisted"
  description    = "Route profile.shortlisted events to SNS"
  event_bus_name = aws_cloudwatch_event_bus.main.name
  event_pattern = jsonencode({
    "detail-type" = ["profile.shortlisted"]
  })
  tags = var.tags
}

resource "aws_cloudwatch_event_target" "shortlisted_to_sns" {
  rule           = aws_cloudwatch_event_rule.profile_shortlisted.name
  event_bus_name = aws_cloudwatch_event_bus.main.name
  arn            = aws_sns_topic.profile_events["profile-shortlisted"].arn
}

resource "aws_cloudwatch_event_rule" "profile_accepted" {
  name           = "${var.app_name}-${var.environment}-profile-accepted"
  description    = "Route profile.accepted events to SNS"
  event_bus_name = aws_cloudwatch_event_bus.main.name
  event_pattern = jsonencode({
    "detail-type" = ["profile.accepted"]
  })
  tags = var.tags
}

resource "aws_cloudwatch_event_target" "accepted_to_sns" {
  rule           = aws_cloudwatch_event_rule.profile_accepted.name
  event_bus_name = aws_cloudwatch_event_bus.main.name
  arn            = aws_sns_topic.profile_events["profile-accepted"].arn
}

# ── IAM: allow EventBridge to publish to SNS ──────────────────────────────────
data "aws_iam_policy_document" "eventbridge_to_sns" {
  statement {
    sid    = "AllowEventBridgePublish"
    effect = "Allow"
    principals {
      type        = "Service"
      identifiers = ["events.amazonaws.com"]
    }
    actions   = ["SNS:Publish"]
    resources = [for topic in aws_sns_topic.profile_events : topic.arn]
  }
}

resource "aws_sns_topic_policy" "allow_eventbridge" {
  for_each = toset(local.event_types)

  arn    = aws_sns_topic.profile_events[each.key].arn
  policy = data.aws_iam_policy_document.eventbridge_to_sns.json
}

# ── IAM policy for Lambda to put events on custom bus ────────────────────────
data "aws_iam_policy_document" "put_events" {
  statement {
    sid    = "PutEventsOnCustomBus"
    effect = "Allow"
    actions = ["events:PutEvents"]
    resources = [aws_cloudwatch_event_bus.main.arn]
  }
}

resource "aws_iam_policy" "put_events" {
  name        = "${var.app_name}-${var.environment}-put-events"
  description = "Allow Lambda to put events on the custom EventBridge bus"
  policy      = data.aws_iam_policy_document.put_events.json
  tags        = var.tags
}

# ── Outputs ───────────────────────────────────────────────────────────────────
output "event_bus_name" {
  value = aws_cloudwatch_event_bus.main.name
}

output "event_bus_arn" {
  value = aws_cloudwatch_event_bus.main.arn
}

output "sns_topic_arns" {
  value = { for k, v in aws_sns_topic.profile_events : k => v.arn }
}

output "lambda_put_events_policy_arn" {
  value = aws_iam_policy.put_events.arn
}

# ── Variables ─────────────────────────────────────────────────────────────────
variable "app_name" { type = string }
variable "environment" { type = string }
variable "tags" { type = map(string); default = {} }
