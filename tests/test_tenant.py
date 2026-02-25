"""
tests/test_tenant.py – Unit tests for tenant onboarding endpoints.

Tests cover:
  - POST /admin/tenants  (super-admin only)
  - GET  /admin/tenants
  - PATCH /admin/tenants/{id}
  - Duplicate slug validation
  - Role-based access control (RBAC)
"""

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.jwt import create_access_token
from app.models.user import UserRole
from tests.conftest import make_tenant, make_user


def _auth_header(user) -> dict:
    """Generate a Bearer token header for the given user."""
    token = create_access_token(user.id, user.tenant_id, user.role.value)
    return {"Authorization": f"Bearer {token}"}


# ── POST /admin/tenants ────────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_create_tenant_as_super_admin(
    client: AsyncClient, db: AsyncSession
):
    """Super-admin should successfully create a tenant."""
    # Arrange: create a super-admin user (no tenant)
    super_admin = await make_user(db, tenant=None, role=UserRole.SUPER_ADMIN, tenant_id=None)

    payload = {
        "name": "Sharma Vivah Kendra",
        "slug": "sharma-vivah",
        "contact_email": "sharma@example.com",
        "plan": "growth",
        "max_users": 1000,
        "max_admins": 10,
    }

    # Act
    response = await client.post(
        "/admin/tenants/",
        json=payload,
        headers=_auth_header(super_admin),
    )

    # Assert
    assert response.status_code == 201, response.text
    data = response.json()
    assert data["slug"] == "sharma-vivah"
    assert data["plan"] == "growth"
    assert data["is_active"] is True
    assert "id" in data


@pytest.mark.asyncio
async def test_create_tenant_as_regular_admin_forbidden(
    client: AsyncClient, db: AsyncSession
):
    """A tenant ADMIN must not be able to create new tenants."""
    tenant = await make_tenant(db)
    admin = await make_user(db, tenant=tenant, role=UserRole.ADMIN)

    response = await client.post(
        "/admin/tenants/",
        json={
            "name": "Another Centre",
            "slug": "another-centre",
            "contact_email": "x@example.com",
        },
        headers=_auth_header(admin),
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_create_tenant_duplicate_slug(
    client: AsyncClient, db: AsyncSession
):
    """Creating two tenants with the same slug should return 409."""
    super_admin = await make_user(db, tenant=None, role=UserRole.SUPER_ADMIN, tenant_id=None)
    await make_tenant(db, slug="dup-slug")

    response = await client.post(
        "/admin/tenants/",
        json={
            "name": "Duplicate",
            "slug": "dup-slug",
            "contact_email": "dup@example.com",
        },
        headers=_auth_header(super_admin),
    )
    assert response.status_code == 409


# ── GET /admin/tenants ────────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_list_tenants(client: AsyncClient, db: AsyncSession):
    super_admin = await make_user(db, tenant=None, role=UserRole.SUPER_ADMIN, tenant_id=None)
    await make_tenant(db, slug="list-t1")
    await make_tenant(db, slug="list-t2")

    response = await client.get(
        "/admin/tenants/", headers=_auth_header(super_admin)
    )
    assert response.status_code == 200
    body = response.json()
    assert body["total"] >= 2
    assert isinstance(body["items"], list)


# ── PATCH /admin/tenants/{id} ─────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_update_tenant_plan(client: AsyncClient, db: AsyncSession):
    super_admin = await make_user(db, tenant=None, role=UserRole.SUPER_ADMIN, tenant_id=None)
    tenant = await make_tenant(db, slug="upd-slug", plan="starter")

    response = await client.patch(
        f"/admin/tenants/{tenant.id}",
        json={"plan": "enterprise"},
        headers=_auth_header(super_admin),
    )
    assert response.status_code == 200
    assert response.json()["plan"] == "enterprise"


@pytest.mark.asyncio
async def test_deactivate_tenant(client: AsyncClient, db: AsyncSession):
    super_admin = await make_user(db, tenant=None, role=UserRole.SUPER_ADMIN, tenant_id=None)
    tenant = await make_tenant(db, slug="deact-slug")

    response = await client.delete(
        f"/admin/tenants/{tenant.id}", headers=_auth_header(super_admin)
    )
    assert response.status_code == 204


# ── Pydantic slug validation ──────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_invalid_slug_rejected(client: AsyncClient, db: AsyncSession):
    """Slugs with uppercase or special chars (other than -) must be rejected."""
    super_admin = await make_user(db, tenant=None, role=UserRole.SUPER_ADMIN, tenant_id=None)

    response = await client.post(
        "/admin/tenants/",
        json={
            "name": "Bad Slug",
            "slug": "UPPERCASE_SLUG",   # invalid
            "contact_email": "bad@example.com",
        },
        headers=_auth_header(super_admin),
    )
    assert response.status_code == 422  # Pydantic validation error
