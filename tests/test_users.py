"""
tests/test_users.py – Unit tests for user onboarding and authentication.

Tests cover:
  - Member registration (POST /users/)
  - Login to get JWT (POST /auth/login)
  - Admin onboarding (POST /users/admin)
  - Weak password rejection
  - Duplicate email rejection
  - GET /users/me
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.jwt import create_access_token
from app.models.user import UserRole
from tests.conftest import make_tenant, make_user


def _auth_header(user) -> dict:
    token = create_access_token(user.id, user.tenant_id, user.role.value)
    return {"Authorization": f"Bearer {token}"}


def _tenant_header(tenant) -> dict:
    """Simulate TenantMiddleware by passing the tenant ID header."""
    return {"X-Tenant-ID": str(tenant.id)}


# ── Member registration ────────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_member_registration_success(client: AsyncClient, db: AsyncSession):
    """A valid member registration should return 201 and user JSON."""
    tenant = await make_tenant(db, slug="reg-tenant")

    response = await client.post(
        "/users/",
        json={
            "email": "john.doe@example.com",
            "password": "Strong@123",
            "full_name": "John Doe",
            "phone": "+919999999999",
        },
        headers=_tenant_header(tenant),
    )
    assert response.status_code == 201, response.text
    data = response.json()
    assert data["email"] == "john.doe@example.com"
    assert data["role"] == "member"
    assert "hashed_password" not in data  # never expose hash


@pytest.mark.asyncio
async def test_member_registration_weak_password(client: AsyncClient, db: AsyncSession):
    """Registering with a weak password must return 422."""
    tenant = await make_tenant(db, slug="weak-pwd-tenant")

    response = await client.post(
        "/users/",
        json={
            "email": "weak@example.com",
            "password": "password",   # no uppercase, digit, special char
            "full_name": "Weak User",
        },
        headers=_tenant_header(tenant),
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_member_registration_duplicate_email(client: AsyncClient, db: AsyncSession):
    """Registering the same email twice must return 409."""
    tenant = await make_tenant(db, slug="dup-email-tenant")
    existing = await make_user(db, tenant=tenant, email="dup@example.com")

    response = await client.post(
        "/users/",
        json={
            "email": "dup@example.com",
            "password": "Strong@1234",
            "full_name": "Dup User",
        },
        headers=_tenant_header(tenant),
    )
    assert response.status_code == 409


# ── Authentication ─────────────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_login_success(client: AsyncClient, db: AsyncSession):
    """Correct credentials must return access + refresh tokens."""
    tenant = await make_tenant(db, slug="login-tenant")
    user = await make_user(db, tenant=tenant, email="login@example.com")

    response = await client.post(
        "/auth/login",
        json={"email": "login@example.com", "password": "Test@1234"},
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient, db: AsyncSession):
    """Wrong password must return 401."""
    tenant = await make_tenant(db, slug="badpwd-tenant")
    user = await make_user(db, tenant=tenant, email="badpwd@example.com")

    response = await client.post(
        "/auth/login",
        json={"email": "badpwd@example.com", "password": "WrongPassword!"},
    )
    assert response.status_code == 401


# ── Admin onboarding ───────────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_admin_onboarding_by_super_admin(client: AsyncClient, db: AsyncSession):
    """Super-admin should be able to create an admin for any tenant."""
    super_admin = await make_user(db, tenant=None, role=UserRole.SUPER_ADMIN, tenant_id=None)
    tenant = await make_tenant(db, slug="admin-ob-tenant")

    response = await client.post(
        "/users/admin",
        json={
            "email": "newadmin@example.com",
            "password": "Admin@1234",
            "full_name": "New Admin",
            "role": "admin",
            "tenant_id": str(tenant.id),
        },
        headers=_auth_header(super_admin),
    )
    assert response.status_code == 201, response.text
    assert response.json()["role"] == "admin"


@pytest.mark.asyncio
async def test_admin_cannot_onboard_admin_for_other_tenant(
    client: AsyncClient, db: AsyncSession
):
    """An admin of tenant A must not create an admin for tenant B."""
    tenant_a = await make_tenant(db, slug="tenant-a-ob")
    tenant_b = await make_tenant(db, slug="tenant-b-ob")
    admin_a = await make_user(db, tenant=tenant_a, role=UserRole.ADMIN)

    response = await client.post(
        "/users/admin",
        json={
            "email": "crossadmin@example.com",
            "password": "Admin@1234",
            "full_name": "Cross Admin",
            "role": "admin",
            "tenant_id": str(tenant_b.id),  # different tenant
        },
        headers=_auth_header(admin_a),
    )
    assert response.status_code == 403


# ── GET /users/me ──────────────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_get_me(client: AsyncClient, db: AsyncSession):
    tenant = await make_tenant(db, slug="get-me-tenant")
    user = await make_user(db, tenant=tenant)

    response = await client.get("/users/me", headers=_auth_header(user))
    assert response.status_code == 200
    assert response.json()["id"] == str(user.id)


@pytest.mark.asyncio
async def test_get_me_unauthenticated(client: AsyncClient):
    response = await client.get("/users/me")
    assert response.status_code == 403  # HTTPBearer returns 403 when no credentials
