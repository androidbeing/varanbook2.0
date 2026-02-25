"""
services/notification.py – Enqueue push notifications via AWS SQS → Lambda → FCM.

Architecture:
  FastAPI  →  SQS queue  →  Lambda function  →  Google FCM  →  device

Benefits:
  - FastAPI never blocks on FCM latency.
  - SQS provides at-least-once delivery and dead-letter queue support.
  - Lambda auto-scales independently from the API tier.

Environment variables required:
  SQS_NOTIFICATION_QUEUE_URL  – full SQS queue URL
"""

import json
import uuid
from datetime import datetime, timezone

import boto3
from botocore.exceptions import BotoCoreError, ClientError

from app.config import get_settings

settings = get_settings()

# SQS client – one per worker
_sqs = boto3.client(
    "sqs",
    region_name=settings.AWS_REGION,
    aws_access_key_id=settings.AWS_ACCESS_KEY_ID or None,
    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY or None,
)


class NotificationService:
    """Sends push notification jobs to SQS for async processing."""

    def enqueue(
        self,
        user_id: uuid.UUID,
        fcm_token: str,
        title: str,
        body: str,
        data: dict | None = None,
    ) -> str:
        """
        Publish a push notification message to SQS.

        Returns:
            SQS MessageId for tracing.

        Message shape (consumed by the Lambda):
        {
            "user_id": "<uuid>",
            "fcm_token": "<device_token>",
            "title": "...",
            "body": "...",
            "data": {...},        # optional key-value pairs for FCM data payload
            "enqueued_at": "<iso8601>"
        }
        """
        if not settings.SQS_NOTIFICATION_QUEUE_URL:
            raise RuntimeError(
                "SQS_NOTIFICATION_QUEUE_URL is not configured. "
                "Set it in .env or environment."
            )

        message_body = {
            "user_id": str(user_id),
            "fcm_token": fcm_token,
            "title": title,
            "body": body,
            "data": data or {},
            "enqueued_at": datetime.now(tz=timezone.utc).isoformat(),
        }

        try:
            response = _sqs.send_message(
                QueueUrl=settings.SQS_NOTIFICATION_QUEUE_URL,
                MessageBody=json.dumps(message_body),
                # MessageGroupId only needed for FIFO queues; set if using .fifo suffix
            )
        except (BotoCoreError, ClientError) as exc:
            raise RuntimeError(f"SQS send_message failed: {exc}") from exc

        return response["MessageId"]

    def enqueue_bulk(
        self,
        notifications: list[dict],
    ) -> list[str]:
        """
        Batch-enqueue up to 10 notifications using SQS send_message_batch.

        Each item in `notifications` should have keys:
          user_id, fcm_token, title, body, data (optional).
        """
        if not notifications:
            return []

        entries = [
            {
                "Id": str(i),
                "MessageBody": json.dumps(
                    {
                        "user_id": str(n["user_id"]),
                        "fcm_token": n["fcm_token"],
                        "title": n["title"],
                        "body": n["body"],
                        "data": n.get("data", {}),
                        "enqueued_at": datetime.now(tz=timezone.utc).isoformat(),
                    }
                ),
            }
            for i, n in enumerate(notifications[:10])  # SQS max batch = 10
        ]

        try:
            response = _sqs.send_message_batch(
                QueueUrl=settings.SQS_NOTIFICATION_QUEUE_URL,
                Entries=entries,
            )
        except (BotoCoreError, ClientError) as exc:
            raise RuntimeError(f"SQS batch send failed: {exc}") from exc

        return [r["MessageId"] for r in response.get("Successful", [])]
