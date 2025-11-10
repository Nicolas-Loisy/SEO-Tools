"""Rate limiting middleware for FastAPI."""

from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Callable

from app.core.database import SessionLocal
from app.services.rate_limit import RateLimitService, RateLimitException
from app.core.redis import get_redis


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Middleware to enforce rate limits on API requests.

    Adds rate limit headers to all responses and blocks requests that exceed quotas.
    """

    # Endpoints to exclude from rate limiting
    EXCLUDED_PATHS = [
        "/health",
        "/docs",
        "/redoc",
        "/openapi.json",
        "/api/v1/auth/me",  # Allow checking auth status
    ]

    def __init__(self, app: ASGIApp):
        """Initialize middleware."""
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request and enforce rate limits.

        Args:
            request: HTTP request
            call_next: Next middleware/handler

        Returns:
            HTTP response with rate limit headers
        """
        # Skip rate limiting for excluded paths
        if any(request.url.path.startswith(path) for path in self.EXCLUDED_PATHS):
            return await call_next(request)

        # Skip for OPTIONS requests (CORS preflight)
        if request.method == "OPTIONS":
            return await call_next(request)

        # Get tenant from request state (set by auth dependency)
        tenant = getattr(request.state, "tenant", None)

        if not tenant:
            # No tenant = no authentication = should be handled by auth middleware
            return await call_next(request)

        # Get database session
        db: AsyncSession = SessionLocal()

        try:
            # Get Redis and create rate limiter
            redis = await get_redis()
            rate_limiter = RateLimitService(redis=redis, db=db)

            # Check if tenant is active
            await rate_limiter.check_tenant_active(tenant)

            # Get client IP
            client_ip = request.client.host if request.client else None

            # Check and increment rate limit
            is_allowed, rate_limit_info = await rate_limiter.check_and_increment(
                tenant=tenant,
                endpoint=request.url.path,
                method=request.method,
                ip_address=client_ip,
            )

            # Process request
            response = await call_next(request)

            # Add rate limit headers to response
            response.headers["X-RateLimit-Limit"] = str(rate_limit_info["limit"])
            response.headers["X-RateLimit-Remaining"] = str(
                rate_limit_info["remaining"]
            )
            response.headers["X-RateLimit-Reset"] = str(rate_limit_info["reset"])

            return response

        except RateLimitException as e:
            # Rate limit exceeded
            headers = {
                "X-RateLimit-Limit": str(e.limit),
                "X-RateLimit-Remaining": "0",
            }
            if e.reset_at:
                headers["X-RateLimit-Reset"] = str(int(e.reset_at.timestamp()))

            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "detail": e.message,
                    "limit_type": e.limit_type,
                    "limit": e.limit,
                    "current": e.current,
                    "reset_at": e.reset_at.isoformat() if e.reset_at else None,
                },
                headers=headers,
            )

        except Exception as e:
            # Log error but don't block request
            import traceback

            traceback.print_exc()
            # Continue without rate limiting
            return await call_next(request)

        finally:
            await db.close()
