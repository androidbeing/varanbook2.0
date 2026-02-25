"""
tests/test_auth.py – Integration tests for auth flows.

Covers:
  - Login (success + wrong password)
  - Refresh token rotation (DB-backed)
  - Logout (revoke refresh token)
  - Forgot password + reset password
  - Change password
"""

import pytest
from httpx import AsyncClient


# ── Login ──────────────────────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_login_success(client: AsyncClient, make_user):
    user = await make_user(email="auth@test.com", password="Test@1234")
    resp = await client.post(
        "/auth/login",
        json={"email": "auth@test.com", "password": "Test@1234"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient, make_user):
    await make_user(email="auth2@test.com", password="Test@1234")
    resp = await client.post(
        "/auth/login",
        json={"email": "auth2@test.com", "password": "WrongPassword!"},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_login_unknown_user(client: AsyncClient):
    resp = await client.post(
        "/auth/login",
        json={"email": "nobody@test.com", "password": "Test@1234"},
    )
    assert resp.status_code == 401


# ── Refresh ────────────────────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_refresh_token_rotation(client: AsyncClient, make_user):
    await make_user(email="refresh@test.com", password="Test@1234")
    login = await client.post(
        "/auth/login", json={"email": "refresh@test.com", "password": "Test@1234"}
    )
    old_refresh = login.json()["refresh_token"]

    resp = await client.post("/auth/refresh", json={"refresh_token": old_refresh})
    assert resp.status_code == 200
    new_data = resp.json()
    assert "access_token" in new_data
    assert new_data["refresh_token"] != old_refresh  # rotated

    # Old refresh token must now be invalid
    resp2 = await client.post("/auth/refresh", json={"refresh_token": old_refresh})
    assert resp2.status_code == 401


# ── Logout ─────────────────────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_logout_revokes_refresh_token(client: AsyncClient, make_user):
    await make_user(email="logout@test.com", password="Test@1234")
    login = await client.post(
        "/auth/login", json={"email": "logout@test.com", "password": "Test@1234"}
    )
    refresh = login.json()["refresh_token"]

    logout_resp = await client.post("/auth/logout", json={"refresh_token": refresh})
    assert logout_resp.status_code == 204

    # Revoked token must be rejected
    resp = await client.post("/auth/refresh", json={"refresh_token": refresh})
    assert resp.status_code == 401


# ── Forgot / Reset password ────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_forgot_password_always_204(client: AsyncClient):
    """Must return 204 regardless of whether the email exists (no user enumeration)."""
    resp = await client.post(
        "/auth/forgot-password", json={"email": "ghost@test.com"}
    )
    assert resp.status_code == 204


@pytest.mark.asyncio
async def test_reset_password_invalid_token(client: AsyncClient):
    resp = await client.post(
        "/auth/reset-password",
        json={"token": "a" * 43, "new_password": "NewPass@1234"},
    )
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_change_password(client: AsyncClient, make_user, auth_headers):
    await make_user(email="chpwd@test.com", password="OldPass@1234")
    headers = await auth_headers("chpwd@test.com", "OldPass@1234")
    resp = await client.post(
        "/auth/change-password",
        json={"current_password": "OldPass@1234", "new_password": "NewPass@5678"},
        headers=headers,
    )
    assert resp.status_code == 204

    # Old credentials must now fail
    login = await client.post(
        "/auth/login", json={"email": "chpwd@test.com", "password": "OldPass@1234"}
    )
    assert login.status_code == 401

    # New credentials must work
    login2 = await client.post(
        "/auth/login", json={"email": "chpwd@test.com", "password": "NewPass@5678"}
    )
    assert login2.status_code == 200


@pytest.mark.asyncio
async def test_change_password_wrong_current(client: AsyncClient, make_user, auth_headers):
    await make_user(email="chpwd2@test.com", password="OldPass@1234")
    headers = await auth_headers("chpwd2@test.com", "OldPass@1234")
    resp = await client.post(
        "/auth/change-password",
        json={"current_password": "WrongCurrent!", "new_password": "NewPass@5678"},
        headers=headers,
    )
    assert resp.status_code == 400
