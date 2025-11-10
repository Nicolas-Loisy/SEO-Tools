"""Rate limiting service for API quota management."""

from datetime import datetime
from typing import Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from redis.asyncio import Redis

from app.models.tenant import Tenant
from app.models.usage import APIUsage, RateLimitLog
from app.core.config import settings


class RateLimitException(Exception):
    """Raised when rate limit is exceeded."""

    def __init__(
        self,
        message: str,
        limit_type: str,
        limit: int,
        current: int,
        reset_at: Optional[datetime] = None,
    ):
        self.message = message
        self.limit_type = limit_type
        self.limit = limit
        self.current = current
        self.reset_at = reset_at
        super().__init__(self.message)


class RateLimitService:
    """
    Service for managing API rate limits and quotas.

    Uses Redis for fast in-memory counters and PostgreSQL for persistent tracking.
    """

    def __init__(self, redis: Redis, db: AsyncSession):
        """
        Initialize rate limit service.

        Args:
            redis: Redis client for fast counters
            db: Database session for persistent storage
        """
        self.redis = redis
        self.db = db

    async def check_and_increment(
        self,
        tenant: Tenant,
        endpoint: str,
        method: str,
        ip_address: Optional[str] = None,
    ) -> Tuple[bool, dict]:
        """
        Check rate limits and increment counters.

        Args:
            tenant: Tenant making the request
            endpoint: API endpoint being accessed
            method: HTTP method
            ip_address: Client IP address

        Returns:
            Tuple of (is_allowed, rate_limit_info)

        Raises:
            RateLimitException: If rate limit is exceeded
        """
        # Get current period
        now = datetime.utcnow()
        year = now.year
        month = now.month

        # Check monthly quota
        usage = await self._get_or_create_usage(tenant.id, year, month)

        # Check if monthly limit exceeded
        if usage.total_api_calls >= tenant.max_api_calls_per_month:
            # Log violation
            await self._log_rate_limit_violation(
                tenant_id=tenant.id,
                endpoint=endpoint,
                method=method,
                ip_address=ip_address,
                limit_type="monthly",
                limit_value=tenant.max_api_calls_per_month,
                current_usage=usage.total_api_calls,
            )

            # Calculate reset time (first day of next month)
            if month == 12:
                reset_year = year + 1
                reset_month = 1
            else:
                reset_year = year
                reset_month = month + 1
            reset_at = datetime(reset_year, reset_month, 1)

            raise RateLimitException(
                message=f"Monthly API quota exceeded. Limit: {tenant.max_api_calls_per_month}",
                limit_type="monthly",
                limit=tenant.max_api_calls_per_month,
                current=usage.total_api_calls,
                reset_at=reset_at,
            )

        # Increment counters
        usage.total_api_calls += 1
        usage.updated_at = datetime.utcnow()
        await self.db.commit()

        # Also increment Redis counter for fast access
        redis_key = f"api_usage:{tenant.id}:{year}:{month}"
        await self.redis.incr(redis_key)
        # Set expiry to end of next month
        await self.redis.expire(redis_key, 60 * 60 * 24 * 62)  # ~2 months

        # Calculate remaining quota
        remaining = tenant.max_api_calls_per_month - usage.total_api_calls
        reset_month_next = month + 1 if month < 12 else 1
        reset_year_next = year if month < 12 else year + 1
        reset_at = datetime(reset_year_next, reset_month_next, 1)

        rate_limit_info = {
            "limit": tenant.max_api_calls_per_month,
            "remaining": remaining,
            "reset": int(reset_at.timestamp()),
            "current": usage.total_api_calls,
        }

        return True, rate_limit_info

    async def get_usage_stats(self, tenant_id: int, year: int, month: int) -> dict:
        """
        Get usage statistics for a tenant.

        Args:
            tenant_id: Tenant ID
            year: Year
            month: Month (1-12)

        Returns:
            Usage statistics dictionary
        """
        usage = await self._get_or_create_usage(tenant_id, year, month)

        return {
            "period": f"{year}-{month:02d}",
            "total_api_calls": usage.total_api_calls,
            "crawl_jobs": usage.crawl_jobs,
            "pages_crawled": usage.pages_crawled,
            "analysis_requests": usage.analysis_requests,
        }

    async def increment_crawl_job(self, tenant_id: int, pages_crawled: int = 0):
        """
        Increment crawl job counter.

        Args:
            tenant_id: Tenant ID
            pages_crawled: Number of pages crawled
        """
        now = datetime.utcnow()
        usage = await self._get_or_create_usage(tenant_id, now.year, now.month)

        usage.crawl_jobs += 1
        usage.pages_crawled += pages_crawled
        await self.db.commit()

    async def increment_analysis_request(self, tenant_id: int):
        """
        Increment analysis request counter.

        Args:
            tenant_id: Tenant ID
        """
        now = datetime.utcnow()
        usage = await self._get_or_create_usage(tenant_id, now.year, now.month)

        usage.analysis_requests += 1
        await self.db.commit()

    async def _get_or_create_usage(
        self, tenant_id: int, year: int, month: int
    ) -> APIUsage:
        """
        Get or create usage record for a tenant and period.

        Args:
            tenant_id: Tenant ID
            year: Year
            month: Month (1-12)

        Returns:
            APIUsage record
        """
        # Try to get existing record
        result = await self.db.execute(
            select(APIUsage).where(
                and_(
                    APIUsage.tenant_id == tenant_id,
                    APIUsage.year == year,
                    APIUsage.month == month,
                )
            )
        )
        usage = result.scalar_one_or_none()

        if not usage:
            # Create new record
            usage = APIUsage(
                tenant_id=tenant_id,
                year=year,
                month=month,
                total_api_calls=0,
                crawl_jobs=0,
                pages_crawled=0,
                analysis_requests=0,
            )
            self.db.add(usage)
            await self.db.commit()
            await self.db.refresh(usage)

        return usage

    async def _log_rate_limit_violation(
        self,
        tenant_id: int,
        endpoint: str,
        method: str,
        ip_address: Optional[str],
        limit_type: str,
        limit_value: int,
        current_usage: int,
    ):
        """
        Log a rate limit violation.

        Args:
            tenant_id: Tenant ID
            endpoint: API endpoint
            method: HTTP method
            ip_address: Client IP
            limit_type: Type of limit (monthly, daily, hourly)
            limit_value: Limit value
            current_usage: Current usage
        """
        log = RateLimitLog(
            tenant_id=tenant_id,
            endpoint=endpoint,
            method=method,
            ip_address=ip_address,
            limit_type=limit_type,
            limit_value=limit_value,
            current_usage=current_usage,
        )
        self.db.add(log)
        await self.db.commit()

    async def check_tenant_active(self, tenant: Tenant) -> bool:
        """
        Check if tenant account is active.

        Args:
            tenant: Tenant object

        Returns:
            True if active

        Raises:
            RateLimitException: If tenant is not active
        """
        if not tenant.is_active:
            raise RateLimitException(
                message="Tenant account is inactive. Please contact support.",
                limit_type="account_status",
                limit=0,
                current=0,
            )
        return True


async def get_rate_limiter(db: AsyncSession) -> RateLimitService:
    """
    Dependency to get rate limiter service.

    Args:
        db: Database session

    Returns:
        RateLimitService instance
    """
    from app.core.redis import get_redis

    redis = await get_redis()
    return RateLimitService(redis=redis, db=db)
