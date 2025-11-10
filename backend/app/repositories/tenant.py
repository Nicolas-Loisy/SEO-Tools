"""Tenant repository."""

from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.tenant import Tenant
from app.repositories.base import BaseRepository


class TenantRepository(BaseRepository[Tenant]):
    """Repository for Tenant model."""

    def __init__(self, db: AsyncSession):
        """Initialize with Tenant model."""
        super().__init__(Tenant, db)

    async def get_by_slug(self, slug: str) -> Optional[Tenant]:
        """
        Get tenant by slug.

        Args:
            slug: Tenant slug

        Returns:
            Tenant or None
        """
        result = await self.db.execute(select(Tenant).where(Tenant.slug == slug))
        return result.scalar_one_or_none()

    async def get_or_create_default(self) -> Tenant:
        """
        Get or create default tenant for MVP.

        Returns:
            Default tenant
        """
        tenant = await self.get_by_slug("default")

        if not tenant:
            tenant = Tenant(
                name="Default Tenant",
                slug="default",
                plan="free",
                max_projects=10,
                max_pages_per_crawl=5000,
                max_api_calls_per_month=50000,
            )
            tenant = await self.create(tenant)

        return tenant
