"""
main.py – FastAPI application factory and startup/shutdown lifecycle.

Patterns used:
  - Lifespan context manager (replaces deprecated on_event handlers)
  - CORS middleware configured from settings
  - TenantMiddleware for multi-tenant header/subdomain resolution
  - Structured JSON logging with structlog
  - Global exception handler for clean error responses
"""

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
    Startup: log banner, verify DB connectivity.
    Shutdown: dispose connection pool.
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

    yield  # ── application runs here ──────────────────────────────────────────

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
        lifespan=lifespan,
    )
    # ── Rate limiter ────────────────────────────────────────────────
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    app.add_middleware(SlowAPIMiddleware)
    # ── CORS ──────────────────────────────────────────────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
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
        log.exception("unhandled_error", error=str(exc))
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "An unexpected error occurred. Please try again later."},
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
