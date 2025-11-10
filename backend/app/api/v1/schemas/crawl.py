"""Crawl job schemas for API validation."""

from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class CrawlJobCreate(BaseModel):
    """Schema for creating a crawl job."""

    project_id: int = Field(..., gt=0, description="Project ID to crawl")
    mode: str = Field("fast", pattern="^(fast|js)$", description="Crawl mode: fast or js")
    config: Optional[Dict[str, Any]] = Field(
        None,
        description="Additional crawl configuration (depth, max_pages, selectors, etc.)",
    )


class CrawlJobResponse(BaseModel):
    """Schema for crawl job responses."""

    id: int
    project_id: int
    status: str
    mode: str
    config: Dict[str, Any]

    started_at: Optional[datetime]
    finished_at: Optional[datetime]
    duration_seconds: float

    pages_discovered: int
    pages_crawled: int
    pages_failed: int
    links_found: int

    error_message: Optional[str]
    celery_task_id: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True
