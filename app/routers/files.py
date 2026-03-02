"""
routers/files.py – File upload via S3 pre-signed PUT URLs.

Flow (photos / horoscope):
  1. Client calls POST /files/presign with file metadata.
  2. Server returns a pre-signed S3 PUT URL + object_key.
  3. Client PUTs the file bytes directly to S3.
  4. Client calls PATCH /profiles/{id}/media with object_key to register it.

Flow (avatar – user profile picture):
  1. Client calls POST /files/avatar/presign.
  2. Client PUTs the file directly to S3.
  3. Client calls PATCH /users/me/avatar to persist the object_key.

Flow (tenant logo):
  1. Client calls POST /files/avatar/presign?purpose=tenant_logo.
  2. Client PUTs the file directly to S3.
  3. Client calls PATCH /files/tenant/logo to persist the object_key.

Viewing private objects:
  - GET /files/presign-get?key=<object_key> → short-lived GET URL for display.
"""

import uuid
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user, require_admin
from app.database import get_db
from app.models.profile import Profile
from app.models.tenant import Tenant
from app.models.user import User
from app.schemas.profile import FileUploadRequest, FileUploadResponse
from app.services.s3 import S3Service

router = APIRouter(prefix="/files", tags=["File Upload"])
_s3 = S3Service()


class PresignedGetResponse(BaseModel):
    url: str
    expires_in: int = 900


class AvatarPresignRequest(BaseModel):
    file_name: str
    content_type: str
    purpose: Literal["avatar", "tenant_logo"] = "avatar"


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


# ── Avatar / tenant logo endpoints ────────────────────────────────────────────

@router.post(
    "/avatar/presign",
    response_model=FileUploadResponse,
    summary="Get a pre-signed S3 PUT URL for a user avatar or tenant logo",
)
async def get_avatar_presigned_url(
    payload: AvatarPresignRequest,
    request: Request,
    current_user: Annotated[User, Depends(get_current_user)],
) -> FileUploadResponse:
    """
    Generate a presigned PUT URL for avatar (any user type) or tenant logo.

    - purpose = "avatar"       → for member or admin profile picture
    - purpose = "tenant_logo"  → for tenant branding logo (admin+ only)
    """
    tenant: Tenant | None = request.state.tenant

    if payload.purpose == "tenant_logo" and not tenant:
        raise HTTPException(status_code=400, detail="Tenant context required for tenant_logo.")

    tenant_id = str(tenant.id) if tenant else str(current_user.id)

    try:
        upload_url, object_key = _s3.generate_presigned_put(
            purpose=payload.purpose,
            tenant_id=tenant_id,
            file_name=payload.file_name,
            content_type=payload.content_type,
        )
    except (ValueError, RuntimeError) as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    return FileUploadResponse(upload_url=upload_url, object_key=object_key)


@router.patch(
    "/users/me/avatar",
    summary="Register an uploaded avatar S3 object key on the current user",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def register_avatar(
    object_key: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> None:
    """
    After a successful S3 PUT, persist the avatar object_key on the current user.
    Replaces any previously stored avatar.
    """
    current_user.avatar_key = object_key
    await db.flush()


@router.patch(
    "/tenant/logo",
    summary="Register an uploaded logo S3 object key on the current tenant",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def register_tenant_logo(
    object_key: str,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_admin)],
) -> None:
    """
    After a successful S3 PUT, persist the logo object_key on the tenant.
    Requires admin role. Replaces any previously stored logo.
    """
    tenant: Tenant | None = request.state.tenant
    if not tenant:
        raise HTTPException(status_code=400, detail="Tenant context required.")

    tenant.logo_key = object_key
    await db.flush()


@router.get(
    "/presign-get",
    response_model=PresignedGetResponse,
    summary="Get a short-lived presigned GET URL to display a private S3 object",
)
async def get_presigned_view_url(
    key: str,
    current_user: Annotated[User, Depends(get_current_user)],
) -> PresignedGetResponse:
    """
    Returns a time-limited (15 min) HTTPS URL the browser can use to display
    a private S3 object (photo, avatar, horoscope, logo).

    The caller must be authenticated; no further ownership check is performed
    here so that admins can preview any member's files.
    """
    try:
        url = _s3.generate_presigned_get(key, expiry=900)
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    return PresignedGetResponse(url=url, expires_in=900)


@router.delete(
    "/profiles/{profile_id}/photos",
    summary="Remove a photo from a profile (deletes S3 object and deregisters key)",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_photo(
    profile_id: uuid.UUID,
    object_key: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> None:
    """Remove a single photo from the profile's photo_keys list and delete from S3."""
    profile = await db.get(Profile, profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found.")

    if (
        profile.user_id != current_user.id
        and profile.tenant_id != current_user.tenant_id
    ):
        raise HTTPException(status_code=403, detail="Access denied.")

    keys = list(profile.photo_keys or [])
    if object_key not in keys:
        raise HTTPException(status_code=404, detail="Photo key not found on profile.")

    keys.remove(object_key)
    profile.photo_keys = keys
    await db.flush()

    # Best-effort S3 delete; don't fail the request if S3 deletion fails
    try:
        _s3.delete_object(object_key)
    except RuntimeError:
        pass  # Log in production; S3 versioning allows recovery
