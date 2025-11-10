"""Crawl job repository."""

from typing import Optional, List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.crawl import CrawlJob
from app.repositories.base import BaseRepository


class CrawlJobRepository(BaseRepository[CrawlJob]):
    """Repository for CrawlJob model."""

    def __init__(self, db: AsyncSession):
        """Initialize with CrawlJob model."""
        super().__init__(CrawlJob, db)

    async def get_by_project(
        self, project_id: int, skip: int = 0, limit: int = 50
    ) -> List[CrawlJob]:
        """
        Get crawl jobs for a project.

        Args:
            project_id: Project ID
            skip: Pagination offset
            limit: Pagination limit

        Returns:
            List of crawl jobs
        """
        result = await self.db.execute(
            select(CrawlJob)
            .where(CrawlJob.project_id == project_id)
            .offset(skip)
            .limit(limit)
            .order_by(CrawlJob.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_running_jobs(self, project_id: Optional[int] = None) -> List[CrawlJob]:
        """
        Get currently running crawl jobs.

        Args:
            project_id: Optional project filter

        Returns:
            List of running jobs
        """
        query = select(CrawlJob).where(CrawlJob.status.in_(["pending", "running"]))

        if project_id:
            query = query.where(CrawlJob.project_id == project_id)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_latest_for_project(self, project_id: int) -> Optional[CrawlJob]:
        """
        Get most recent crawl job for a project.

        Args:
            project_id: Project ID

        Returns:
            Latest crawl job or None
        """
        result = await self.db.execute(
            select(CrawlJob)
            .where(CrawlJob.project_id == project_id)
            .order_by(CrawlJob.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def get_by_celery_task_id(self, task_id: str) -> Optional[CrawlJob]:
        """
        Get crawl job by Celery task ID.

        Args:
            task_id: Celery task ID

        Returns:
            Crawl job or None
        """
        result = await self.db.execute(
            select(CrawlJob).where(CrawlJob.celery_task_id == task_id)
        )
        return result.scalar_one_or_none()
