"""
routers/files.py – File upload via S3 pre-signed PUT URLs.

Flow:
  1. Client calls POST /files/presign with file metadata.
  2. Server returns a pre-signed S3 PUT URL + object_key.
  3. Client PUTs the file bytes directly to S3.
  4. Client calls PATCH /profiles/{id}/media with object_key to register it.
"""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.database import get_db
from app.models.profile import Profile
from app.models.tenant import Tenant
from app.models.user import User
from app.schemas.profile import FileUploadRequest, FileUploadResponse
from app.services.s3 import S3Service

router = APIRouter(prefix="/files", tags=["File Upload"])
_s3 = S3Service()


@router.post(
    "/presign",
    response_model=FileUploadResponse,
    summary="Get a pre-signed S3 PUT URL for photo or horoscope upload",
)
async def get_presigned_url(
    payload: FileUploadRequest,
    request: Request,
    current_user: Annotated[User, Depends(get_current_user)],
) -> FileUploadResponse:
    """
    Generate a pre-signed S3 PUT URL.

    - Only authenticated users may request URLs.
    - Object keys are scoped to the tenant to prevent cross-tenant access.
    - The caller must PUT the file to upload_url within the expiry window
      (default 3600 seconds).
    """
    tenant: Tenant | None = request.state.tenant
    if not tenant:
        raise HTTPException(status_code=400, detail="Tenant context required.")

    try:
        upload_url, object_key = _s3.generate_presigned_put(
            purpose=payload.upload_purpose,
            tenant_id=str(tenant.id),
            file_name=payload.file_name,
            content_type=payload.content_type,
        )
    except (ValueError, RuntimeError) as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    return FileUploadResponse(upload_url=upload_url, object_key=object_key)


@router.patch(
    "/profiles/{profile_id}/media",
    summary="Register an uploaded S3 object key on a profile",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def register_media(
    profile_id: uuid.UUID,
    object_key: str,
    purpose: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> None:
    """
    After a successful S3 PUT, call this endpoint to persist the object_key.

    - purpose = "profile_photo" → appended to photo_keys list
    - purpose = "horoscope"     → stored in horoscope_key (overwrites)
    """
    profile = await db.get(Profile, profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found.")

    # Basic ownership check
    if (
        profile.user_id != current_user.id
        and profile.tenant_id != current_user.tenant_id
    ):
        raise HTTPException(status_code=403, detail="Access denied.")

    if purpose == "profile_photo":
        # Append to array; initialise if None
        keys = list(profile.photo_keys or [])
        keys.append(object_key)
        profile.photo_keys = keys
    elif purpose == "horoscope":
        profile.horoscope_key = object_key
    else:
        raise HTTPException(status_code=400, detail=f"Unknown purpose: {purpose}")

    await db.flush()
