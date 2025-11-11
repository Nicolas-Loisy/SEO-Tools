"""Tests for rate limiting service."""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

from app.services.rate_limit import RateLimitService, RateLimitException
from app.models.tenant import Tenant


@pytest.mark.asyncio
async def test_check_and_increment_within_limit():
    """Test rate limit check when within quota."""
    # Arrange
    redis = AsyncMock()
    redis.incr = AsyncMock(return_value=1)
    redis.expire = AsyncMock(return_value=True)

    db = AsyncMock()
    
    tenant = Tenant(
        id=1,
        name="Test Tenant",
        slug="test",
        plan="pro",
        max_api_calls_per_month=10000,
        is_active=True,
    )

    service = RateLimitService(redis=redis, db=db)
    
    # Mock usage retrieval
    from app.models.usage import APIUsage
    mock_usage = APIUsage(
        id=1,
        tenant_id=1,
        year=2024,
        month=2,
        total_api_calls=100,
    )
    
    service._get_or_create_usage = AsyncMock(return_value=mock_usage)

    # Act
    is_allowed, info = await service.check_and_increment(
        tenant=tenant,
        endpoint="/test",
        method="GET",
        ip_address="127.0.0.1",
    )

    # Assert
    assert is_allowed is True
    assert info["limit"] == 10000
    assert info["remaining"] == 9899  # 10000 - 101 (100 + 1)
    assert "reset" in info


@pytest.mark.asyncio
async def test_check_and_increment_exceeds_limit():
    """Test rate limit check when quota exceeded."""
    # Arrange
    redis = AsyncMock()
    db = AsyncMock()
    
    tenant = Tenant(
        id=1,
        name="Test Tenant",
        slug="test",
        plan="free",
        max_api_calls_per_month=1000,
        is_active=True,
    )

    service = RateLimitService(redis=redis, db=db)
    
    # Mock usage at limit
    from app.models.usage import APIUsage
    mock_usage = APIUsage(
        id=1,
        tenant_id=1,
        year=2024,
        month=2,
        total_api_calls=1000,  # At limit
    )
    
    service._get_or_create_usage = AsyncMock(return_value=mock_usage)
    service._log_rate_limit_violation = AsyncMock()

    # Act & Assert
    with pytest.raises(RateLimitException) as exc_info:
        await service.check_and_increment(
            tenant=tenant,
            endpoint="/test",
            method="GET",
        )
    
    assert "Monthly API quota exceeded" in str(exc_info.value)
    assert exc_info.value.limit == 1000
    assert exc_info.value.current == 1000


@pytest.mark.asyncio
async def test_get_usage_stats():
    """Test retrieving usage statistics."""
    # Arrange
    redis = AsyncMock()
    db = AsyncMock()
    
    service = RateLimitService(redis=redis, db=db)
    
    from app.models.usage import APIUsage
    mock_usage = APIUsage(
        id=1,
        tenant_id=1,
        year=2024,
        month=2,
        total_api_calls=500,
        crawl_jobs=10,
        pages_crawled=1500,
        analysis_requests=25,
    )
    
    service._get_or_create_usage = AsyncMock(return_value=mock_usage)

    # Act
    stats = await service.get_usage_stats(tenant_id=1, year=2024, month=2)

    # Assert
    assert stats["period"] == "2024-02"
    assert stats["total_api_calls"] == 500
    assert stats["crawl_jobs"] == 10
    assert stats["pages_crawled"] == 1500
    assert stats["analysis_requests"] == 25
