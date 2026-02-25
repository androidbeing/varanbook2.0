"""
database.py – Async SQLAlchemy engine, session factory, and base class.

Key design decisions:
 1. engine is created once at import time using settings.
 2. AsyncSession is yielded per-request via a FastAPI dependency.
 3. Row-Level Security (RLS) is activated for every session by setting the
    `app.current_tenant_id` Postgres config variable, which RLS policies use.
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

import structlog
from sqlalchemy import event, text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase, MappedColumn, mapped_column
from sqlalchemy.pool import NullPool

from app.config import get_settings

log = structlog.get_logger(__name__)
settings = get_settings()

# ── Engine ─────────────────────────────────────────────────────────────────────
# NullPool is used in test environments to prevent connection reuse across tests.
engine = create_async_engine(
    str(settings.DATABASE_URL),
    pool_size=settings.DATABASE_POOL_SIZE,
    max_overflow=settings.DATABASE_MAX_OVERFLOW,
    echo=settings.DEBUG,           # logs SQL when DEBUG=True
    future=True,
)

# ── Session factory ────────────────────────────────────────────────────────────
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,        # don't invalidate objects after commit
    autoflush=False,
)


# ── Declarative base ───────────────────────────────────────────────────────────
class Base(DeclarativeBase):
    """All ORM models inherit from this base."""
    pass


# ── Per-request session dependency ────────────────────────────────────────────
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency that opens an async DB session per request,
    commits on success, rolls back on any exception, and always closes.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# ── Tenant-aware session ───────────────────────────────────────────────────────
async def get_tenant_db(
    tenant_id: str,
) -> AsyncGenerator[AsyncSession, None]:
    """
    Opens a DB session and sets the RLS context variable so that
    Postgres RLS policies restrict rows to the current tenant.

    Usage (inside a router dependency):
        async with get_tenant_db(tenant_id) as db: ...
    """
    async with AsyncSessionLocal() as session:
        try:
            # Postgres SET LOCAL only lasts for the current transaction.
            await session.execute(
                text("SET LOCAL app.current_tenant_id = :tid"),
                {"tid": tenant_id},
            )
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
