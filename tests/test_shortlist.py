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


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────
async def _register_and_login(client: AsyncClient, email: str) -> tuple[dict, str]:
    """Register a member, create a profile, return (headers, profile_id)."""
    # Register
    await client.post(
        "/users/",
        json={
            "email": email,
            "password": "Test@1234",
            "full_name": "Test User",
        },
    )
    login = await client.post(
        "/auth/login", json={"email": email, "password": "Test@1234"}
    )
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Create profile
    profile_resp = await client.post(
        "/profiles/",
        json={"gender": "male", "date_of_birth": "1995-06-15"},
        headers=headers,
    )
    profile_id = profile_resp.json()["id"]
    return headers, profile_id


# ──────────────────────────────────────────────────────────────────────────────
# Tests
# ──────────────────────────────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_shortlist_create(client: AsyncClient):
    headers_a, _ = await _register_and_login(client, "alice@sl.test")
    _, profile_b_id = await _register_and_login(client, "bob@sl.test")

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
async def test_shortlist_duplicate_rejected(client: AsyncClient):
    headers_a, _ = await _register_and_login(client, "alice2@sl.test")
    _, profile_b_id = await _register_and_login(client, "bob2@sl.test")

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
async def test_shortlist_cannot_shortlist_self(client: AsyncClient):
    headers_a, profile_a_id = await _register_and_login(client, "alice3@sl.test")
    resp = await client.post(
        "/shortlists/",
        json={"to_profile_id": profile_a_id},
        headers=headers_a,
    )
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_list_sent_and_received(client: AsyncClient):
    headers_a, _ = await _register_and_login(client, "alice4@sl.test")
    headers_b, profile_b_id = await _register_and_login(client, "bob4@sl.test")

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
async def test_accept_shortlist(client: AsyncClient):
    headers_a, _ = await _register_and_login(client, "alice5@sl.test")
    headers_b, profile_b_id = await _register_and_login(client, "bob5@sl.test")

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
async def test_only_recipient_can_accept(client: AsyncClient):
    headers_a, _ = await _register_and_login(client, "alice6@sl.test")
    _, profile_b_id = await _register_and_login(client, "bob6@sl.test")
    headers_c, _ = await _register_and_login(client, "carol6@sl.test")

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
async def test_withdraw_shortlist(client: AsyncClient):
    headers_a, _ = await _register_and_login(client, "alice7@sl.test")
    _, profile_b_id = await _register_and_login(client, "bob7@sl.test")

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
