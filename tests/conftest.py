"""
tests/conftest.py – Shared pytest fixtures for the test suite.

Architecture:
  - SQLite in-memory DB (via aiosqlite) for fast, isolated tests.
  - FastAPI TestClient wrapping an async test app.
  - Each test gets a fresh DB transaction that is rolled back after.
  - Factory helpers for creating tenants and users.
"""

import asyncio
import uuid
from typing import AsyncGenerator, Generator

import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
import bcrypt as _bcrypt_lib
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from sqlalchemy import JSON
from sqlalchemy.dialects.postgresql import ARRAY, JSONB

from app.database import Base, get_db
from app.main import create_app
from app.models.tenant import Tenant
from app.models.user import User, UserRole

# ── Test DB – SQLite in-memory ─────────────────────────────────────────────────
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

_test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
_TestSession = async_sessionmaker(
    bind=_test_engine, class_=AsyncSession, expire_on_commit=False
)

def _hash_password(plain: str) -> str:
    return _bcrypt_lib.hashpw(plain.encode(), _bcrypt_lib.gensalt(4)).decode()


def _replace_array_with_json(conn) -> None:
    """
    SQLite does not support PostgreSQL's ARRAY or JSONB types.
    Replace every ARRAY/JSONB column in the metadata with JSON before create_all,
    so the in-memory test DB can create the tables without errors.
    Array/JSONB values will be stored/retrieved as JSON, which is fine for tests.
    """
    for table in Base.metadata.tables.values():
        for column in table.columns:
            if isinstance(column.type, (ARRAY, JSONB)):
                column.type = JSON()
    Base.metadata.create_all(conn)


# ── Create tables once per test session ───────────────────────────────────────
@pytest_asyncio.fixture(scope="session", autouse=True)
async def create_test_tables():
    async with _test_engine.begin() as conn:
        await conn.run_sync(_replace_array_with_json)
    yield
    async with _test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


# ── Per-test DB session (rolled back after each test) ─────────────────────────
@pytest_asyncio.fixture
async def db() -> AsyncGenerator[AsyncSession, None]:
    """
    Yields an async session that is rolled back after every test,
    keeping the in-memory DB pristine.
    """
    async with _TestSession() as session:
        yield session
        await session.rollback()


# ── FastAPI app with overridden DB dependency ──────────────────────────────────
@pytest.fixture
def app(db: AsyncSession) -> FastAPI:
    """Return a FastAPI app instance with the real DB dependency overridden."""
    _app = create_app()

    async def _override_get_db():
        yield db

    _app.dependency_overrides[get_db] = _override_get_db
    return _app


# ── Async HTTP client ──────────────────────────────────────────────────────────
@pytest_asyncio.fixture
async def client(app: FastAPI) -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac


# ── Factory helpers ────────────────────────────────────────────────────────────
async def make_tenant(db: AsyncSession, **kwargs) -> Tenant:
    """Create and persist a Tenant with sensible defaults."""
    defaults = {
        "id": uuid.uuid4(),
        "name": "Test Matrimonial Centre",
        "slug": f"test-{uuid.uuid4().hex[:6]}",
        "contact_person": "Test Admin",
        "contact_email": "admin@test.example.com",
        "contact_number": "+911234567890",
        "plan": "starter",
    }
    defaults.update(kwargs)
    tenant = Tenant(**defaults)
    db.add(tenant)
    await db.flush()
    await db.refresh(tenant)
    return tenant


async def make_user(
    db: AsyncSession,
    tenant: Tenant | None,
    role: UserRole = UserRole.MEMBER,
    **kwargs,
) -> User:
    """Create and persist a User with sensible defaults."""
    defaults = {
        "id": uuid.uuid4(),
        "tenant_id": tenant.id if tenant is not None else None,
        "email": f"user-{uuid.uuid4().hex[:6]}@example.com",
        "hashed_password": _hash_password("Test@1234"),
        "full_name": "Test User",
        "role": role,
    }
    defaults.update(kwargs)
    user = User(**defaults)
    db.add(user)
    await db.flush()
    await db.refresh(user)
    return user


# ── Fixture-style factory wrappers (inject db automatically) ──────────────────
@pytest_asyncio.fixture
async def make_tenant_f(db: AsyncSession):
    """Fixture factory: call make_tenant_f(**kwargs) inside a test."""
    async def _inner(**kwargs) -> Tenant:
        return await make_tenant(db, **kwargs)
    return _inner


@pytest_asyncio.fixture
async def make_user_f(db: AsyncSession):
    """Fixture factory: call make_user_f(tenant, **kwargs) inside a test."""
    async def _inner(tenant: Tenant, **kwargs) -> User:
        return await make_user(db, tenant, **kwargs)
    return _inner


# ── Convenience: make_auth_user that creates its own tenant ─────────────────
@pytest_asyncio.fixture
async def make_auth_user(db: AsyncSession):
    """
    Simplified fixture used in test_auth.py:
      await make_auth_user(email="...", password="...")
    Creates a fresh tenant automatically.
    """
    async def _inner(email: str, password: str, role: UserRole = UserRole.MEMBER) -> User:
        tenant = await make_tenant(db)
        user = User(
            id=uuid.uuid4(),
            tenant_id=tenant.id,
            email=email.lower(),
            hashed_password=_hash_password(password),
            full_name="Test User",
            role=role,
        )
        db.add(user)
        await db.flush()
        await db.refresh(user)
        return user
    return _inner


@pytest_asyncio.fixture
async def auth_headers(client: "AsyncClient"):
    """
    Returns a helper that logs in and returns Bearer headers.
      headers = await auth_headers("user@ex.com", "Pass@1234")
    """
    async def _inner(email: str, password: str) -> dict:
        resp = await client.post("/auth/login", json={"email": email, "password": password})
        resp.raise_for_status()
        token = resp.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}
    return _inner
