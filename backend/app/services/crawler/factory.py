"""Crawler factory implementing Factory pattern."""

from typing import Dict, Any
from app.services.crawler.base import BaseCrawler
from app.services.crawler.fast_crawler import FastCrawler
from app.services.crawler.playwright_crawler import PlaywrightCrawler


class CrawlerFactory:
    """
    Factory for creating crawlers based on mode.

    Implements Factory Pattern for crawler instantiation.

    Available modes:
    - fast: Fast crawler using aiohttp (no JavaScript execution)
    - js: Playwright crawler with JavaScript execution and screenshot support
    """

    @staticmethod
    def create(mode: str, config: Dict[str, Any]) -> BaseCrawler:
        """
        Create a crawler instance based on mode.

        Args:
            mode: Crawler mode ("fast" or "js")
            config: Crawler configuration

        Returns:
            Crawler instance

        Raises:
            ValueError: If mode is unknown
        """
        if mode == "fast":
            return FastCrawler(config)

        elif mode == "js":
            return PlaywrightCrawler(config)

        else:
            raise ValueError(f"Unknown crawler mode: {mode}. Use 'fast' or 'js'.")
