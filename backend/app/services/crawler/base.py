"""Base crawler interface."""

from abc import ABC, abstractmethod
from typing import List, Dict, Any
from dataclasses import dataclass
from datetime import datetime


@dataclass
class CrawledPage:
    """Data class for crawled page information."""

    url: str
    url_hash: str
    status_code: int
    content_type: str | None
    title: str | None
    meta_description: str | None
    meta_keywords: str | None
    h1: str | None
    text_content: str
    rendered_html: str | None
    content_hash: str
    word_count: int
    lang: str | None
    canonical_url: str | None
    hreflang: Dict[str, str] | None
    depth: int
    outgoing_links: List[Dict[str, str]]  # Changed from List[str] to include anchor text: [{"url": "...", "anchor_text": "..."}]


@dataclass
class CrawlResult:
    """Result of a crawl operation."""

    pages: List[CrawledPage]
    total_discovered: int
    total_crawled: int
    total_failed: int
    errors: List[Dict[str, Any]]
    started_at: datetime
    finished_at: datetime


class BaseCrawler(ABC):
    """
    Base crawler interface.

    All crawlers must implement this interface for consistency.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize crawler with configuration.

        Args:
            config: Crawler configuration dictionary
        """
        self.config = config
        self.start_url = config.get("start_url")
        self.max_depth = config.get("max_depth", 3)
        self.max_pages = config.get("max_pages", 1000)
        self.delay = config.get("delay", 1.0)
        self.respect_robots = config.get("respect_robots", True)
        self.user_agent = config.get("user_agent", "SEO-SaaS-Bot/1.0")

    @abstractmethod
    async def crawl(self) -> CrawlResult:
        """
        Execute the crawl.

        Returns:
            CrawlResult with all crawled pages

        Raises:
            CrawlerException: If crawl fails
        """
        pass

    @abstractmethod
    async def stop(self) -> None:
        """Stop the crawler gracefully."""
        pass

    def _should_crawl_url(self, url: str) -> bool:
        """
        Check if URL should be crawled.

        Args:
            url: URL to check

        Returns:
            True if URL should be crawled
        """
        # Basic filtering logic
        if not url:
            return False

        # Skip common non-HTML resources
        skip_extensions = ('.pdf', '.jpg', '.jpeg', '.png', '.gif', '.css', '.js', '.xml', '.zip')
        if any(url.lower().endswith(ext) for ext in skip_extensions):
            return False

        return True


class CrawlerException(Exception):
    """Base exception for crawler errors."""

    pass
