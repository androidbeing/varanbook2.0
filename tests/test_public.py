import pytest
from httpx import AsyncClient

from app.config import get_settings
from tests.conftest import make_tenant


@pytest.mark.asyncio
async def test_public_tenant_includes_phone_otp_flag_disabled(
    client: AsyncClient,
    db,
    monkeypatch: pytest.MonkeyPatch,
):
    tenant = await make_tenant(db, slug='public-disabled', self_registration_enabled=True)

    monkeypatch.setenv('FIREBASE_OTP_ENABLED', 'false')
    get_settings.cache_clear()
    try:
        response = await client.get(f'/public/tenant/{tenant.slug}')
    finally:
        get_settings.cache_clear()

    assert response.status_code == 200
    body = response.json()
    assert body['self_registration_enabled'] is True
    assert body['phone_otp_enabled'] is False


@pytest.mark.asyncio
async def test_public_tenant_includes_phone_otp_flag_enabled(
    client: AsyncClient,
    db,
    monkeypatch: pytest.MonkeyPatch,
):
    tenant = await make_tenant(db, slug='public-enabled', self_registration_enabled=True)

    monkeypatch.setenv('FIREBASE_OTP_ENABLED', 'true')
    get_settings.cache_clear()
    try:
        response = await client.get(f'/public/tenant/{tenant.slug}')
    finally:
        get_settings.cache_clear()

    assert response.status_code == 200
    body = response.json()
    assert body['phone_otp_enabled'] is True


# ── Self-registration: email-only ──────────────────────────────────────────────
@pytest.mark.asyncio
async def test_self_register_email_only(
    client: AsyncClient,
    db,
    monkeypatch: pytest.MonkeyPatch,
):
    """Register with only an email address (no phone) – should succeed."""
    from app.config import get_settings
    tenant = await make_tenant(db, slug='reg-email-only', self_registration_enabled=True)

    monkeypatch.setenv('FIREBASE_OTP_ENABLED', 'false')
    get_settings.cache_clear()
    try:
        resp = await client.post(
            f'/public/register/{tenant.slug}',
            json={
                'full_name': 'Email Only User',
                'email': 'emailonly@test.example.com',
                'gender': 'male',
                'password': 'Test@1234',
            },
        )
    finally:
        get_settings.cache_clear()

    assert resp.status_code == 201
    data = resp.json()
    assert data['email'] == 'emailonly@test.example.com'
    assert data['phone'] is None


@pytest.mark.asyncio
async def test_self_register_phone_only(
    client: AsyncClient,
    db,
    monkeypatch: pytest.MonkeyPatch,
):
    """Register with only a phone number (no email) – should succeed in dev mode."""
    from app.config import get_settings
    tenant = await make_tenant(db, slug='reg-phone-only', self_registration_enabled=True)

    monkeypatch.setenv('FIREBASE_OTP_ENABLED', 'false')
    get_settings.cache_clear()
    try:
        resp = await client.post(
            f'/public/register/{tenant.slug}',
            json={
                'full_name': 'Phone Only User',
                'phone': '+919100000001',
                'gender': 'female',
                'password': 'Test@1234',
            },
        )
    finally:
        get_settings.cache_clear()

    assert resp.status_code == 201
    data = resp.json()
    assert data['email'] is None
    assert data['phone'] == '+919100000001'


@pytest.mark.asyncio
async def test_self_register_both_email_and_phone(
    client: AsyncClient,
    db,
    monkeypatch: pytest.MonkeyPatch,
):
    """Register with both email and phone – both should be stored."""
    from app.config import get_settings
    tenant = await make_tenant(db, slug='reg-both', self_registration_enabled=True)

    monkeypatch.setenv('FIREBASE_OTP_ENABLED', 'false')
    get_settings.cache_clear()
    try:
        resp = await client.post(
            f'/public/register/{tenant.slug}',
            json={
                'full_name': 'Both User',
                'email': 'both@test.example.com',
                'phone': '+919100000002',
                'gender': 'male',
                'password': 'Test@1234',
            },
        )
    finally:
        get_settings.cache_clear()

    assert resp.status_code == 201
    data = resp.json()
    assert data['email'] == 'both@test.example.com'
    assert data['phone'] == '+919100000002'


@pytest.mark.asyncio
async def test_self_register_no_contact_rejected(
    client: AsyncClient,
    db,
    monkeypatch: pytest.MonkeyPatch,
):
    """Registration with neither email nor phone must be rejected (422)."""
    from app.config import get_settings
    tenant = await make_tenant(db, slug='reg-none', self_registration_enabled=True)

    monkeypatch.setenv('FIREBASE_OTP_ENABLED', 'false')
    get_settings.cache_clear()
    try:
        resp = await client.post(
            f'/public/register/{tenant.slug}',
            json={
                'full_name': 'No Contact User',
                'gender': 'male',
                'password': 'Test@1234',
            },
        )
    finally:
        get_settings.cache_clear()

    assert resp.status_code == 422