"""
middleware/tenant.py – Starlette middleware that resolves the current tenant
from the request and attaches it to request.state.

Resolution strategy (in priority order):
  1. X-Tenant-ID header    (UUID string)
  2. Host subdomain        (e.g. sharma.varanbook.in → slug "sharma")
  3. No tenant             (allowed for /health, /auth/*, super-admin routes)

The resolved tenant record is stored in request.state.tenant so route
handlers can access it without hitting the DB again.
"""

import uuid
from typing import Callable

import structlog
from fastapi import Request, Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.config import get_settings
from app.database import AsyncSessionLocal
from app.models.tenant import Tenant

log = structlog.get_logger(__name__)
settings = get_settings()

# Paths that do NOT require a tenant context
_TENANT_FREE_PREFIXES = (
    "/health",
    "/docs",
    "/openapi.json",
    "/redoc",
    "/auth",           # login / token refresh – tenant resolved from JWT later
    "/admin/tenants",  # super-admin tenant CRUD
)


class TenantMiddleware(BaseHTTPMiddleware):
    """
    For every inbound request:
      - Skip tenant resolution for tenant-free paths.
      - Attempt to resolve tenant from header or subdomain.
      - Attach tenant to request.state.tenant (None if not found).

    Does NOT short-circuit the request on missing tenant; routers that require
    a tenant should call the `get_tenant_from_request` dependency instead.
    """

    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        request.state.tenant = None  # default

        # Skip resolution for public/super-admin paths
        if any(request.url.path.startswith(p) for p in _TENANT_FREE_PREFIXES):
            return await call_next(request)

        tenant = await self._resolve_tenant(request)
        request.state.tenant = tenant

        if tenant:
            log.info("tenant_resolved", slug=tenant.slug, path=request.url.path)
        else:
            log.debug("no_tenant_resolved", path=request.url.path)

        return await call_next(request)

    async def _resolve_tenant(self, request: Request) -> Tenant | None:
        """Try header first, then subdomain slug."""
        # 1. Header: X-Tenant-ID (UUID)
        tenant_id_header = request.headers.get(settings.TENANT_ID_HEADER)
        if tenant_id_header:
            try:
                tid = uuid.UUID(tenant_id_header)
            except ValueError:
                return None
            return await self._fetch_by_id(tid)

        # 2. Subdomain: <slug>.varanbook.in
        host = request.headers.get("host", "")
        parts = host.split(".")
        if len(parts) >= 3:  # slug.domain.tld
            slug = parts[0]
            return await self._fetch_by_slug(slug)

        return None

    async def _fetch_by_id(self, tenant_id: uuid.UUID) -> Tenant | None:
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(Tenant).where(
                    Tenant.id == tenant_id, Tenant.is_active == True  # noqa: E712
                )
            )
            return result.scalar_one_or_none()

    async def _fetch_by_slug(self, slug: str) -> Tenant | None:
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(Tenant).where(
                    Tenant.slug == slug, Tenant.is_active == True  # noqa: E712
                )
            )
            return result.scalar_one_or_none()
