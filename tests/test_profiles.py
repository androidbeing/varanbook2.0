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
from app.models.user import User, UserRole
from app.models.tenant import Tenant
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
    assert data["status"] == "active"  # self-service profiles are active immediately


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
async def test_member_can_view_active_profile_in_same_tenant(
    client: AsyncClient, db: AsyncSession
):
    """Member A can browse active profiles of other members in the same tenant."""
    tenant = await make_tenant(db, slug="prof-cross")
    user_a = await make_user(db, tenant=tenant)
    user_b = await make_user(db, tenant=tenant, email="b@example.com")

    # Create profile as user_b (becomes active immediately)
    create_resp = await client.post(
        "/profiles/", json=_valid_profile_payload(), headers=_auth_header(user_b)
    )
    assert create_resp.status_code == 201, create_resp.text
    profile_id = create_resp.json()["id"]

    # Member A can view the active profile
    response = await client.get(
        f"/profiles/{profile_id}", headers=_auth_header(user_a)
    )
    assert response.status_code == 200


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
        json={"city": "Pune", "profession": "Software Engineer"},
        headers=_auth_header(user),
    )
    assert patch_resp.status_code == 200
    data = patch_resp.json()
    assert data["city"] == "Pune"
    assert data["profession"] == "Software Engineer"


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


# ── Privacy controls + accepted shortlist ────────────────────────────────────
# Helper: register user, create a profile, return (user, headers, profile_id).
async def _setup_member(
    client: AsyncClient,
    db,
    email: str,
    gender: str = "male",
    *,
    slug_suffix: str = "",
) -> tuple:
    tenant = await make_tenant(db, slug=f"priv{slug_suffix}-{email[:6]}")
    user = await make_user(db, tenant=tenant, email=email)
    headers = _auth_header(user)
    resp = await client.post(
        "/profiles/",
        json=_valid_profile_payload(gender=gender),
        headers=headers,
    )
    assert resp.status_code == 201
    profile_id = resp.json()["id"]
    return user, headers, profile_id, tenant


@pytest.mark.asyncio
async def test_privacy_flags_hide_sections_from_stranger(
    client: AsyncClient, db
):
    """A member without a shortlist connection sees private fields as 'hidden'
    (enforced on the frontend), and the API returns connection_status=null."""
    from sqlalchemy import select

    _, _, profile_b_id, _ = await _setup_member(
        client, db, "priv_b1@test.com", "female", slug_suffix="b1"
    )
    # Create user_a in the SAME tenant; activate profile_b so it's visible
    result = await db.execute(select(Profile).where(Profile.id == uuid.UUID(profile_b_id)))
    profile_b = result.scalar_one()
    profile_b.status = ProfileStatus.ACTIVE
    await db.flush()
    tenant_result = await db.execute(
        select(Tenant).where(Tenant.id == profile_b.tenant_id)
    )
    tenant = tenant_result.scalar_one()
    user_a = await make_user(db, tenant=tenant, email="priv_a1@test.com")
    # user_a also needs a profile (required for opposite-gender access check)
    await client.post(
        "/profiles/",
        json=_valid_profile_payload(gender="male"),
        headers=_auth_header(user_a),
    )

    # user_b profile has all privacy flags False (default)
    # user_a (no shortlist) fetches user_b's profile → connection_status null
    resp = await client.get(
        f"/profiles/{profile_b_id}",
        headers=_auth_header(user_a),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["connection_status"] is None
    # Privacy flags are whatever the profile owner set (all False by default)
    assert data["photo_visible"] is False
    assert data["birth_visible"] is False


@pytest.mark.asyncio
async def test_accepted_connection_returns_connection_status(
    client: AsyncClient, db
):
    """After A→B shortlist is accepted, both A and B get connection_status='accepted'."""
    from sqlalchemy import select

    _, headers_a, profile_a_id, _ = await _setup_member(
        client, db, "acc_a@test.com", "male", slug_suffix="acc"
    )
    # B must be in the same tenant
    result = await db.execute(select(Profile).where(Profile.id == uuid.UUID(profile_a_id)))
    profile_a = result.scalar_one()
    tenant_result = await db.execute(
        select(Tenant).where(Tenant.id == profile_a.tenant_id)
    )
    tenant = tenant_result.scalar_one()
    user_b = await make_user(db, tenant=tenant, email="acc_b@test.com")
    headers_b = _auth_header(user_b)
    create_resp = await client.post(
        "/profiles/",
        json=_valid_profile_payload(gender="female"),
        headers=headers_b,
    )
    assert create_resp.status_code == 201
    profile_b_id = create_resp.json()["id"]

    # A shortlists B
    sl_resp = await client.post(
        "/shortlists/",
        json={"to_profile_id": profile_b_id},
        headers=headers_a,
    )
    assert sl_resp.status_code == 201
    sl_id = sl_resp.json()["id"]

    # B accepts
    accept_resp = await client.patch(
        f"/shortlists/{sl_id}",
        json={"status": "accepted"},
        headers=headers_b,
    )
    assert accept_resp.status_code == 200

    # A views B's profile → connection_status = "accepted"
    resp_a = await client.get(f"/profiles/{profile_b_id}", headers=headers_a)
    assert resp_a.status_code == 200
    assert resp_a.json()["connection_status"] == "accepted"

    # B views A's profile → connection_status = "accepted" (bidirectional)
    resp_b = await client.get(f"/profiles/{profile_a_id}", headers=headers_b)
    assert resp_b.status_code == 200
    assert resp_b.json()["connection_status"] == "accepted"


@pytest.mark.asyncio
async def test_pending_shortlist_does_not_grant_connection_status(
    client: AsyncClient, db
):
    """A shortlist that is still pending (not accepted) must NOT set connection_status."""
    from sqlalchemy import select

    _, headers_a, _, _ = await _setup_member(
        client, db, "pend_a@test.com", "male", slug_suffix="pend"
    )
    user_a_result = await db.execute(
        select(User).where(User.email == "pend_a@test.com")
    )
    user_a = user_a_result.scalar_one()
    tenant_result = await db.execute(
        select(Tenant).where(Tenant.id == user_a.tenant_id)
    )
    tenant = tenant_result.scalar_one()
    user_b = await make_user(db, tenant=tenant, email="pend_b@test.com")
    headers_b = _auth_header(user_b)
    create_resp = await client.post(
        "/profiles/",
        json=_valid_profile_payload(gender="female"),
        headers=headers_b,
    )
    profile_b_id = create_resp.json()["id"]

    # Activate profile_b so a non-connected member can still view it (status=200)
    result = await db.execute(select(Profile).where(Profile.id == uuid.UUID(profile_b_id)))
    pend_profile_b = result.scalar_one()
    pend_profile_b.status = ProfileStatus.ACTIVE
    await db.flush()

    # A shortlists B but B does NOT accept
    await client.post(
        "/shortlists/",
        json={"to_profile_id": profile_b_id},
        headers=headers_a,
    )

    # A views B's profile → connection_status must be null (not accepted yet)
    resp = await client.get(f"/profiles/{profile_b_id}", headers=headers_a)
    assert resp.status_code == 200
    assert resp.json()["connection_status"] is None


@pytest.mark.asyncio
async def test_accepted_connection_allows_access_regardless_of_profile_status(
    client: AsyncClient, db
):
    """
    Even if the target profile is DRAFT (not ACTIVE), an accepted connection
    must still be able to view it (the status restriction is bypassed).
    """
    from sqlalchemy import select

    _, headers_a, _, _ = await _setup_member(
        client, db, "draft_a@test.com", "male", slug_suffix="draft"
    )
    user_a_result = await db.execute(
        select(User).where(User.email == "draft_a@test.com")
    )
    user_a = user_a_result.scalar_one()
    tenant_result = await db.execute(
        select(Tenant).where(Tenant.id == user_a.tenant_id)
    )
    tenant = tenant_result.scalar_one()
    user_b = await make_user(db, tenant=tenant, email="draft_b@test.com")
    headers_b = _auth_header(user_b)
    create_resp = await client.post(
        "/profiles/",
        json=_valid_profile_payload(gender="female"),
        headers=headers_b,
    )
    profile_b_id = create_resp.json()["id"]

    # Force profile_b to DRAFT status directly
    result = await db.execute(select(Profile).where(Profile.id == uuid.UUID(profile_b_id)))
    profile_b = result.scalar_one()
    profile_b.status = ProfileStatus.DRAFT
    await db.flush()

    # A shortlists B and B accepts
    sl_resp = await client.post(
        "/shortlists/",
        json={"to_profile_id": profile_b_id},
        headers=headers_a,
    )
    sl_id = sl_resp.json()["id"]
    await client.patch(
        f"/shortlists/{sl_id}", json={"status": "accepted"}, headers=headers_b
    )

    # A can now view B's DRAFT profile because of the accepted connection
    resp = await client.get(f"/profiles/{profile_b_id}", headers=headers_a)
    assert resp.status_code == 200
    assert resp.json()["connection_status"] == "accepted"
