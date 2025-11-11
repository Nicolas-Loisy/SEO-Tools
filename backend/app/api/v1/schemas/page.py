"""Page schemas for API validation."""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class PageResponse(BaseModel):
    """Schema for page responses."""

    id: int
    project_id: int
    crawl_job_id: int
    url: str
    canonical_url: Optional[str]

    status_code: Optional[int]
    content_type: Optional[str]

    title: Optional[str]
    meta_description: Optional[str]
    meta_keywords: Optional[str]
    h1: Optional[str]

    word_count: int
    depth: int
    seo_score: float

    hreflang: Optional[str]
    lang: Optional[str]

    discovered_at: datetime
    last_crawled_at: Optional[datetime]

    # Computed fields
    internal_links_count: int = Field(default=0, description="Number of internal links")
    external_links_count: int = Field(default=0, description="Number of external links")

    class Config:
        from_attributes = True


class PageListResponse(BaseModel):
    """Schema for paginated page list."""

    items: List[PageResponse]
    total: int
    skip: int
    limit: int

    @property
    def has_next(self) -> bool:
        """Check if there are more pages."""
        return self.skip + self.limit < self.total
