"""API usage and quota management endpoints."""

from datetime import datetime
from typing import List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.models.tenant import Tenant
from app.core.deps import get_current_tenant
from app.services.rate_limit import get_rate_limiter, RateLimitService


router = APIRouter()


class UsageStatsResponse(BaseModel):
    """Response model for usage statistics."""

    period: str = Field(..., description="Period in YYYY-MM format")
    total_api_calls: int = Field(..., description="Total API calls made")
    crawl_jobs: int = Field(..., description="Number of crawl jobs started")
    pages_crawled: int = Field(..., description="Total pages crawled")
    analysis_requests: int = Field(..., description="Number of analysis requests")


class QuotaResponse(BaseModel):
    """Response model for quota information."""

    plan: str = Field(..., description="Current subscription plan")
    max_projects: int = Field(..., description="Maximum number of projects")
    max_pages_per_crawl: int = Field(..., description="Maximum pages per crawl job")
    max_api_calls_per_month: int = Field(..., description="Maximum API calls per month")
    current_usage: UsageStatsResponse = Field(..., description="Current month's usage")
    remaining: dict = Field(..., description="Remaining quotas")


class UsageHistoryResponse(BaseModel):
    """Response model for usage history."""

    history: List[UsageStatsResponse] = Field(..., description="Monthly usage history")


@router.get("/quota", response_model=QuotaResponse)
async def get_quota(
    tenant: Tenant = Depends(get_current_tenant),
    rate_limiter: RateLimitService = Depends(get_rate_limiter),
):
    """
    Get current quota and usage information.

    Returns quota limits and current usage for the authenticated tenant.
    """
    # Get current month's usage
    now = datetime.utcnow()
    usage_stats = await rate_limiter.get_usage_stats(tenant.id, now.year, now.month)

    # Calculate remaining quotas
    remaining = {
        "api_calls": max(
            0, tenant.max_api_calls_per_month - usage_stats["total_api_calls"]
        ),
        "projects": max(0, tenant.max_projects),  # This would need to count actual projects
        "pages_per_crawl": tenant.max_pages_per_crawl,
    }

    return QuotaResponse(
        plan=tenant.plan,
        max_projects=tenant.max_projects,
        max_pages_per_crawl=tenant.max_pages_per_crawl,
        max_api_calls_per_month=tenant.max_api_calls_per_month,
        current_usage=UsageStatsResponse(**usage_stats),
        remaining=remaining,
    )


@router.get("/stats", response_model=UsageStatsResponse)
async def get_usage_stats(
    year: int = Query(None, description="Year (default: current year)"),
    month: int = Query(None, ge=1, le=12, description="Month 1-12 (default: current month)"),
    tenant: Tenant = Depends(get_current_tenant),
    rate_limiter: RateLimitService = Depends(get_rate_limiter),
):
    """
    Get usage statistics for a specific period.

    Returns detailed usage statistics for the specified month and year.
    If not specified, returns current month's statistics.
    """
    now = datetime.utcnow()
    year = year or now.year
    month = month or now.month

    usage_stats = await rate_limiter.get_usage_stats(tenant.id, year, month)
    return UsageStatsResponse(**usage_stats)


@router.get("/history", response_model=UsageHistoryResponse)
async def get_usage_history(
    months: int = Query(6, ge=1, le=12, description="Number of months to retrieve"),
    tenant: Tenant = Depends(get_current_tenant),
    rate_limiter: RateLimitService = Depends(get_rate_limiter),
):
    """
    Get usage history for the past N months.

    Returns usage statistics for the specified number of past months.
    Useful for charts and trends analysis.
    """
    from datetime import datetime
    from dateutil.relativedelta import relativedelta

    now = datetime.utcnow()
    history = []

    for i in range(months):
        # Calculate month
        target_date = now - relativedelta(months=i)
        year = target_date.year
        month = target_date.month

        # Get stats
        usage_stats = await rate_limiter.get_usage_stats(tenant.id, year, month)
        history.append(UsageStatsResponse(**usage_stats))

    return UsageHistoryResponse(history=history)


@router.get("/limits", response_model=dict)
async def get_rate_limits(tenant: Tenant = Depends(get_current_tenant)):
    """
    Get rate limit information for the current tenant.

    Returns all rate limits and thresholds for the tenant's plan.
    """
    # Define limits per plan
    limits_by_plan = {
        "free": {
            "api_calls_per_month": 10000,
            "max_projects": 1,
            "max_pages_per_crawl": 100,
            "analysis_requests_per_month": 100,
            "crawl_jobs_per_month": 10,
        },
        "starter": {
            "api_calls_per_month": 50000,
            "max_projects": 5,
            "max_pages_per_crawl": 1000,
            "analysis_requests_per_month": 1000,
            "crawl_jobs_per_month": 50,
        },
        "pro": {
            "api_calls_per_month": 200000,
            "max_projects": 50,
            "max_pages_per_crawl": 10000,
            "analysis_requests_per_month": 10000,
            "crawl_jobs_per_month": 500,
        },
        "enterprise": {
            "api_calls_per_month": 1000000,
            "max_projects": 500,
            "max_pages_per_crawl": 100000,
            "analysis_requests_per_month": 100000,
            "crawl_jobs_per_month": 5000,
        },
    }

    plan_limits = limits_by_plan.get(tenant.plan, limits_by_plan["free"])

    # Get current usage for reset time
    now = datetime.utcnow()
    next_month = now.month + 1 if now.month < 12 else 1
    next_year = now.year if now.month < 12 else now.year + 1
    reset_at = datetime(next_year, next_month, 1)

    return {
        "plan": tenant.plan,
        "limits": plan_limits,
        "reset_at": reset_at.isoformat(),
        "reset_timestamp": int(reset_at.timestamp()),
    }
