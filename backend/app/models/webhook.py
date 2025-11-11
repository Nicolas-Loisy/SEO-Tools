"""Webhook models for event notifications."""

from datetime import datetime
from sqlalchemy import String, Integer, DateTime, ForeignKey, Boolean, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class Webhook(Base):
    """
    Webhook configuration model.

    Stores webhook endpoints that receive notifications for various events.
    Supports multiple event types and customizable payloads.
    """

    __tablename__ = "webhooks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    tenant_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Webhook configuration
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    url: Mapped[str] = mapped_column(String(2048), nullable=False)
    secret: Mapped[str] = mapped_column(String(255), nullable=True)  # For HMAC signing
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Event subscriptions (comma-separated or JSON array)
    events: Mapped[list] = mapped_column(JSON, default=list)
    # Possible events:
    # - crawl.started
    # - crawl.completed
    # - crawl.failed
    # - analysis.completed
    # - content.generated
    # - quota.warning (80%)
    # - quota.exceeded (100%)
    # - project.created
    # - project.deleted

    # Delivery configuration
    max_retries: Mapped[int] = mapped_column(Integer, default=3)
    retry_delay: Mapped[int] = mapped_column(Integer, default=60)  # seconds
    timeout: Mapped[int] = mapped_column(Integer, default=30)  # seconds

    # Custom headers (JSON)
    custom_headers: Mapped[dict] = mapped_column(JSON, default=dict, nullable=True)

    # Metadata
    description: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    last_triggered_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)

    # Relationships
    tenant: Mapped["Tenant"] = relationship("Tenant", back_populates="webhooks")
    deliveries: Mapped[list["WebhookDelivery"]] = relationship(
        "WebhookDelivery", back_populates="webhook", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Webhook(id={self.id}, name='{self.name}', events={self.events})>"


class WebhookDelivery(Base):
    """
    Webhook delivery log model.

    Tracks all webhook delivery attempts including request/response data,
    status, and retry information.
    """

    __tablename__ = "webhook_deliveries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    webhook_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("webhooks.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Event information
    event_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    event_id: Mapped[str] = mapped_column(String(255), nullable=True)  # Reference to source event

    # Request details
    payload: Mapped[dict] = mapped_column(JSON, nullable=False)
    headers: Mapped[dict] = mapped_column(JSON, nullable=True)

    # Response details
    status_code: Mapped[int] = mapped_column(Integer, nullable=True)
    response_body: Mapped[str] = mapped_column(Text, nullable=True)
    response_headers: Mapped[dict] = mapped_column(JSON, nullable=True)

    # Delivery status
    success: Mapped[bool] = mapped_column(Boolean, default=False)
    error_message: Mapped[str] = mapped_column(Text, nullable=True)

    # Retry information
    attempt_number: Mapped[int] = mapped_column(Integer, default=1)
    next_retry_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)

    # Timing
    duration_ms: Mapped[int] = mapped_column(Integer, nullable=True)  # Response time
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    delivered_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)

    # Relationships
    webhook: Mapped["Webhook"] = relationship("Webhook", back_populates="deliveries")

    def __repr__(self) -> str:
        return f"<WebhookDelivery(id={self.id}, event='{self.event_type}', success={self.success})>"
