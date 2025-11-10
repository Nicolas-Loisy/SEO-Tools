"""Crawl job schemas for API validation."""

from datetime import datetime
from typing import Optional, Dict, Any, List, Literal
from pydantic import BaseModel, Field


class ViewportConfig(BaseModel):
    """Viewport configuration for Playwright crawler."""

    width: int = Field(1920, ge=320, le=3840, description="Viewport width in pixels")
    height: int = Field(1080, ge=240, le=2160, description="Viewport height in pixels")


class PlaywrightConfig(BaseModel):
    """Configuration specific to Playwright (JS mode) crawler."""

    headless: bool = Field(True, description="Run browser in headless mode")
    capture_screenshot: bool = Field(False, description="Capture page screenshots")
    screenshot_type: Literal["viewport", "fullpage"] = Field(
        "viewport", description="Screenshot type: viewport or fullpage"
    )
    viewport: ViewportConfig = Field(
        default_factory=ViewportConfig, description="Browser viewport size"
    )
    wait_until: Literal["load", "domcontentloaded", "networkidle"] = Field(
        "networkidle", description="Wait until condition before considering page loaded"
    )
    timeout: int = Field(30000, ge=5000, le=120000, description="Page load timeout in milliseconds")
    block_resources: List[str] = Field(
        default_factory=lambda: ["image", "font", "media"],
        description="Resource types to block for performance",
    )


class CrawlConfig(BaseModel):
    """General crawl configuration."""

    depth: Optional[int] = Field(None, ge=0, le=10, description="Maximum crawl depth (overrides project setting)")
    max_pages: Optional[int] = Field(None, ge=1, le=100000, description="Maximum pages to crawl (overrides project setting)")

    # Playwright-specific config (only used when mode='js')
    headless: Optional[bool] = Field(None, description="[JS mode] Run browser in headless mode")
    capture_screenshot: Optional[bool] = Field(None, description="[JS mode] Capture page screenshots")
    screenshot_type: Optional[Literal["viewport", "fullpage"]] = Field(None, description="[JS mode] Screenshot type")
    viewport: Optional[Dict[str, int]] = Field(None, description="[JS mode] Browser viewport size")
    wait_until: Optional[Literal["load", "domcontentloaded", "networkidle"]] = Field(None, description="[JS mode] Page load wait condition")
    timeout: Optional[int] = Field(None, description="[JS mode] Page load timeout in milliseconds")
    block_resources: Optional[List[str]] = Field(None, description="[JS mode] Resource types to block")


class CrawlJobCreate(BaseModel):
    """Schema for creating a crawl job."""

    project_id: int = Field(..., gt=0, description="Project ID to crawl")
    mode: Literal["fast", "js"] = Field("fast", description="Crawl mode: fast (aiohttp) or js (Playwright)")
    config: Optional[CrawlConfig] = Field(
        None,
        description="Crawl configuration options",
    )

    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "project_id": 1,
                    "mode": "fast",
                    "config": {
                        "depth": 2,
                        "max_pages": 50,
                    },
                },
                {
                    "project_id": 1,
                    "mode": "js",
                    "config": {
                        "depth": 3,
                        "max_pages": 100,
                        "headless": True,
                        "capture_screenshot": True,
                        "screenshot_type": "viewport",
                        "viewport": {"width": 1920, "height": 1080},
                        "wait_until": "networkidle",
                        "timeout": 30000,
                        "block_resources": ["image", "font"],
                    },
                },
            ]
        }


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
