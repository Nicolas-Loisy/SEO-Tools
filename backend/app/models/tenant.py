"""Tenant model for multi-tenancy."""

from datetime import datetime
from sqlalchemy import String, Integer, DateTime, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class Tenant(Base):
    """
    Tenant model for multi-tenant SaaS architecture.

    Each tenant represents a separate customer/organization with isolated data.
    """

    __tablename__ = "tenants"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)

    # Subscription & Billing
    plan: Mapped[str] = mapped_column(String(50), default="free")  # free, starter, pro, enterprise
    billing_info: Mapped[dict] = mapped_column(JSON, nullable=True)

    # Quotas
    max_projects: Mapped[int] = mapped_column(Integer, default=5)
    max_pages_per_crawl: Mapped[int] = mapped_column(Integer, default=1000)
    max_api_calls_per_month: Mapped[int] = mapped_column(Integer, default=10000)

    # Status
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    projects: Mapped[list["Project"]] = relationship(
        "Project", back_populates="tenant", cascade="all, delete-orphan"
    )
    webhooks: Mapped[list["Webhook"]] = relationship(
        "Webhook", back_populates="tenant", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Tenant(id={self.id}, name='{self.name}', plan='{self.plan}')>"
