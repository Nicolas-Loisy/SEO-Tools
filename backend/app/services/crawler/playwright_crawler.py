"""Playwright crawler for JavaScript-heavy sites with screenshot support."""

import asyncio
import hashlib
import base64
from datetime import datetime
from typing import List, Dict, Any, Set, Optional
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright, Page, Browser, BrowserContext, Error as PlaywrightError
from tenacity import retry, stop_after_attempt, wait_exponential

from app.services.crawler.base import BaseCrawler, CrawledPage, CrawlResult, CrawlerException
from app.services.nlp.language import detect_language


class PlaywrightCrawler(BaseCrawler):
    """
    Advanced crawler for JavaScript-heavy sites using Playwright.

    Features:
    - Executes JavaScript and waits for page load
    - Captures screenshots (full page or viewport)
    - Detects JavaScript errors
    - Supports custom viewport sizes
    - Mobile/Desktop user agent switching
    """

    def __init__(self, config: Dict[str, Any]):
        """Initialize Playwright crawler."""
        super().__init__(config)
        self.visited_urls: Set[str] = set()
        self.pages: List[CrawledPage] = []
        self.errors: List[Dict[str, Any]] = []
        self._should_stop = False

        # Playwright specific config
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.headless = config.get("headless", True)
        self.capture_screenshot = config.get("capture_screenshot", False)
        self.screenshot_type = config.get("screenshot_type", "viewport")  # viewport or fullpage
        self.viewport = config.get("viewport", {"width": 1920, "height": 1080})
        self.wait_until = config.get("wait_until", "networkidle")  # load, domcontentloaded, networkidle
        self.timeout = config.get("timeout", 30000)  # 30 seconds
        self.block_resources = config.get("block_resources", ["image", "font", "media"])  # Optimize speed

        # JavaScript error tracking
        self.js_errors: Dict[str, List[str]] = {}

    async def crawl(self) -> CrawlResult:
        """
        Execute the crawl with Playwright.

        Returns:
            CrawlResult with all crawled pages
        """
        started_at = datetime.utcnow()

        try:
            # Launch Playwright
            async with async_playwright() as p:
                # Launch browser
                self.browser = await p.chromium.launch(headless=self.headless)

                # Create context with configuration
                self.context = await self.browser.new_context(
                    viewport=self.viewport,
                    user_agent=self.user_agent,
                )

                # Block resources to improve performance
                if self.block_resources:
                    await self.context.route(
                        "**/*",
                        lambda route: (
                            route.abort()
                            if route.request.resource_type in self.block_resources
                            else route.continue_()
                        ),
                    )

                # Start crawling
                await self._crawl_url(self.start_url, depth=0)

                # Close browser
                await self.context.close()
                await self.browser.close()

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
            raise CrawlerException(f"Playwright crawl failed: {str(e)}") from e

        finally:
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()

    async def stop(self) -> None:
        """Stop the crawler gracefully."""
        self._should_stop = True
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True,
    )
    async def _fetch_page(self, url: str) -> tuple[Page, int, str]:
        """
        Fetch a page with Playwright and retries.

        Args:
            url: URL to fetch

        Returns:
            Tuple of (page, status_code, html)
        """
        if not self.context:
            raise CrawlerException("Browser context not initialized")

        page = await self.context.new_page()

        # Track JavaScript errors
        js_errors = []

        def log_console_message(msg):
            """Log console errors."""
            if msg.type in ["error", "warning"]:
                js_errors.append(f"[{msg.type}] {msg.text}")

        page.on("console", log_console_message)

        # Navigate to page
        try:
            response = await page.goto(
                url,
                wait_until=self.wait_until,
                timeout=self.timeout,
            )

            status_code = response.status if response else 0

            # Wait for dynamic content to render (increased for JS frameworks)
            await page.wait_for_timeout(3000)  # 3 seconds for React/Vue/etc

            # Additional wait: ensure body has actual content (not just "enable JS" message)
            try:
                # Wait for body to have meaningful content
                await page.wait_for_function(
                    """() => {
                        const body = document.body;
                        return body && body.innerText && body.innerText.length > 100;
                    }""",
                    timeout=5000  # 5 seconds max
                )
            except Exception:
                # If timeout, continue anyway (some pages might be legitimately small)
                pass

            # Get rendered HTML
            html = await page.content()

            # Store JS errors for this URL
            if js_errors:
                self.js_errors[url] = js_errors

            return page, status_code, html

        except PlaywrightError as e:
            await page.close()
            raise CrawlerException(f"Failed to load {url}: {str(e)}") from e

    async def _crawl_url(self, url: str, depth: int) -> None:
        """
        Crawl a single URL with Playwright.

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

        page_obj = None

        try:
            # Fetch page with Playwright
            page_obj, status_code, html = await self._fetch_page(url)

            # Capture screenshot if enabled
            screenshot_data = None
            if self.capture_screenshot:
                screenshot_data = await self._capture_screenshot(page_obj)

            # Parse page
            crawled_page = await self._parse_page(
                url, status_code, html, depth, screenshot_data
            )
            self.pages.append(crawled_page)

            # Close the page
            await page_obj.close()
            page_obj = None

            # Crawl outgoing links (sequentially to avoid browser overload)
            if depth < self.max_depth:
                for link_url in crawled_page.outgoing_links[:10]:  # Limit links per page
                    if len(self.pages) < self.max_pages:
                        await self._crawl_url(link_url, depth + 1)
                    else:
                        break

        except Exception as e:
            self.errors.append(
                {
                    "url": url,
                    "depth": depth,
                    "error": str(e),
                    "js_errors": self.js_errors.get(url, []),
                    "timestamp": datetime.utcnow().isoformat(),
                }
            )

        finally:
            # Ensure page is closed
            if page_obj:
                await page_obj.close()

    async def _capture_screenshot(self, page: Page) -> Optional[str]:
        """
        Capture screenshot of the page.

        Args:
            page: Playwright page object

        Returns:
            Base64 encoded screenshot or None
        """
        try:
            screenshot_bytes = await page.screenshot(
                full_page=(self.screenshot_type == "fullpage"),
                type="png",
            )
            # Encode to base64 for storage
            return base64.b64encode(screenshot_bytes).decode("utf-8")
        except Exception as e:
            print(f"Screenshot capture failed: {e}")
            return None

    async def _parse_page(
        self,
        url: str,
        status_code: int,
        html: str,
        depth: int,
        screenshot_data: Optional[str] = None,
    ) -> CrawledPage:
        """
        Parse rendered HTML and extract SEO information.

        Args:
            url: Page URL
            status_code: HTTP status code
            html: Rendered HTML content
            depth: Crawl depth
            screenshot_data: Base64 encoded screenshot

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
        for script in soup(["script", "style"]):
            script.decompose()
        text_content = soup.get_text(separator=" ", strip=True)
        word_count = len(text_content.split())

        # Extract lang from HTML attribute
        html_tag = soup.find("html")
        lang_from_html = html_tag.get("lang") if html_tag else None

        # Auto-detect language
        if not lang_from_html or len(lang_from_html) > 5:
            detected = detect_language(text_content)
            lang = detected if detected else lang_from_html
        else:
            lang = lang_from_html.split("-")[0] if lang_from_html else None

        # Extract canonical
        canonical_tag = soup.find("link", attrs={"rel": "canonical"})
        canonical_url = canonical_tag.get("href") if canonical_tag else None

        # Extract hreflang
        hreflang_tags = soup.find_all("link", attrs={"rel": "alternate", "hreflang": True})
        hreflang = (
            {tag.get("hreflang"): tag.get("href") for tag in hreflang_tags}
            if hreflang_tags
            else None
        )

        # Extract outgoing links with anchor text
        outgoing_links = []
        base_domain = urlparse(url).netloc

        for link in soup.find_all("a", href=True):
            href = link.get("href")
            if not href:
                continue

            absolute_url = urljoin(url, href)
            parsed = urlparse(absolute_url)

            # Only internal links
            if parsed.netloc == base_domain:
                # Extract anchor text (strip whitespace and newlines)
                anchor_text = link.get_text(strip=True)
                outgoing_links.append({
                    "url": absolute_url,
                    "anchor_text": anchor_text if anchor_text else None
                })

        # Generate hashes
        url_hash = hashlib.sha256(url.encode()).hexdigest()
        content_hash = hashlib.md5(text_content.encode()).hexdigest()

        # Store screenshot in rendered_html field if available (temporary solution)
        # TODO: Store screenshots in MinIO/S3 instead
        rendered_html_data = None
        if screenshot_data:
            rendered_html_data = f"SCREENSHOT:{screenshot_data[:1000]}"  # Truncate for DB
        elif len(html) <= 10000:
            rendered_html_data = html

        return CrawledPage(
            url=url,
            url_hash=url_hash,
            status_code=status_code,
            content_type="text/html",  # Playwright always returns HTML
            title=title,
            meta_description=meta_description,
            meta_keywords=meta_keywords,
            h1=h1,
            text_content=text_content,
            rendered_html=rendered_html_data,
            content_hash=content_hash,
            word_count=word_count,
            lang=lang,
            canonical_url=canonical_url,
            hreflang=hreflang,
            depth=depth,
            outgoing_links=outgoing_links,
        )
