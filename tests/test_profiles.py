"""
tests/test_profiles.py – Unit tests for matrimonial profile CRUD.

Tests cover:
  - Profile creation (POST /profiles/)
  - Duplicate profile rejection
  - Age validation (must be 18+)
  - Profile retrieval by owner (member) and admin
  - Access control: member cannot view another member's profile
  - Profile update (PATCH)
"""

import uuid
from datetime import date

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.jwt import create_access_token
from app.models.profile import Profile, ProfileStatus
from app.models.user import UserRole
from tests.conftest import make_tenant, make_user


def _auth_header(user) -> dict:
    token = create_access_token(user.id, user.tenant_id, user.role.value)
    return {"Authorization": f"Bearer {token}"}


def _valid_profile_payload(**overrides) -> dict:
    """Return a minimal valid profile payload."""
    data = {
        "gender": "male",
        "date_of_birth": "1995-06-15",   # age ~30; passes 18+ check
        "marital_status": "never_married",
        "country": "India",
    }
    data.update(overrides)
    return data


# ── Create profile ────────────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_create_profile_success(client: AsyncClient, db: AsyncSession):
    tenant = await make_tenant(db, slug="prof-create")
    user = await make_user(db, tenant=tenant)

    response = await client.post(
        "/profiles/",
        json=_valid_profile_payload(),
        headers=_auth_header(user),
    )
    assert response.status_code == 201, response.text
    data = response.json()
    assert data["user_id"] == str(user.id)
    assert data["status"] == "draft"


@pytest.mark.asyncio
async def test_create_profile_underage_rejected(client: AsyncClient, db: AsyncSession):
    """A candidate under 18 must be rejected."""
    tenant = await make_tenant(db, slug="prof-underage")
    user = await make_user(db, tenant=tenant)

    response = await client.post(
        "/profiles/",
        json=_valid_profile_payload(date_of_birth="2015-01-01"),  # ~11 years old
        headers=_auth_header(user),
    )
    assert response.status_code == 422
    assert "18" in response.text


@pytest.mark.asyncio
async def test_create_duplicate_profile_rejected(client: AsyncClient, db: AsyncSession):
    """A second profile for the same user must return 409."""
    tenant = await make_tenant(db, slug="prof-dup")
    user = await make_user(db, tenant=tenant)

    # First creation
    await client.post(
        "/profiles/", json=_valid_profile_payload(), headers=_auth_header(user)
    )
    # Second creation
    response = await client.post(
        "/profiles/", json=_valid_profile_payload(), headers=_auth_header(user)
    )
    assert response.status_code == 409


# ── Get profile ───────────────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_member_can_get_own_profile(client: AsyncClient, db: AsyncSession):
    tenant = await make_tenant(db, slug="prof-own")
    user = await make_user(db, tenant=tenant)

    # Create profile
    create_resp = await client.post(
        "/profiles/", json=_valid_profile_payload(), headers=_auth_header(user)
    )
    profile_id = create_resp.json()["id"]

    # Retrieve it
    get_resp = await client.get(
        f"/profiles/{profile_id}", headers=_auth_header(user)
    )
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == profile_id


@pytest.mark.asyncio
async def test_member_cannot_get_other_member_profile(
    client: AsyncClient, db: AsyncSession
):
    """Member A must not be able to read Member B's profile."""
    tenant = await make_tenant(db, slug="prof-cross")
    user_a = await make_user(db, tenant=tenant)
    user_b = await make_user(db, tenant=tenant, email="b@example.com")

    # Create profile as user_b
    create_resp = await client.post(
        "/profiles/", json=_valid_profile_payload(), headers=_auth_header(user_b)
    )
    profile_id = create_resp.json()["id"]

    # Try to access as user_a
    response = await client.get(
        f"/profiles/{profile_id}", headers=_auth_header(user_a)
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_admin_can_get_any_profile_in_tenant(
    client: AsyncClient, db: AsyncSession
):
    """An admin must be able to read any profile within their tenant."""
    tenant = await make_tenant(db, slug="prof-admin-read")
    member = await make_user(db, tenant=tenant)
    admin = await make_user(
        db, tenant=tenant, role=UserRole.ADMIN, email="admin@prof.example.com"
    )

    create_resp = await client.post(
        "/profiles/", json=_valid_profile_payload(), headers=_auth_header(member)
    )
    profile_id = create_resp.json()["id"]

    response = await client.get(
        f"/profiles/{profile_id}", headers=_auth_header(admin)
    )
    assert response.status_code == 200


# ── Update profile ────────────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_update_profile_field(client: AsyncClient, db: AsyncSession):
    tenant = await make_tenant(db, slug="prof-upd")
    user = await make_user(db, tenant=tenant)

    create_resp = await client.post(
        "/profiles/", json=_valid_profile_payload(), headers=_auth_header(user)
    )
    profile_id = create_resp.json()["id"]

    patch_resp = await client.patch(
        f"/profiles/{profile_id}",
        json={"education": "B.Tech Computer Science", "city": "Pune"},
        headers=_auth_header(user),
    )
    assert patch_resp.status_code == 200
    data = patch_resp.json()
    assert data["education"] == "B.Tech Computer Science"
    assert data["city"] == "Pune"


# ── Pydantic validation ───────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_invalid_blood_group_rejected(client: AsyncClient, db: AsyncSession):
    tenant = await make_tenant(db, slug="prof-blood")
    user = await make_user(db, tenant=tenant)

    response = await client.post(
        "/profiles/",
        json=_valid_profile_payload(blood_group="XY"),   # invalid
        headers=_auth_header(user),
    )
    assert response.status_code == 422
