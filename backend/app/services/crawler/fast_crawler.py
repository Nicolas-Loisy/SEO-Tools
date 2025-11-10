"""Fast crawler using requests and BeautifulSoup with language detection."""

import asyncio
import hashlib
from datetime import datetime
from typing import List, Dict, Any, Set
from urllib.parse import urljoin, urlparse
import aiohttp
from bs4 import BeautifulSoup
from tenacity import retry, stop_after_attempt, wait_exponential

from app.services.crawler.base import BaseCrawler, CrawledPage, CrawlResult, CrawlerException
from app.services.nlp.language import detect_language


class FastCrawler(BaseCrawler):
    """
    Fast crawler for static HTML sites using aiohttp and BeautifulSoup.

    Does not execute JavaScript - suitable for static sites only.
    """

    def __init__(self, config: Dict[str, Any]):
        """Initialize fast crawler."""
        super().__init__(config)
        self.visited_urls: Set[str] = set()
        self.pages: List[CrawledPage] = []
        self.errors: List[Dict[str, Any]] = []
        self.session: aiohttp.ClientSession | None = None
        self._should_stop = False

    async def crawl(self) -> CrawlResult:
        """
        Execute the crawl.

        Returns:
            CrawlResult with all crawled pages
        """
        started_at = datetime.utcnow()

        try:
            # Create aiohttp session
            timeout = aiohttp.ClientTimeout(total=30)
            self.session = aiohttp.ClientSession(
                timeout=timeout,
                headers={"User-Agent": self.user_agent},
            )

            # Start crawling from start URL
            await self._crawl_url(self.start_url, depth=0)

            finished_at = datetime.utcnow()

            return CrawlResult(
                pages=self.pages,
                total_discovered=len(self.visited_urls),
                total_crawled=len(self.pages),
                total_failed=len(self.errors),
                errors=self.errors,
                started_at=started_at,
                finished_at=finished_at,
            )

        except Exception as e:
            raise CrawlerException(f"Crawl failed: {str(e)}") from e

        finally:
            if self.session:
                await self.session.close()

    async def stop(self) -> None:
        """Stop the crawler gracefully."""
        self._should_stop = True
        if self.session:
            await self.session.close()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True,
    )
    async def _fetch_page(self, url: str) -> tuple[int, str, str]:
        """
        Fetch a page with retries.

        Args:
            url: URL to fetch

        Returns:
            Tuple of (status_code, content_type, html)
        """
        if not self.session:
            raise CrawlerException("Session not initialized")

        async with self.session.get(url) as response:
            content_type = response.headers.get("Content-Type", "")
            html = await response.text()
            return response.status, content_type, html

    async def _crawl_url(self, url: str, depth: int) -> None:
        """
        Crawl a single URL.

        Args:
            url: URL to crawl
            depth: Current depth
        """
        # Check stopping conditions
        if self._should_stop:
            return

        if depth > self.max_depth:
            return

        if len(self.pages) >= self.max_pages:
            return

        if url in self.visited_urls:
            return

        if not self._should_crawl_url(url):
            return

        # Mark as visited
        self.visited_urls.add(url)

        # Apply delay
        if self.delay > 0 and len(self.pages) > 0:
            await asyncio.sleep(self.delay)

        try:
            # Fetch page
            status_code, content_type, html = await self._fetch_page(url)

            # Parse page
            page = await self._parse_page(url, status_code, content_type, html, depth)
            self.pages.append(page)

            # Crawl outgoing links
            if depth < self.max_depth:
                tasks = []
                for link_url in page.outgoing_links:
                    if len(self.pages) < self.max_pages:
                        tasks.append(self._crawl_url(link_url, depth + 1))

                # Crawl links concurrently (limited)
                if tasks:
                    await asyncio.gather(*tasks[:10])  # Limit concurrent requests

        except Exception as e:
            self.errors.append(
                {
                    "url": url,
                    "depth": depth,
                    "error": str(e),
                    "timestamp": datetime.utcnow().isoformat(),
                }
            )

    async def _parse_page(
        self, url: str, status_code: int, content_type: str, html: str, depth: int
    ) -> CrawledPage:
        """
        Parse HTML and extract SEO information.

        Args:
            url: Page URL
            status_code: HTTP status code
            content_type: Content type
            html: HTML content
            depth: Crawl depth

        Returns:
            CrawledPage object
        """
        soup = BeautifulSoup(html, "lxml")

        # Extract title
        title_tag = soup.find("title")
        title = title_tag.get_text(strip=True) if title_tag else None

        # Extract meta description
        meta_desc = soup.find("meta", attrs={"name": "description"})
        meta_description = meta_desc.get("content") if meta_desc else None

        # Extract meta keywords
        meta_kw = soup.find("meta", attrs={"name": "keywords"})
        meta_keywords = meta_kw.get("content") if meta_kw else None

        # Extract H1
        h1_tag = soup.find("h1")
        h1 = h1_tag.get_text(strip=True) if h1_tag else None

        # Extract text content
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
        text_content = soup.get_text(separator=" ", strip=True)
        word_count = len(text_content.split())

        # Extract lang from HTML attribute
        html_tag = soup.find("html")
        lang_from_html = html_tag.get("lang") if html_tag else None

        # Auto-detect language from content if not specified or too generic
        if not lang_from_html or len(lang_from_html) > 5:
            # HTML lang attribute is missing or too generic (e.g., "en-US" → use "en")
            detected = detect_language(text_content)
            lang = detected if detected else lang_from_html
        else:
            # Clean HTML lang (e.g., "en-US" → "en")
            lang = lang_from_html.split("-")[0] if lang_from_html else None

        # Extract canonical
        canonical_tag = soup.find("link", attrs={"rel": "canonical"})
        canonical_url = canonical_tag.get("href") if canonical_tag else None

        # Extract hreflang
        hreflang_tags = soup.find_all("link", attrs={"rel": "alternate", "hreflang": True})
        hreflang = {tag.get("hreflang"): tag.get("href") for tag in hreflang_tags} if hreflang_tags else None

        # Extract outgoing links
        outgoing_links = []
        base_domain = urlparse(url).netloc

        for link in soup.find_all("a", href=True):
            href = link.get("href")
            if not href:
                continue

            # Resolve relative URLs
            absolute_url = urljoin(url, href)
            parsed = urlparse(absolute_url)

            # Only internal links
            if parsed.netloc == base_domain:
                outgoing_links.append(absolute_url)

        # Generate hashes
        url_hash = hashlib.sha256(url.encode()).hexdigest()
        content_hash = hashlib.md5(text_content.encode()).hexdigest()

        return CrawledPage(
            url=url,
            url_hash=url_hash,
            status_code=status_code,
            content_type=content_type,
            title=title,
            meta_description=meta_description,
            meta_keywords=meta_keywords,
            h1=h1,
            text_content=text_content,
            rendered_html=html[:10000] if len(html) <= 10000 else None,  # Limit stored HTML
            content_hash=content_hash,
            word_count=word_count,
            lang=lang,
            canonical_url=canonical_url,
            hreflang=hreflang,
            depth=depth,
            outgoing_links=outgoing_links,
        )
