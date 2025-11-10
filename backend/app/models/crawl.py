"""Crawl job model for tracking crawler execution."""

from datetime import datetime
from sqlalchemy import String, Integer, DateTime, ForeignKey, JSON, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class CrawlJob(Base):
    """
    CrawlJob model for tracking crawl execution and metrics.

    Implements Command pattern - encapsulates crawl request for history/replay.
    """

    __tablename__ = "crawl_jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    project_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Job metadata
    status: Mapped[str] = mapped_column(
        String(50), default="pending"
    )  # pending, running, completed, failed, cancelled
    mode: Mapped[str] = mapped_column(String(20), default="fast")  # fast, js

    # Configuration (Command pattern - stores job parameters)
    config: Mapped[dict] = mapped_column(JSON, default=dict)  # depth, max_pages, selectors, etc.

    # Execution
    started_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    finished_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    duration_seconds: Mapped[float] = mapped_column(default=0.0)

    # Metrics
    pages_discovered: Mapped[int] = mapped_column(Integer, default=0)
    pages_crawled: Mapped[int] = mapped_column(Integer, default=0)
    pages_failed: Mapped[int] = mapped_column(Integer, default=0)
    links_found: Mapped[int] = mapped_column(Integer, default=0)

    # Error tracking
    error_message: Mapped[str] = mapped_column(Text, nullable=True)
    error_details: Mapped[dict] = mapped_column(JSON, nullable=True)

    # Celery task ID for tracking async execution
    celery_task_id: Mapped[str] = mapped_column(String(255), nullable=True, index=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    project: Mapped["Project"] = relationship("Project", back_populates="crawl_jobs")

    def __repr__(self) -> str:
        return f"<CrawlJob(id={self.id}, status='{self.status}', mode='{self.mode}')>"

    @property
    def is_running(self) -> bool:
        """Check if job is currently running."""
        return self.status in ("pending", "running")

    @property
    def is_finished(self) -> bool:
        """Check if job has finished (success or failure)."""
        return self.status in ("completed", "failed", "cancelled")
