"""Webhook schemas for API."""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, HttpUrl
from datetime import datetime


class WebhookCreateRequest(BaseModel):
    """Request to create a new webhook."""

    name: str = Field(..., min_length=1, max_length=255, description="Webhook name")
    url: HttpUrl = Field(..., description="Webhook endpoint URL")
    secret: Optional[str] = Field(None, max_length=255, description="Secret key for HMAC signing")
    events: List[str] = Field(..., min_items=1, description="List of event types to subscribe to")
    max_retries: int = Field(3, ge=0, le=10, description="Maximum retry attempts (0-10)")
    retry_delay: int = Field(60, ge=10, le=3600, description="Retry delay in seconds (10-3600)")
    timeout: int = Field(30, ge=5, le=300, description="Request timeout in seconds (5-300)")
    custom_headers: Optional[Dict[str, str]] = Field(None, description="Custom HTTP headers")
    description: Optional[str] = Field(None, description="Webhook description")

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Production Webhook",
                "url": "https://api.example.com/webhooks/seo-events",
                "secret": "your-secret-key",
                "events": ["crawl.completed", "quota.warning"],
                "max_retries": 3,
                "retry_delay": 60,
                "timeout": 30,
                "custom_headers": {"X-Custom-Header": "value"},
                "description": "Main webhook for production notifications",
            }
        }


class WebhookUpdateRequest(BaseModel):
    """Request to update a webhook."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    url: Optional[HttpUrl] = None
    secret: Optional[str] = Field(None, max_length=255)
    events: Optional[List[str]] = Field(None, min_items=1)
    is_active: Optional[bool] = None
    max_retries: Optional[int] = Field(None, ge=0, le=10)
    retry_delay: Optional[int] = Field(None, ge=10, le=3600)
    timeout: Optional[int] = Field(None, ge=5, le=300)
    custom_headers: Optional[Dict[str, str]] = None
    description: Optional[str] = None


class WebhookResponse(BaseModel):
    """Webhook response."""

    id: int
    name: str
    url: str
    is_active: bool
    events: List[str]
    max_retries: int
    retry_delay: int
    timeout: int
    custom_headers: Optional[Dict[str, str]]
    description: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]
    last_triggered_at: Optional[datetime]

    class Config:
        from_attributes = True


class WebhookListResponse(BaseModel):
    """List of webhooks."""

    webhooks: List[WebhookResponse]
    total: int


class WebhookDeliveryResponse(BaseModel):
    """Webhook delivery response."""

    id: int
    webhook_id: int
    event_type: str
    event_id: Optional[str]
    payload: Dict[str, Any]
    status_code: Optional[int]
    success: bool
    error_message: Optional[str]
    attempt_number: int
    next_retry_at: Optional[datetime]
    duration_ms: Optional[int]
    created_at: datetime
    delivered_at: Optional[datetime]

    class Config:
        from_attributes = True


class WebhookDeliveryListResponse(BaseModel):
    """List of webhook deliveries."""

    deliveries: List[WebhookDeliveryResponse]
    total: int


class WebhookStatsResponse(BaseModel):
    """Webhook delivery statistics."""

    total_deliveries: int
    successful_deliveries: int
    failed_deliveries: int
    success_rate: float
    avg_response_time_ms: float


class WebhookTestRequest(BaseModel):
    """Request to test a webhook."""

    event_type: str = Field("test.ping", description="Event type for test")
    test_payload: Optional[Dict[str, Any]] = Field(None, description="Optional test payload")


class WebhookEventsResponse(BaseModel):
    """Available webhook events."""

    events: Dict[str, str]
