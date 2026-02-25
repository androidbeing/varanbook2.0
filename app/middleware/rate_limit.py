"""
middleware/rate_limit.py – Per-IP sliding-window rate limiter using slowapi.

Limits:
  - Default global:   200 requests / minute per IP
  - Auth endpoints:   10 requests / minute per IP   (applied per route)
  - Upload endpoints: 30 requests / minute per IP   (applied per route)

Usage in main.py:
  from slowapi import _rate_limit_exceeded_handler
  from slowapi.errors import RateLimitExceeded
  from app.middleware.rate_limit import limiter

  app.state.limiter = limiter
  app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

Usage in a router:
  from app.middleware.rate_limit import limiter

  @router.post("/login")
  @limiter.limit("10/minute")
  async def login(request: Request, ...):
      ...
"""

from slowapi import Limiter
from slowapi.util import get_remote_address

# Uses the real client IP (X-Forwarded-For aware via starlette's Request)
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200/minute"],
    headers_enabled=True,          # adds X-RateLimit-* response headers
    swallow_errors=False,
)

# Convenience decorators reused across routers
RATE_AUTH = "10/minute"
RATE_UPLOAD = "30/minute"
RATE_SEARCH = "60/minute"
