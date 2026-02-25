"""
routers/tenant.py – Tenant onboarding endpoints.

All routes here require SUPER_ADMIN role.
Tenants are the top-level multi-tenant entities (matrimonial centres).
"""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import require_super_admin
from app.database import get_db
from app.models.tenant import Tenant
from app.models.user import User
from app.schemas.tenant import TenantCreate, TenantList, TenantRead, TenantUpdate

router = APIRouter(prefix="/admin/tenants", tags=["Tenant Management"])


@router.post(
    "/",
    response_model=TenantRead,
    status_code=status.HTTP_201_CREATED,
    summary="Onboard a new matrimonial centre (tenant)",
)
async def create_tenant(
    payload: TenantCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_super_admin)],
) -> TenantRead:
    """
    Create a new tenant/matrimonial centre.

    - slug must be globally unique
    - only SUPER_ADMINs can create tenants
    """
    tenant = Tenant(**payload.model_dump())
    db.add(tenant)
    try:
        await db.flush()  # catch DB constraint errors before commit
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Tenant with slug '{payload.slug}' already exists.",
        )
    await db.refresh(tenant)
    return TenantRead.model_validate(tenant)


@router.get(
    "/",
    response_model=TenantList,
    summary="List all tenants (paginated)",
)
async def list_tenants(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_super_admin)],
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    is_active: bool | None = Query(None),
) -> TenantList:
    """Return paginated list of tenants. Optionally filter by active status."""
    query = select(Tenant)
    if is_active is not None:
        query = query.where(Tenant.is_active == is_active)

    total_result = await db.execute(select(func.count()).select_from(query.subquery()))
    total = total_result.scalar_one()

    items_result = await db.execute(
        query.offset((page - 1) * page_size).limit(page_size)
    )
    items = [TenantRead.model_validate(t) for t in items_result.scalars().all()]

    return TenantList(items=items, total=total, page=page, page_size=page_size)


@router.get(
    "/{tenant_id}",
    response_model=TenantRead,
    summary="Get a single tenant by ID",
)
async def get_tenant(
    tenant_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_super_admin)],
) -> TenantRead:
    tenant = await db.get(Tenant, tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found.")
    return TenantRead.model_validate(tenant)


@router.patch(
    "/{tenant_id}",
    response_model=TenantRead,
    summary="Update tenant details",
)
async def update_tenant(
    tenant_id: uuid.UUID,
    payload: TenantUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_super_admin)],
) -> TenantRead:
    tenant = await db.get(Tenant, tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found.")

    # Apply only the provided fields (partial update)
    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(tenant, field, value)

    await db.flush()
    await db.refresh(tenant)
    return TenantRead.model_validate(tenant)


@router.delete(
    "/{tenant_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Soft-deactivate a tenant",
)
async def deactivate_tenant(
    tenant_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_super_admin)],
) -> None:
    tenant = await db.get(Tenant, tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found.")
    tenant.is_active = False
    await db.flush()
