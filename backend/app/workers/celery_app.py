"""Celery application configuration."""

from celery import Celery
from app.core.config import settings

# Create Celery instance
celery_app = Celery(
    "seo_saas",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "app.workers.crawler_tasks",
        "app.workers.content_tasks",
        "app.workers.analysis_tasks",
    ],
)

# Configure Celery
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 hour max
    task_soft_time_limit=3000,  # 50 minutes soft limit
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=50,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    result_expires=86400,  # 24 hours
)

# Task routes
celery_app.conf.task_routes = {
    "app.workers.crawler_tasks.*": {"queue": "crawler"},
    "app.workers.content_tasks.*": {"queue": "content"},
    "app.workers.analysis_tasks.*": {"queue": "analysis"},
}

# Beat schedule (for periodic tasks)
celery_app.conf.beat_schedule = {
    # Add periodic tasks here
    # "check-scheduled-crawls": {
    #     "task": "app.workers.crawler_tasks.check_scheduled_crawls",
    #     "schedule": 300.0,  # every 5 minutes
    # },
}
