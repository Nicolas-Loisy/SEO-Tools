"""Tests for crawler factory."""

import pytest
from app.services.crawler.factory import CrawlerFactory
from app.services.crawler.fast_crawler import FastCrawler
from app.services.crawler.playwright_crawler import PlaywrightCrawler


def test_create_fast_crawler():
    """Test creating fast crawler."""
    config = {
        "start_url": "https://example.com",
        "max_depth": 2,
        "max_pages": 50,
    }
    crawler = CrawlerFactory.create(mode="fast", config=config)
    assert isinstance(crawler, FastCrawler)
    assert crawler.start_url == "https://example.com"
    assert crawler.max_depth == 2


def test_create_js_crawler():
    """Test creating Playwright crawler."""
    config = {
        "start_url": "https://example.com",
        "max_depth": 1,
        "headless": True,
    }
    crawler = CrawlerFactory.create(mode="js", config=config)
    assert isinstance(crawler, PlaywrightCrawler)
    assert crawler.headless is True


def test_create_invalid_mode():
    """Test creating crawler with invalid mode."""
    with pytest.raises(ValueError) as exc_info:
        CrawlerFactory.create(mode="invalid", config={})
    assert "Unknown crawler mode" in str(exc_info.value)


def test_crawler_configuration():
    """Test crawler inherits configuration correctly."""
    config = {
        "start_url": "https://test.com",
        "max_depth": 5,
        "max_pages": 1000,
        "delay": 2.0,
        "user_agent": "TestBot/1.0",
    }
    crawler = CrawlerFactory.create(mode="fast", config=config)
    
    assert crawler.start_url == "https://test.com"
    assert crawler.max_depth == 5
    assert crawler.max_pages == 1000
    assert crawler.delay == 2.0
    assert crawler.user_agent == "TestBot/1.0"
