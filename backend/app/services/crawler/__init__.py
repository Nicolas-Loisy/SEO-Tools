"""Web crawler services."""

from app.services.crawler.base import BaseCrawler, CrawledPage, CrawlResult, CrawlerException
from app.services.crawler.fast_crawler import FastCrawler
from app.services.crawler.factory import CrawlerFactory

__all__ = [
    "BaseCrawler",
    "CrawledPage",
    "CrawlResult",
    "CrawlerException",
    "FastCrawler",
    "CrawlerFactory",
]
