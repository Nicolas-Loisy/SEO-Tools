"""Celery tasks for web crawling."""

from datetime import datetime
from celery import Task
from app.workers.celery_app import celery_app
from app.core.database import SessionLocal
from app.models.crawl import CrawlJob


class CrawlTask(Task):
    """Base task for crawling with error handling."""

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Handle task failure."""
        job_id = args[0] if args else None
        if job_id:
            db = SessionLocal()
            try:
                job = db.query(CrawlJob).filter(CrawlJob.id == job_id).first()
                if job:
                    job.status = "failed"
                    job.finished_at = datetime.utcnow()
                    job.error_message = str(exc)
                    db.commit()
            finally:
                db.close()


@celery_app.task(base=CrawlTask, name="app.workers.crawler_tasks.crawl_site")
def crawl_site(job_id: int) -> dict:
    """
    Crawl a website based on crawl job configuration.

    Args:
        job_id: CrawlJob ID

    Returns:
        Crawl results dictionary
    """
    import asyncio
    from app.services.crawler import CrawlerFactory
    from app.models.project import Project
    from app.models.page import Page, Link

    db = SessionLocal()
    try:
        # Get job and project
        job = db.query(CrawlJob).filter(CrawlJob.id == job_id).first()
        if not job:
            raise ValueError(f"CrawlJob {job_id} not found")

        project = db.query(Project).filter(Project.id == job.project_id).first()
        if not project:
            raise ValueError(f"Project {job.project_id} not found")

        # Update status
        job.status = "running"
        job.started_at = datetime.utcnow()
        db.commit()

        # Prepare crawler config
        crawler_config = {
            "start_url": str(project.domain),
            "max_depth": job.config.get("depth", project.max_depth),
            "max_pages": job.config.get("max_pages", project.max_pages),
            "delay": project.crawl_delay,
            "respect_robots": project.respect_robots,
            "user_agent": "SEO-SaaS-Bot/1.0",
        }

        # Add Playwright-specific config if using JS mode
        if job.mode == "js":
            crawler_config.update({
                "headless": job.config.get("headless", True),
                "capture_screenshot": job.config.get("capture_screenshot", False),
                "screenshot_type": job.config.get("screenshot_type", "viewport"),
                "viewport": job.config.get("viewport", {"width": 1920, "height": 1080}),
                "wait_until": job.config.get("wait_until", "networkidle"),
                "timeout": job.config.get("timeout", 30000),
                "block_resources": job.config.get("block_resources", ["image", "font", "media"]),
            })

        # Create crawler using Factory pattern
        crawler = CrawlerFactory.create(job.mode, crawler_config)

        # Run crawler (async)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        crawl_result = loop.run_until_complete(crawler.crawl())
        loop.close()

        # Save pages to database
        from app.services.seo_analyzer import seo_analyzer
        total_links = 0
        for crawled_page in crawl_result.pages:
            # Count links (outgoing_links only contains internal links from the crawler)
            internal_links_count = len(crawled_page.outgoing_links)
            external_links_count = 0  # Not currently tracked by crawler

            # Calculate SEO score
            seo_score, _ = seo_analyzer.analyze_page(
                url=crawled_page.url,
                title=crawled_page.title,
                meta_description=crawled_page.meta_description,
                h1=crawled_page.h1,
                word_count=crawled_page.word_count,
                status_code=crawled_page.status_code,
                internal_links_count=internal_links_count,
            )

            # Create Page object
            page = Page(
                project_id=project.id,
                crawl_job_id=job.id,
                url=crawled_page.url,
                url_hash=crawled_page.url_hash,
                status_code=crawled_page.status_code,
                content_type=crawled_page.content_type,
                title=crawled_page.title,
                meta_description=crawled_page.meta_description,
                meta_keywords=crawled_page.meta_keywords,
                h1=crawled_page.h1,
                text_content=crawled_page.text_content,
                rendered_html=crawled_page.rendered_html,
                content_hash=crawled_page.content_hash,
                word_count=crawled_page.word_count,
                internal_links_count=internal_links_count,
                external_links_count=external_links_count,
                lang=crawled_page.lang,
                canonical_url=crawled_page.canonical_url,
                depth=crawled_page.depth,
                seo_score=seo_score,
                last_crawled_at=datetime.utcnow(),
            )

            # Check if page already exists
            existing = (
                db.query(Page)
                .filter(Page.project_id == project.id, Page.url_hash == crawled_page.url_hash)
                .first()
            )

            if existing:
                # Update existing page
                for key, value in page.__dict__.items():
                    if key not in ["_sa_instance_state", "id"]:
                        setattr(existing, key, value)
            else:
                db.add(page)

            db.flush()

            # Track outgoing links for later processing
            total_links += len(crawled_page.outgoing_links)

        # Commit all pages first
        db.commit()

        # Now create Link objects - we need all pages to exist first
        print(f"[CrawlerTask] Creating {total_links} link relationships...")

        # Create URL to page_id mapping
        url_to_page_id = {
            p.url: p.id for p in db.query(Page).filter(
                Page.project_id == project.id,
                Page.crawl_job_id == job.id
            ).all()
        }

        links_created = 0
        links_skipped = 0

        from app.models.page import Link

        for crawled_page in crawl_result.pages:
            # Get source page ID
            source_page_id = url_to_page_id.get(crawled_page.url)
            if not source_page_id:
                continue

            # Create links to each outgoing URL
            for target_url in crawled_page.outgoing_links:
                # Get target page ID
                target_page_id = url_to_page_id.get(target_url)

                if not target_page_id:
                    # Target page not in this crawl (external or not crawled yet)
                    links_skipped += 1
                    continue

                # Check if link already exists
                existing_link = db.query(Link).filter(
                    Link.source_page_id == source_page_id,
                    Link.target_page_id == target_page_id
                ).first()

                if existing_link:
                    # Link already exists, skip
                    continue

                # Create new Link object
                link = Link(
                    source_page_id=source_page_id,
                    target_page_id=target_page_id,
                    anchor_text=None,  # Could be extracted from HTML later
                    rel=None,
                    is_internal=True  # These are internal links from crawler
                )

                db.add(link)
                links_created += 1

        db.commit()
        print(f"[CrawlerTask] Created {links_created} links, skipped {links_skipped} (targets not found)")

        # Index pages to Meilisearch for full-text search
        try:
            from app.services.meilisearch_service import meilisearch_service

            # Get all pages for this crawl job to index
            pages_to_index = db.query(Page).filter(Page.crawl_job_id == job.id).all()

            # Format pages for Meilisearch
            documents = []
            for page in pages_to_index:
                documents.append({
                    "id": page.id,
                    "project_id": page.project_id,
                    "crawl_job_id": page.crawl_job_id,
                    "url": page.url,
                    "title": page.title or "",
                    "meta_description": page.meta_description or "",
                    "h1": page.h1 or "",
                    "text_content": page.text_content or "",
                    "status_code": page.status_code,
                    "word_count": page.word_count,
                    "seo_score": page.seo_score,
                    "depth": page.depth,
                    "internal_links_count": page.internal_links_count,
                    "external_links_count": page.external_links_count,
                })

            # Index documents in bulk
            if documents:
                meilisearch_service.index_pages_bulk(documents)
        except Exception as e:
            # Log error but don't fail the crawl
            print(f"Warning: Failed to index pages to Meilisearch: {e}")

        # Update job with results
        job.status = "completed"
        job.finished_at = datetime.utcnow()
        job.duration_seconds = (job.finished_at - job.started_at).total_seconds()
        job.pages_discovered = crawl_result.total_discovered
        job.pages_crawled = crawl_result.total_crawled
        job.pages_failed = crawl_result.total_failed
        job.links_found = total_links
        db.commit()

        # Update project last crawl time
        project.last_crawl_at = datetime.utcnow()
        db.commit()

        return {
            "pages_discovered": crawl_result.total_discovered,
            "pages_crawled": crawl_result.total_crawled,
            "pages_failed": crawl_result.total_failed,
            "links_found": total_links,
        }

    except Exception as e:
        if db:
            job = db.query(CrawlJob).filter(CrawlJob.id == job_id).first()
            if job:
                job.status = "failed"
                job.finished_at = datetime.utcnow()
                job.error_message = str(e)
                if job.started_at:
                    job.duration_seconds = (job.finished_at - job.started_at).total_seconds()
                db.commit()
        raise
    finally:
        db.close()


@celery_app.task(name="app.workers.crawler_tasks.check_scheduled_crawls")
def check_scheduled_crawls() -> None:
    """
    Check for scheduled crawls and enqueue them.

    This task runs periodically to check projects with cron schedules.
    """
    # TODO: Implement scheduled crawl checking
    pass
