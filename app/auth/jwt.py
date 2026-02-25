"""
auth/jwt.py – JWT creation and verification utilities.

Two token types:
  - access  : short-lived (default 60 min), used on every API call
  - refresh : long-lived (default 7 days), used only at /auth/refresh

Token payload structure:
  {
    "sub" : "<user_id>",          # subject
    "tid" : "<tenant_id>",        # tenant identifier (null for super_admin)
    "rol" : "<role>",             # UserRole value
    "typ" : "access" | "refresh",
    "iat" : <issued-at epoch>,
    "exp" : <expiry epoch>
  }
"""

from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID

from jose import JWTError, jwt
from pydantic import BaseModel

from app.config import get_settings

settings = get_settings()


class TokenPayload(BaseModel):
    sub: str          # user_id as string
    tid: str | None   # tenant_id; None for SUPER_ADMIN
    rol: str          # UserRole
    typ: str          # "access" or "refresh"
    exp: int
    iat: int


def _utcnow() -> datetime:
    return datetime.now(tz=timezone.utc)


def create_access_token(
    user_id: UUID,
    tenant_id: UUID | None,
    role: str,
) -> str:
    """Mint a short-lived JWT access token."""
    now = _utcnow()
    payload: dict[str, Any] = {
        "sub": str(user_id),
        "tid": str(tenant_id) if tenant_id else None,
        "rol": role,
        "typ": "access",
        "iat": int(now.timestamp()),
        "exp": int(
            (now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)).timestamp()
        ),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(
    user_id: UUID,
    tenant_id: UUID | None,
    role: str,
) -> str:
    """Mint a long-lived JWT refresh token."""
    now = _utcnow()
    payload: dict[str, Any] = {
        "sub": str(user_id),
        "tid": str(tenant_id) if tenant_id else None,
        "rol": role,
        "typ": "refresh",
        "iat": int(now.timestamp()),
        "exp": int(
            (now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)).timestamp()
        ),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> TokenPayload:
    """
    Decode and validate a JWT.

    Raises:
        jose.JWTError – if signature is invalid, token expired, or malformed.
    """
    raw = jwt.decode(
        token,
        settings.SECRET_KEY,
        algorithms=[settings.JWT_ALGORITHM],
    )
    return TokenPayload(**raw)
