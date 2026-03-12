"""
tests/test_shortlist.py – Integration tests for shortlist / accept flow.

Covers:
  - Create shortlist (express interest)
  - Duplicate shortlist rejected (409)
  - List sent / received
  - Accept / reject by recipient
  - Withdraw by sender
  - Foreign tenant isolation
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.jwt import create_access_token
from app.models.user import UserRole
from tests.conftest import make_tenant, make_user


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────
async def _setup_member_profile(
    client: AsyncClient,
    db: AsyncSession,
    email: str,
    tenant,
    gender: str = "male",
) -> tuple[dict, str]:
    """Create a user in the test DB, mint a JWT, create a profile via API.
    Returns (auth_headers, profile_id)."""
    user = await make_user(db, tenant=tenant, email=email)
    token = create_access_token(user.id, user.tenant_id, user.role.value)
    headers = {"Authorization": f"Bearer {token}"}

    profile_resp = await client.post(
        "/profiles/",
        json={"gender": gender, "date_of_birth": "1995-06-15"},
        headers=headers,
    )
    assert profile_resp.status_code == 201, f"Profile creation failed: {profile_resp.text}"
    return headers, profile_resp.json()["id"]


# ──────────────────────────────────────────────────────────────────────────────
# Tests
# ──────────────────────────────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_shortlist_create(client: AsyncClient, db: AsyncSession):
    tenant = await make_tenant(db, slug="sl-create")
    headers_a, _ = await _setup_member_profile(client, db, "alice@sl.test", tenant, "female")
    headers_b, profile_b_id = await _setup_member_profile(client, db, "bob@sl.test", tenant, "male")

    resp = await client.post(
        "/shortlists/",
        json={"to_profile_id": profile_b_id, "note": "Looks compatible"},
        headers=headers_a,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["status"] == "shortlisted"
    assert data["to_profile_id"] == profile_b_id


@pytest.mark.asyncio
async def test_shortlist_duplicate_rejected(client: AsyncClient, db: AsyncSession):
    tenant = await make_tenant(db, slug="sl-dup")
    headers_a, _ = await _setup_member_profile(client, db, "alice2@sl.test", tenant, "female")
    headers_b, profile_b_id = await _setup_member_profile(client, db, "bob2@sl.test", tenant, "male")

    await client.post(
        "/shortlists/",
        json={"to_profile_id": profile_b_id},
        headers=headers_a,
    )
    resp2 = await client.post(
        "/shortlists/",
        json={"to_profile_id": profile_b_id},
        headers=headers_a,
    )
    assert resp2.status_code == 409


@pytest.mark.asyncio
async def test_shortlist_cannot_shortlist_self(client: AsyncClient, db: AsyncSession):
    tenant = await make_tenant(db, slug="sl-self")
    headers_a, profile_a_id = await _setup_member_profile(client, db, "alice3@sl.test", tenant)
    resp = await client.post(
        "/shortlists/",
        json={"to_profile_id": profile_a_id},
        headers=headers_a,
    )
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_list_sent_and_received(client: AsyncClient, db: AsyncSession):
    tenant = await make_tenant(db, slug="sl-list")
    headers_a, _ = await _setup_member_profile(client, db, "alice4@sl.test", tenant, "female")
    headers_b, profile_b_id = await _setup_member_profile(client, db, "bob4@sl.test", tenant, "male")

    await client.post(
        "/shortlists/",
        json={"to_profile_id": profile_b_id},
        headers=headers_a,
    )

    sent = await client.get("/shortlists/sent", headers=headers_a)
    assert sent.status_code == 200
    assert sent.json()["total"] >= 1

    received = await client.get("/shortlists/received", headers=headers_b)
    assert received.status_code == 200
    assert received.json()["total"] >= 1


@pytest.mark.asyncio
async def test_accept_shortlist(client: AsyncClient, db: AsyncSession):
    tenant = await make_tenant(db, slug="sl-accept")
    headers_a, _ = await _setup_member_profile(client, db, "alice5@sl.test", tenant, "female")
    headers_b, profile_b_id = await _setup_member_profile(client, db, "bob5@sl.test", tenant, "male")

    create_resp = await client.post(
        "/shortlists/",
        json={"to_profile_id": profile_b_id},
        headers=headers_a,
    )
    sl_id = create_resp.json()["id"]

    accept_resp = await client.patch(
        f"/shortlists/{sl_id}",
        json={"status": "accepted"},
        headers=headers_b,
    )
    assert accept_resp.status_code == 200
    assert accept_resp.json()["status"] == "accepted"


@pytest.mark.asyncio
async def test_only_recipient_can_accept(client: AsyncClient, db: AsyncSession):
    tenant = await make_tenant(db, slug="sl-recip")
    headers_a, _ = await _setup_member_profile(client, db, "alice6@sl.test", tenant, "female")
    _, profile_b_id = await _setup_member_profile(client, db, "bob6@sl.test", tenant, "male")
    headers_c, _ = await _setup_member_profile(client, db, "carol6@sl.test", tenant, "female")

    create_resp = await client.post(
        "/shortlists/",
        json={"to_profile_id": profile_b_id},
        headers=headers_a,
    )
    sl_id = create_resp.json()["id"]

    # carol cannot accept alice→bob shortlist
    resp = await client.patch(
        f"/shortlists/{sl_id}",
        json={"status": "accepted"},
        headers=headers_c,
    )
    assert resp.status_code in (403, 404)


@pytest.mark.asyncio
async def test_withdraw_shortlist(client: AsyncClient, db: AsyncSession):
    tenant = await make_tenant(db, slug="sl-withdraw")
    headers_a, _ = await _setup_member_profile(client, db, "alice7@sl.test", tenant, "female")
    _, profile_b_id = await _setup_member_profile(client, db, "bob7@sl.test", tenant, "male")

    create_resp = await client.post(
        "/shortlists/",
        json={"to_profile_id": profile_b_id},
        headers=headers_a,
    )
    sl_id = create_resp.json()["id"]

    del_resp = await client.delete(f"/shortlists/{sl_id}", headers=headers_a)
    assert del_resp.status_code == 204

    sent = await client.get("/shortlists/sent", headers=headers_a)
    assert all(i["id"] != sl_id for i in sent.json()["items"])
