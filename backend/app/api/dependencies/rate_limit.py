"""Rate limit dependencies for fine-grained control."""

from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.tenant import Tenant
from app.services.rate_limit import RateLimitService, get_rate_limiter


async def check_crawl_quota(
    tenant: Tenant = Depends(lambda: None),  # Will be injected by auth
    rate_limiter: RateLimitService = Depends(get_rate_limiter),
    db: AsyncSession = Depends(get_db),
) -> Tenant:
    """
    Dependency to check crawl job quota before creating new crawl.

    Args:
        tenant: Current tenant
        rate_limiter: Rate limiter service
        db: Database session

    Returns:
        Tenant if quota allows

    Raises:
        HTTPException: If quota exceeded
    """
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )

    # Get current month's usage
    from datetime import datetime

    now = datetime.utcnow()
    usage_stats = await rate_limiter.get_usage_stats(tenant.id, now.year, now.month)

    # Check if within limits
    # Note: This is a simple check, more sophisticated logic can be added
    if usage_stats["crawl_jobs"] >= tenant.max_projects * 10:
        # Arbitrary limit: 10 crawls per project per month
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Monthly crawl job quota exceeded. Limit: {tenant.max_projects * 10}",
            headers={
                "X-RateLimit-Limit": str(tenant.max_projects * 10),
                "X-RateLimit-Remaining": "0",
            },
        )

    return tenant


async def check_analysis_quota(
    tenant: Tenant = Depends(lambda: None),
    rate_limiter: RateLimitService = Depends(get_rate_limiter),
    db: AsyncSession = Depends(get_db),
) -> Tenant:
    """
    Dependency to check analysis quota before running expensive operations.

    Args:
        tenant: Current tenant
        rate_limiter: Rate limiter service
        db: Database session

    Returns:
        Tenant if quota allows

    Raises:
        HTTPException: If quota exceeded
    """
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )

    # Get current month's usage
    from datetime import datetime

    now = datetime.utcnow()
    usage_stats = await rate_limiter.get_usage_stats(tenant.id, now.year, now.month)

    # Define analysis limits based on plan
    analysis_limits = {
        "free": 100,
        "starter": 1000,
        "pro": 10000,
        "enterprise": 100000,
    }

    limit = analysis_limits.get(tenant.plan, 100)

    if usage_stats["analysis_requests"] >= limit:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Monthly analysis quota exceeded for {tenant.plan} plan. Limit: {limit}",
            headers={
                "X-RateLimit-Limit": str(limit),
                "X-RateLimit-Remaining": "0",
            },
        )

    return tenant


def require_plan(min_plan: str):
    """
    Decorator to require minimum plan level.

    Args:
        min_plan: Minimum required plan (free, starter, pro, enterprise)

    Returns:
        Dependency function
    """
    plan_hierarchy = ["free", "starter", "pro", "enterprise"]

    async def _check_plan(tenant: Tenant = Depends(lambda: None)) -> Tenant:
        if not tenant:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required",
            )

        if tenant.plan not in plan_hierarchy:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid plan",
            )

        min_plan_index = plan_hierarchy.index(min_plan)
        tenant_plan_index = plan_hierarchy.index(tenant.plan)

        if tenant_plan_index < min_plan_index:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"This feature requires {min_plan} plan or higher. Current plan: {tenant.plan}",
            )

        return tenant

    return _check_plan
