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
    db = SessionLocal()
    try:
        # Get job
        job = db.query(CrawlJob).filter(CrawlJob.id == job_id).first()
        if not job:
            raise ValueError(f"CrawlJob {job_id} not found")

        # Update status
        job.status = "running"
        job.started_at = datetime.utcnow()
        db.commit()

        # TODO: Implement actual crawling logic
        # This will use the Factory pattern to select crawler
        # from app.services.crawler import CrawlerFactory
        # crawler = CrawlerFactory.create(job.mode, job.project, job.config)
        # results = crawler.crawl()

        # Placeholder results
        results = {
            "pages_discovered": 0,
            "pages_crawled": 0,
            "pages_failed": 0,
            "links_found": 0,
        }

        # Update job
        job.status = "completed"
        job.finished_at = datetime.utcnow()
        job.duration_seconds = (job.finished_at - job.started_at).total_seconds()
        job.pages_discovered = results["pages_discovered"]
        job.pages_crawled = results["pages_crawled"]
        job.pages_failed = results["pages_failed"]
        job.links_found = results["links_found"]
        db.commit()

        return results

    except Exception as e:
        if db:
            job = db.query(CrawlJob).filter(CrawlJob.id == job_id).first()
            if job:
                job.status = "failed"
                job.finished_at = datetime.utcnow()
                job.error_message = str(e)
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
