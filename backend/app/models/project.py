"""Project model for site management."""

from datetime import datetime
from sqlalchemy import String, Integer, DateTime, JSON, ForeignKey, Boolean, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class Project(Base):
    """
    Project model representing a website to be analyzed/optimized.

    Each project belongs to a tenant and contains configuration for crawling
    and SEO analysis.
    """

    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    tenant_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Basic info
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    domain: Mapped[str] = mapped_column(String(255), nullable=False)

    # URLs
    sitemap_url: Mapped[str] = mapped_column(String(500), nullable=True)
    robots_txt_url: Mapped[str] = mapped_column(String(500), nullable=True)

    # Crawl Settings
    js_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    max_depth: Mapped[int] = mapped_column(Integer, default=3)
    max_pages: Mapped[int] = mapped_column(Integer, default=1000)
    crawl_delay: Mapped[float] = mapped_column(default=1.0)
    respect_robots: Mapped[bool] = mapped_column(Boolean, default=True)

    # JS-specific settings
    wait_for_selector: Mapped[str] = mapped_column(String(255), nullable=True)
    wait_for_timeout: Mapped[int] = mapped_column(Integer, default=3000)
    wait_for_network_idle: Mapped[bool] = mapped_column(Boolean, default=True)

    # Schedule
    crawl_schedule: Mapped[str] = mapped_column(String(100), nullable=True)  # cron format

    # Additional settings
    settings: Mapped[dict] = mapped_column(JSON, default=dict)

    # Metadata
    description: Mapped[str] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    last_crawl_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)

    # Relationships
    tenant: Mapped["Tenant"] = relationship("Tenant", back_populates="projects")
    pages: Mapped[list["Page"]] = relationship(
        "Page", back_populates="project", cascade="all, delete-orphan"
    )
    crawl_jobs: Mapped[list["CrawlJob"]] = relationship(
        "CrawlJob", back_populates="project", cascade="all, delete-orphan"
    )
    site_trees: Mapped[list["SiteTree"]] = relationship(
        "SiteTree", back_populates="project", cascade="all, delete-orphan"
    )
    content_drafts: Mapped[list["ContentDraft"]] = relationship(
        "ContentDraft", back_populates="project", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Project(id={self.id}, name='{self.name}', domain='{self.domain}')>"
