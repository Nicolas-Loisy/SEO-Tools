"""Crawler factory implementing Factory pattern."""

from typing import Dict, Any
from app.services.crawler.base import BaseCrawler
from app.services.crawler.fast_crawler import FastCrawler


class CrawlerFactory:
    """
    Factory for creating crawlers based on mode.

    Implements Factory Pattern for crawler instantiation.
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
            # TODO: Implement PlaywrightCrawler
            # from app.services.crawler.js_crawler import JSCrawler
            # return JSCrawler(config)
            raise NotImplementedError("JS crawler not yet implemented. Use mode='fast' for now.")

        else:
            raise ValueError(f"Unknown crawler mode: {mode}. Use 'fast' or 'js'.")
