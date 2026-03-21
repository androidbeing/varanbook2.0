"""
main.py – FastAPI application factory and startup/shutdown lifecycle.

Patterns used:
  - Lifespan context manager (replaces deprecated on_event handlers)
  - CORS middleware configured from settings
  - TenantMiddleware for multi-tenant header/subdomain resolution
  - Structured JSON logging with structlog
  - Global exception handler for clean error responses
"""

import asyncio
import time
from contextlib import asynccontextmanager
from typing import AsyncIterator

import structlog
import uvicorn
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.config import get_settings
from app.database import engine, Base
from app.middleware.audit import AuditMiddleware
from app.middleware.rate_limit import limiter
from app.middleware.tenant import TenantMiddleware
from app.routers import files, notifications, profiles, tenant
from app.routers.users import auth_router, users_router
from app.routers.shortlist import router as shortlist_router
from app.routers.partner_preference import router as partner_pref_router
from app.routers.castes import router as castes_router
from app.routers.membership_plans import admin_router as plan_admin_router
from app.routers.membership_plans import router as membership_router

# ── Configure structured logging ───────────────────────────────────────────────
structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,          # request-scoped context
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer(),              # produces JSON log lines
    ],
    wrapper_class=structlog.make_filtering_bound_logger(20),  # INFO
)
log = structlog.get_logger(__name__)
settings = get_settings()


# ── Lifespan ───────────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """
    Startup: log banner, verify DB connectivity, start background tasks.
    Shutdown: cancel background tasks, dispose connection pool.
    """
    log.info(
        "startup",
        app=settings.APP_NAME,
        env=settings.APP_ENV,
        debug=settings.DEBUG,
    )
    # Verify DB is reachable (fail fast)
    async with engine.begin() as conn:
        await conn.execute(text("SELECT 1"))
    log.info("db_connected")

    # ── Background task: expire subscriptions hourly ───────────────────────────
    async def _expiry_loop() -> None:
        """
        Every hour:
          1. Flip status='expired' for overdue active subscriptions.
          2. Send an expiry email to each affected member.
        """
        while True:
            await asyncio.sleep(3600)
            try:
                async with engine.begin() as conn:
                    # RETURNING gives us the user_id + plan for email dispatch
                    rows = await conn.execute(
                        text(
                            """
                            UPDATE member_subscriptions ms
                            SET    status = 'expired'
                            FROM   membership_plan_templates pt,
                                   users u
                            WHERE  ms.plan_template_id = pt.id
                              AND  ms.user_id          = u.id
                              AND  ms.status           = 'active'
                              AND  ms.expires_at       < NOW()
                            RETURNING u.email, u.full_name, pt.name AS plan_name
                            """
                        )
                    )
                expired = rows.fetchall()
                if expired:
                    log.info("subscriptions_expired", count=len(expired))
                    from app.services.email import EmailService
                    for row in expired:
                        try:
                            await EmailService.send_subscription_expired(
                                to_email=row.email,
                                full_name=row.full_name,
                                plan_name=row.plan_name,
                            )
                        except Exception as mail_exc:
                            log.warning(
                                "expiry_email_failed",
                                email=row.email,
                                error=str(mail_exc),
                            )
            except Exception as exc:
                log.warning("subscription_expiry_failed", error=str(exc))

    # ── Background task: 3-day expiry warning (daily) ─────────────────────────
    async def _warning_loop() -> None:
        """
        Every 24 hours: find active subscriptions expiring within 3 days
        that haven't been warned yet, send a warning email, and flip the flag.
        """
        while True:
            await asyncio.sleep(86400)
            try:
                async with engine.begin() as conn:
                    rows = await conn.execute(
                        text(
                            """
                            UPDATE member_subscriptions ms
                            SET    expiry_warning_sent = TRUE
                            FROM   membership_plan_templates pt,
                                   users u
                            WHERE  ms.plan_template_id    = pt.id
                              AND  ms.user_id             = u.id
                              AND  ms.status              = 'active'
                              AND  ms.expiry_warning_sent = FALSE
                              AND  ms.expires_at          BETWEEN NOW() AND NOW() + INTERVAL '3 days'
                            RETURNING u.email, u.full_name, pt.name AS plan_name,
                                      ms.expires_at
                            """
                        )
                    )
                warned = rows.fetchall()
                if warned:
                    log.info("expiry_warnings_sent", count=len(warned))
                    from app.services.email import EmailService
                    for row in warned:
                        try:
                            expires_on = row.expires_at.strftime("%d %b %Y")
                            await EmailService.send_subscription_expiry_warning(
                                to_email=row.email,
                                full_name=row.full_name,
                                plan_name=row.plan_name,
                                expires_on=expires_on,
                            )
                        except Exception as mail_exc:
                            log.warning(
                                "warning_email_failed",
                                email=row.email,
                                error=str(mail_exc),
                            )
            except Exception as exc:
                log.warning("subscription_warning_failed", error=str(exc))

    expiry_task = asyncio.create_task(_expiry_loop())
    warning_task = asyncio.create_task(_warning_loop())

    yield  # ── application runs here ──────────────────────────────────────────

    expiry_task.cancel()
    warning_task.cancel()
    try:
        await asyncio.gather(expiry_task, warning_task, return_exceptions=True)
    except asyncio.CancelledError:
        pass
    await engine.dispose()
    log.info("shutdown", app=settings.APP_NAME)


# ── Application factory ────────────────────────────────────────────────────────
def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        version="1.0.0",
        description=(
            "Multi-tenant SaaS backend for matrimonial information centres. "
            "Provides tenant onboarding, member biodata management, "
            "file uploads (S3), and push notifications."
        ),
        docs_url="/docs",
        redoc_url="/redoc",
        redirect_slashes=False,
        lifespan=lifespan,
    )
    # ── Rate limiter ────────────────────────────────────────────────
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    app.add_middleware(SlowAPIMiddleware)
    # ── CORS ──────────────────────────────────────────────────────────────────
    # Regex covers: localhost, 127.0.0.1, and any private-network IP (LAN access)
    _LOCAL_ORIGIN_REGEX = (
        r"^https?://(localhost|127\.0\.0\.1"
        r"|192\.168\.\d{1,3}\.\d{1,3}"
        r"|10\.\d{1,3}\.\d{1,3}\.\d{1,3}"
        r"|172\.(1[6-9]|2\d|3[01])\.\d{1,3}\.\d{1,3}"
        r")(:\d+)?$"
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_origin_regex=_LOCAL_ORIGIN_REGEX,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID"],
    )

    # ── Tenant resolution (must come AFTER CORS) ───────────────────────────────
    app.add_middleware(TenantMiddleware)
    # ── Audit logging ────────────────────────────────────────────────────
    app.add_middleware(AuditMiddleware)
    # ── Request ID + timing middleware ─────────────────────────────────────────
    @app.middleware("http")
    async def request_context_middleware(request: Request, call_next):
        import uuid as _uuid
        request_id = str(_uuid.uuid4())
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(
            request_id=request_id,
            path=request.url.path,
            method=request.method,
        )
        start = time.perf_counter()
        response = await call_next(request)
        elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
        response.headers["X-Request-ID"] = request_id
        log.info("request_complete", status=response.status_code, elapsed_ms=elapsed_ms)
        return response

    # ── Global exception handler ───────────────────────────────────────────────
    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        import re as _re
        import traceback as _tb
        log.exception("unhandled_error", error=str(exc), traceback=_tb.format_exc())
        origin = request.headers.get("origin", "")
        cors_headers = {}
        if origin in settings.ALLOWED_ORIGINS or (
            origin and _re.match(_LOCAL_ORIGIN_REGEX, origin)
        ):
            cors_headers["Access-Control-Allow-Origin"] = origin
            cors_headers["Access-Control-Allow-Credentials"] = "true"
        # In DEBUG mode expose the real error so it's easier to diagnose
        detail = (
            f"{type(exc).__name__}: {exc}" if settings.DEBUG
            else "An unexpected error occurred. Please try again later."
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": detail},
            headers=cors_headers,
        )

    # ── Routers ───────────────────────────────────────────────────────────────
    app.include_router(auth_router)
    app.include_router(users_router)
    app.include_router(tenant.router)
    app.include_router(profiles.router)
    app.include_router(files.router)
    app.include_router(notifications.router)
    app.include_router(shortlist_router)
    app.include_router(partner_pref_router)
    app.include_router(plan_admin_router)
    app.include_router(membership_router)
    app.include_router(castes_router)
    # ── Health check ──────────────────────────────────────────────────────────
    @app.get("/health", tags=["Health"], summary="Liveness probe")
    async def health() -> dict:
        return {"status": "ok", "app": settings.APP_NAME}

    return app


# ── Module-level app instance (used by Gunicorn/Uvicorn) ──────────────────────
app = create_app()


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_config=None,   # let structlog handle logging
    )
