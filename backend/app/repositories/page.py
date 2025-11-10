"""Page repository."""

from typing import Optional, List
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.page import Page, Link
from app.repositories.base import BaseRepository


class PageRepository(BaseRepository[Page]):
    """Repository for Page model."""

    def __init__(self, db: AsyncSession):
        """Initialize with Page model."""
        super().__init__(Page, db)

    async def get_by_url(self, project_id: int, url: str) -> Optional[Page]:
        """
        Get page by URL.

        Args:
            project_id: Project ID
            url: Page URL

        Returns:
            Page or None
        """
        result = await self.db.execute(
            select(Page).where(Page.project_id == project_id, Page.url == url)
        )
        return result.scalar_one_or_none()

    async def get_by_url_hash(self, project_id: int, url_hash: str) -> Optional[Page]:
        """
        Get page by URL hash (faster than URL comparison).

        Args:
            project_id: Project ID
            url_hash: SHA256 hash of URL

        Returns:
            Page or None
        """
        result = await self.db.execute(
            select(Page).where(Page.project_id == project_id, Page.url_hash == url_hash)
        )
        return result.scalar_one_or_none()

    async def get_by_project(
        self,
        project_id: int,
        skip: int = 0,
        limit: int = 100,
        status_code: Optional[int] = None,
        min_depth: Optional[int] = None,
        max_depth: Optional[int] = None,
    ) -> List[Page]:
        """
        Get pages for a project with optional filters.

        Args:
            project_id: Project ID
            skip: Pagination offset
            limit: Pagination limit
            status_code: Filter by HTTP status
            min_depth: Minimum crawl depth
            max_depth: Maximum crawl depth

        Returns:
            List of pages
        """
        query = select(Page).where(Page.project_id == project_id)

        if status_code is not None:
            query = query.where(Page.status_code == status_code)
        if min_depth is not None:
            query = query.where(Page.depth >= min_depth)
        if max_depth is not None:
            query = query.where(Page.depth <= max_depth)

        query = query.offset(skip).limit(limit).order_by(Page.discovered_at.desc())

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def count_by_project(
        self,
        project_id: int,
        status_code: Optional[int] = None,
        min_depth: Optional[int] = None,
        max_depth: Optional[int] = None,
    ) -> int:
        """
        Count pages for a project.

        Args:
            project_id: Project ID
            status_code: Filter by HTTP status
            min_depth: Minimum crawl depth
            max_depth: Maximum crawl depth

        Returns:
            Page count
        """
        query = select(func.count()).select_from(Page).where(Page.project_id == project_id)

        if status_code is not None:
            query = query.where(Page.status_code == status_code)
        if min_depth is not None:
            query = query.where(Page.depth >= min_depth)
        if max_depth is not None:
            query = query.where(Page.depth <= max_depth)

        result = await self.db.execute(query)
        return result.scalar()

    async def find_similar_pages(
        self, page: Page, limit: int = 10, threshold: float = 0.7
    ) -> List[Page]:
        """
        Find semantically similar pages using vector embeddings.

        Args:
            page: Source page
            limit: Maximum number of results
            threshold: Similarity threshold (0-1)

        Returns:
            List of similar pages
        """
        if page.embedding is None:
            return []

        # Use pgvector cosine distance
        query = (
            select(Page)
            .where(
                Page.project_id == page.project_id,
                Page.id != page.id,
                Page.embedding.isnot(None),
            )
            .order_by(Page.embedding.cosine_distance(page.embedding))
            .limit(limit)
        )

        result = await self.db.execute(query)
        return list(result.scalars().all())


class LinkRepository(BaseRepository[Link]):
    """Repository for Link model."""

    def __init__(self, db: AsyncSession):
        """Initialize with Link model."""
        super().__init__(Link, db)

    async def get_by_pages(self, source_id: int, target_id: int) -> Optional[Link]:
        """
        Get link between two pages.

        Args:
            source_id: Source page ID
            target_id: Target page ID

        Returns:
            Link or None
        """
        result = await self.db.execute(
            select(Link).where(
                Link.source_page_id == source_id, Link.target_page_id == target_id
            )
        )
        return result.scalar_one_or_none()

    async def get_outgoing_links(self, page_id: int) -> List[Link]:
        """
        Get all outgoing links from a page.

        Args:
            page_id: Source page ID

        Returns:
            List of links
        """
        result = await self.db.execute(
            select(Link).where(Link.source_page_id == page_id)
        )
        return list(result.scalars().all())

    async def get_incoming_links(self, page_id: int) -> List[Link]:
        """
        Get all incoming links to a page.

        Args:
            page_id: Target page ID

        Returns:
            List of links
        """
        result = await self.db.execute(
            select(Link).where(Link.target_page_id == page_id)
        )
        return list(result.scalars().all())

    async def count_outgoing(self, page_id: int) -> int:
        """
        Count outgoing links from a page.

        Args:
            page_id: Source page ID

        Returns:
            Link count
        """
        result = await self.db.execute(
            select(func.count()).select_from(Link).where(Link.source_page_id == page_id)
        )
        return result.scalar()

    async def count_incoming(self, page_id: int) -> int:
        """
        Count incoming links to a page.

        Args:
            page_id: Target page ID

        Returns:
            Link count
        """
        result = await self.db.execute(
            select(func.count()).select_from(Link).where(Link.target_page_id == page_id)
        )
        return result.scalar()
