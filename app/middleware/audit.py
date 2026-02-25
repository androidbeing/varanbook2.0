"""
middleware/audit.py – Request-level audit logging middleware.

Writes one AuditLog row per mutating request (POST, PUT, PATCH, DELETE).
GET requests are not logged here; sensitive reads can call log_action() directly.

The DB session is obtained directly via the engine (not via the FastAPI
dependency graph) so that the audit row is committed even if the main
handler raises an exception.
"""

from __future__ import annotations

import time
import uuid
from typing import Any

import structlog
from sqlalchemy import text
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp

from app.database import AsyncSessionLocal
from app.models.audit_log import AuditLog

logger = structlog.get_logger(__name__)

_MUTATING_METHODS = {"POST", "PUT", "PATCH", "DELETE"}


class AuditMiddleware(BaseHTTPMiddleware):
    """
    After each mutating HTTP request completes, persist an AuditLog row.

    Tenant + user context are harvested from request.state (populated by
    TenantMiddleware and auth dependencies respectively).
    """

    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: Any) -> Response:
        start = time.monotonic()
        response: Response = await call_next(request)
        duration_ms = int((time.monotonic() - start) * 1000)

        if request.method not in _MUTATING_METHODS:
            return response

        # Best-effort – never fail the real response
        try:
            await self._write_audit(request, response.status_code, duration_ms)
        except Exception as exc:  # noqa: BLE001
            logger.warning("audit_write_failed", error=str(exc))

        return response

    async def _write_audit(
        self,
        request: Request,
        status_code: int,
        duration_ms: int,
    ) -> None:
        tenant_id: uuid.UUID | None = None
        user_id: uuid.UUID | None = None

        if hasattr(request.state, "tenant") and request.state.tenant:
            tenant_id = request.state.tenant.id
        if hasattr(request.state, "user") and request.state.user:
            user_id = request.state.user.id

        action = f"{request.method.lower()}:{request.url.path}"
        ip = request.client.host if request.client else None
        ua = request.headers.get("user-agent", "")[:512]

        async with AsyncSessionLocal() as db:
            db.add(
                AuditLog(
                    tenant_id=tenant_id,
                    user_id=user_id,
                    action=action,
                    ip_address=ip,
                    user_agent=ua,
                    status_code=status_code,
                    payload={"duration_ms": duration_ms},
                )
            )
            await db.commit()


async def log_action(
    *,
    db: Any,
    tenant_id: uuid.UUID | None,
    user_id: uuid.UUID | None,
    action: str,
    resource_type: str | None = None,
    resource_id: uuid.UUID | None = None,
    payload: dict | None = None,
    status_code: int | None = None,
) -> None:
    """
    Helper for explicit audit entries from service/router code.

    Example:
        await log_action(db=db, tenant_id=..., user_id=..., action="profile.delete",
                         resource_type="profile", resource_id=profile.id)
    """
    db.add(
        AuditLog(
            tenant_id=tenant_id,
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            payload=payload,
            status_code=status_code,
        )
    )
    await db.flush()
