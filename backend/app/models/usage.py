"""API Usage tracking model for rate limiting and quotas."""

from datetime import datetime
from sqlalchemy import String, Integer, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class APIUsage(Base):
    """
    Track API usage for rate limiting and billing.

    Stores usage statistics per tenant on a monthly basis.
    """

    __tablename__ = "api_usage"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"), nullable=False, index=True)

    # Time period
    year: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    month: Mapped[int] = mapped_column(Integer, nullable=False, index=True)  # 1-12

    # Usage counters
    total_api_calls: Mapped[int] = mapped_column(Integer, default=0)
    crawl_jobs: Mapped[int] = mapped_column(Integer, default=0)
    pages_crawled: Mapped[int] = mapped_column(Integer, default=0)
    analysis_requests: Mapped[int] = mapped_column(Integer, default=0)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    tenant: Mapped["Tenant"] = relationship("Tenant")

    def __repr__(self) -> str:
        return f"<APIUsage(tenant_id={self.tenant_id}, period={self.year}-{self.month:02d}, calls={self.total_api_calls})>"

    @property
    def period_key(self) -> str:
        """Get a string key for this period."""
        return f"{self.year}-{self.month:02d}"


class RateLimitLog(Base):
    """
    Log rate limit violations for monitoring and abuse detection.
    """

    __tablename__ = "rate_limit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"), nullable=False, index=True)

    # Request details
    endpoint: Mapped[str] = mapped_column(String(500), nullable=False)
    method: Mapped[str] = mapped_column(String(10), nullable=False)
    ip_address: Mapped[str] = mapped_column(String(45), nullable=True)  # IPv6 max length

    # Limit details
    limit_type: Mapped[str] = mapped_column(String(50), nullable=False)  # monthly, daily, hourly
    limit_value: Mapped[int] = mapped_column(Integer, nullable=False)
    current_usage: Mapped[int] = mapped_column(Integer, nullable=False)

    # Timestamp
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)

    # Relationships
    tenant: Mapped["Tenant"] = relationship("Tenant")

    def __repr__(self) -> str:
        return f"<RateLimitLog(tenant_id={self.tenant_id}, endpoint='{self.endpoint}', limit={self.limit_value})>"
