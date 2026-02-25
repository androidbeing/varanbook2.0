"""
auth/dependencies.py – FastAPI dependencies for authentication & authorisation.

Usage in routers:
    @router.get("/me")
    async def get_me(current_user: Annotated[User, Depends(get_current_user)]):
        ...

    # Require admin or above:
    @router.post("/admins")
    async def create_admin(
        _: Annotated[User, Depends(require_admin)]
    ):
        ...
"""

from typing import Annotated

import structlog
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.jwt import decode_token
from app.database import get_db
from app.models.user import User, UserRole

log = structlog.get_logger(__name__)

# OAuth2 bearer scheme – reads Authorization: Bearer <token>
_bearer = HTTPBearer(auto_error=True)


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(_bearer)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    """
    Validate Bearer JWT and return the authenticated User ORM object.

    Steps:
      1. Decode token (verify signature + expiry).
      2. Confirm token type is 'access' (reject refresh tokens here).
      3. Load user from DB and confirm they are still active.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_token(credentials.credentials)
    except JWTError as exc:
        log.warning("jwt_decode_error", error=str(exc))
        raise credentials_exception

    if payload.typ != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type. Use an access token.",
        )

    # Load user from the DB (ensures account hasn't been deleted/deactivated)
    result = await db.execute(select(User).where(User.id == payload.sub))
    user = result.scalar_one_or_none()

    if user is None or not user.is_active:
        raise credentials_exception

    return user


# ── Role-based shortcuts ───────────────────────────────────────────────────────
def _role_guard(*allowed_roles: UserRole):
    """Factory that returns a dependency ensuring the user has one of the given roles."""

    async def _check(
        current_user: Annotated[User, Depends(get_current_user)],
    ) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires one of: {[r.value for r in allowed_roles]}",
            )
        return current_user

    return _check


require_super_admin = _role_guard(UserRole.SUPER_ADMIN)
require_admin = _role_guard(UserRole.SUPER_ADMIN, UserRole.ADMIN)
require_member = _role_guard(UserRole.SUPER_ADMIN, UserRole.ADMIN, UserRole.MEMBER)
