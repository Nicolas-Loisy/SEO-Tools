"""Project schemas for API validation."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, HttpUrl


class ProjectBase(BaseModel):
    """Base project schema with common fields."""

    name: str = Field(..., min_length=1, max_length=255, description="Project name")
    domain: HttpUrl = Field(..., description="Website domain")
    description: Optional[str] = Field(None, description="Project description")

    # URLs
    sitemap_url: Optional[HttpUrl] = Field(None, description="Sitemap URL")
    robots_txt_url: Optional[HttpUrl] = Field(None, description="Robots.txt URL")

    # Crawl settings
    js_enabled: bool = Field(False, description="Enable JavaScript rendering")
    max_depth: int = Field(3, ge=1, le=10, description="Maximum crawl depth")
    max_pages: int = Field(1000, ge=1, le=100000, description="Maximum pages to crawl")
    crawl_delay: float = Field(1.0, ge=0.1, le=10.0, description="Delay between requests (seconds)")
    respect_robots: bool = Field(True, description="Respect robots.txt")

    # JS-specific settings
    wait_for_selector: Optional[str] = Field(None, description="CSS selector to wait for")
    wait_for_timeout: int = Field(3000, ge=100, le=60000, description="Timeout in milliseconds")
    wait_for_network_idle: bool = Field(True, description="Wait for network idle")


class ProjectCreate(ProjectBase):
    """Schema for creating a new project."""

    pass


class ProjectUpdate(BaseModel):
    """Schema for updating a project (all fields optional)."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    domain: Optional[HttpUrl] = None
    description: Optional[str] = None
    sitemap_url: Optional[HttpUrl] = None
    robots_txt_url: Optional[HttpUrl] = None
    js_enabled: Optional[bool] = None
    max_depth: Optional[int] = Field(None, ge=1, le=10)
    max_pages: Optional[int] = Field(None, ge=1, le=100000)
    crawl_delay: Optional[float] = Field(None, ge=0.1, le=10.0)
    respect_robots: Optional[bool] = None
    wait_for_selector: Optional[str] = None
    wait_for_timeout: Optional[int] = Field(None, ge=100, le=60000)
    wait_for_network_idle: Optional[bool] = None
    is_active: Optional[bool] = None


class ProjectResponse(ProjectBase):
    """Schema for project responses."""

    id: int
    tenant_id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    last_crawl_at: Optional[datetime]

    class Config:
        from_attributes = True
