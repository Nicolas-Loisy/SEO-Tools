"""Dependency injection for FastAPI."""

from typing import AsyncGenerator, Tuple
from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import verify_api_key, api_key_header
from app.models.tenant import Tenant
from app.repositories.tenant import TenantRepository


async def get_current_tenant(
    api_key: str = Depends(api_key_header),
    db: AsyncSession = Depends(get_db),
) -> Tenant:
    """
    Get current tenant from API key.

    Args:
        api_key: API key from header
        db: Database session

    Returns:
        Tenant object

    Raises:
        HTTPException: If authentication fails
    """
    tenant_id, _ = await verify_api_key(api_key, db)

    tenant_repo = TenantRepository(db)
    tenant = await tenant_repo.get_by_id(tenant_id)

    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found",
        )

    if not tenant.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tenant account is inactive",
        )

    return tenant


async def get_current_tenant_optional(
    api_key: str = Depends(api_key_header),
    db: AsyncSession = Depends(get_db),
) -> Tenant | None:
    """
    Get current tenant from API key (optional for public endpoints).

    Args:
        api_key: API key from header
        db: Database session

    Returns:
        Tenant object or None if no authentication
    """
    if not api_key:
        return None

    try:
        return await get_current_tenant(api_key, db)
    except HTTPException:
        return None


def require_scopes(*required_scopes: str):
    """
    Dependency to require specific API key scopes.

    Args:
        required_scopes: Required scope strings

    Returns:
        Dependency function
    """

    async def check_scopes(
        api_key: str = Depends(api_key_header),
        db: AsyncSession = Depends(get_db),
    ) -> Tuple[int, int]:
        """Check if API key has required scopes."""
        tenant_id, key_id = await verify_api_key(api_key, db)

        from sqlalchemy import select
        from app.models.api_key import APIKey

        result = await db.execute(select(APIKey).where(APIKey.id == key_id))
        key_obj = result.scalar_one_or_none()

        if not key_obj:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="API key not found",
            )

        # Parse scopes
        key_scopes = set(key_obj.scopes.split(","))

        # Check if all required scopes are present
        if not all(scope in key_scopes for scope in required_scopes):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing required scopes: {', '.join(required_scopes)}",
            )

        return tenant_id, key_id

    return check_scopes
