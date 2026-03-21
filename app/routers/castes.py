"""
routers/castes.py – Caste master management endpoints.

Admins manage the list of castes for their tenant.
Members can read the list to populate dropdowns.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user, require_admin
from app.database import get_db
from app.models.tenant import Tenant
from app.models.user import User

router = APIRouter(prefix="/castes", tags=["Caste Master"])


class CasteLockStatus(BaseModel):
    caste_locked: bool


@router.get(
    "/",
    response_model=list[str],
    summary="List castes for the current tenant",
)
async def list_castes(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> list[str]:
    """Return the caste list configured for the authenticated user's tenant."""
    if not current_user.tenant_id:
        return []
    tenant = await db.get(Tenant, current_user.tenant_id)
    if not tenant:
        return []
    return tenant.castes or []


@router.put(
    "/",
    response_model=list[str],
    summary="Replace the full caste list (admin only)",
)
async def replace_castes(
    castes: list[str],
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_admin)],
) -> list[str]:
    """Overwrite the tenant's caste list. Duplicates are removed."""
    if not current_user.tenant_id:
        raise HTTPException(status_code=400, detail="User has no tenant.")
    tenant = await db.get(Tenant, current_user.tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found.")
    # Deduplicate while preserving order
    seen: set[str] = set()
    unique: list[str] = []
    for c in castes:
        stripped = c.strip()
        if stripped and stripped not in seen:
            seen.add(stripped)
            unique.append(stripped)
    tenant.castes = unique
    await db.flush()
    await db.refresh(tenant)
    return tenant.castes or []


@router.post(
    "/",
    response_model=list[str],
    status_code=status.HTTP_201_CREATED,
    summary="Add a caste to the tenant list (admin only)",
)
async def add_caste(
    caste: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_admin)],
) -> list[str]:
    """Append a single caste to the tenant's list if not already present."""
    if not current_user.tenant_id:
        raise HTTPException(status_code=400, detail="User has no tenant.")
    tenant = await db.get(Tenant, current_user.tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found.")
    current = list(tenant.castes or [])
    stripped = caste.strip()
    if not stripped:
        raise HTTPException(status_code=422, detail="Caste name cannot be empty.")
    if stripped in current:
        raise HTTPException(status_code=409, detail=f"'{stripped}' already exists.")
    current.append(stripped)
    tenant.castes = current
    await db.flush()
    await db.refresh(tenant)
    return tenant.castes or []


@router.delete(
    "/{caste_name}",
    response_model=list[str],
    summary="Remove a caste from the tenant list (admin only)",
)
async def remove_caste(
    caste_name: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_admin)],
) -> list[str]:
    """Remove a single caste from the tenant's list."""
    if not current_user.tenant_id:
        raise HTTPException(status_code=400, detail="User has no tenant.")
    tenant = await db.get(Tenant, current_user.tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found.")
    current = list(tenant.castes or [])
    if caste_name not in current:
        raise HTTPException(status_code=404, detail=f"'{caste_name}' not found in caste list.")
    current.remove(caste_name)
    tenant.castes = current
    await db.flush()
    await db.refresh(tenant)
    return tenant.castes or []


# ── Caste Lock Toggle ─────────────────────────────────────────────────────────

@router.get(
    "/lock-status",
    response_model=CasteLockStatus,
    summary="Get caste lock status for the current tenant",
)
async def get_lock_status(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> CasteLockStatus:
    """Return whether the tenant has caste-based profile filtering enabled."""
    if not current_user.tenant_id:
        return CasteLockStatus(caste_locked=False)
    tenant = await db.get(Tenant, current_user.tenant_id)
    if not tenant:
        return CasteLockStatus(caste_locked=False)
    return CasteLockStatus(caste_locked=tenant.caste_locked)


@router.put(
    "/lock-status",
    response_model=CasteLockStatus,
    summary="Toggle caste lock (admin only)",
)
async def set_lock_status(
    body: CasteLockStatus,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_admin)],
) -> CasteLockStatus:
    """Enable or disable caste-based profile filtering for the tenant."""
    if not current_user.tenant_id:
        raise HTTPException(status_code=400, detail="User has no tenant.")
    tenant = await db.get(Tenant, current_user.tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found.")
    tenant.caste_locked = body.caste_locked
    await db.flush()
    await db.refresh(tenant)
    return CasteLockStatus(caste_locked=tenant.caste_locked)
