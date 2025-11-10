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

        # Create crawler using Factory pattern
        crawler = CrawlerFactory.create(job.mode, crawler_config)

        # Run crawler (async)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        crawl_result = loop.run_until_complete(crawler.crawl())
        loop.close()

        # Save pages to database
        total_links = 0
        for crawled_page in crawl_result.pages:
            # Create Page object
            page = Page(
                project_id=project.id,
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
                lang=crawled_page.lang,
                canonical_url=crawled_page.canonical_url,
                depth=crawled_page.depth,
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

            # Save links
            total_links += len(crawled_page.outgoing_links)

        db.commit()

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
