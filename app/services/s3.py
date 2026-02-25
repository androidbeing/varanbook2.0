"""
services/s3.py – Async wrapper around boto3 S3 for pre-signed URLs.

Why pre-signed URLs (PUT)?
  - The client uploads directly to S3 — the application server never handles
    multi-MB photo or horoscope PDF bytes, keeping the API tier stateless.
  - After a successful upload the client calls PATCH /profiles/{id}/media
    to register the S3 object key in the DB.

Usage:
    url, key = await S3Service().generate_presigned_put(
        purpose="profile_photo",
        tenant_id=str(tenant_id),
        file_name="photo.jpg",
        content_type="image/jpeg",
    )
"""

import mimetypes
import uuid
from datetime import datetime, timezone

import boto3
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError

from app.config import get_settings

settings = get_settings()

# S3 client is cheap to create; one per async worker is fine.
# Use path-style addressing when running against localstack.
_s3_client = boto3.client(
    "s3",
    region_name=settings.AWS_REGION,
    aws_access_key_id=settings.AWS_ACCESS_KEY_ID or None,
    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY or None,
    config=Config(signature_version="s3v4"),
)


class S3Service:
    """Handles S3 pre-signed URL generation and object key management."""

    ALLOWED_PURPOSES = {"profile_photo", "horoscope"}
    ALLOWED_CONTENT_TYPES = {
        "image/jpeg", "image/png", "image/webp", "image/heic",
        "application/pdf",
    }

    def generate_object_key(
        self,
        purpose: str,
        tenant_id: str,
        file_name: str,
    ) -> str:
        """
        Build a deterministic, collision-free S3 key.

        Pattern: <purpose>/<tenant_id>/<year>/<uuid>.<ext>
        e.g.: profile_photo/abc-123/2025/ebf1234-...jpg
        """
        ext = file_name.rsplit(".", 1)[-1].lower() if "." in file_name else "bin"
        year = datetime.now(tz=timezone.utc).year
        return f"{purpose}/{tenant_id}/{year}/{uuid.uuid4()}.{ext}"

    def generate_presigned_put(
        self,
        purpose: str,
        tenant_id: str,
        file_name: str,
        content_type: str,
    ) -> tuple[str, str]:
        """
        Generate a pre-signed PUT URL and return (upload_url, object_key).

        The client should PUT the file bytes to upload_url with the
        Content-Type header set to content_type.

        Raises:
            ValueError – for invalid purpose or content type.
            RuntimeError – if AWS SDK returns an error.
        """
        if purpose not in self.ALLOWED_PURPOSES:
            raise ValueError(f"Invalid purpose: {purpose}")
        if content_type not in self.ALLOWED_CONTENT_TYPES:
            raise ValueError(f"Unsupported content type: {content_type}")

        object_key = self.generate_object_key(purpose, tenant_id, file_name)

        try:
            url = _s3_client.generate_presigned_url(
                "put_object",
                Params={
                    "Bucket": settings.S3_BUCKET_NAME,
                    "Key": object_key,
                    "ContentType": content_type,
                    # Server-side encryption at rest (AES-256)
                    "ServerSideEncryption": "AES256",
                },
                ExpiresIn=settings.S3_PRESIGNED_URL_EXPIRY,
                HttpMethod="PUT",
            )
        except (BotoCoreError, ClientError) as exc:
            raise RuntimeError(f"S3 pre-signed URL generation failed: {exc}") from exc

        return url, object_key

    def delete_object(self, object_key: str) -> None:
        """Soft-delete: actually removes from S3 (versioning handles recovery)."""
        try:
            _s3_client.delete_object(
                Bucket=settings.S3_BUCKET_NAME,
                Key=object_key,
            )
        except (BotoCoreError, ClientError) as exc:
            raise RuntimeError(f"S3 delete failed: {exc}") from exc
