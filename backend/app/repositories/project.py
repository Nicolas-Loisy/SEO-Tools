"""Project repository."""

from typing import Optional, List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.project import Project
from app.repositories.base import BaseRepository


class ProjectRepository(BaseRepository[Project]):
    """Repository for Project model."""

    def __init__(self, db: AsyncSession):
        """Initialize with Project model."""
        super().__init__(Project, db)

    async def get_by_domain(self, domain: str) -> Optional[Project]:
        """
        Get project by domain.

        Args:
            domain: Domain URL

        Returns:
            Project or None
        """
        result = await self.db.execute(select(Project).where(Project.domain == domain))
        return result.scalar_one_or_none()

    async def get_by_tenant(
        self, tenant_id: int, skip: int = 0, limit: int = 100
    ) -> List[Project]:
        """
        Get all projects for a tenant.

        Args:
            tenant_id: Tenant ID
            skip: Pagination offset
            limit: Pagination limit

        Returns:
            List of projects
        """
        result = await self.db.execute(
            select(Project)
            .where(Project.tenant_id == tenant_id)
            .offset(skip)
            .limit(limit)
            .order_by(Project.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_active_projects(
        self, tenant_id: int, skip: int = 0, limit: int = 100
    ) -> List[Project]:
        """
        Get active projects for a tenant.

        Args:
            tenant_id: Tenant ID
            skip: Pagination offset
            limit: Pagination limit

        Returns:
            List of active projects
        """
        result = await self.db.execute(
            select(Project)
            .where(Project.tenant_id == tenant_id, Project.is_active == True)
            .offset(skip)
            .limit(limit)
            .order_by(Project.created_at.desc())
        )
        return list(result.scalars().all())

    async def count_by_tenant(self, tenant_id: int) -> int:
        """
        Count projects for a tenant.

        Args:
            tenant_id: Tenant ID

        Returns:
            Project count
        """
        from sqlalchemy import func

        result = await self.db.execute(
            select(func.count())
            .select_from(Project)
            .where(Project.tenant_id == tenant_id)
        )
        return result.scalar()
