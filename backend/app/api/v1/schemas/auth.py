"""Authentication schemas."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class APIKeyCreate(BaseModel):
    """Schema for creating an API key."""

    name: str = Field(..., min_length=1, max_length=255, description="Key name")
    description: Optional[str] = Field(None, max_length=500, description="Key description")
    scopes: str = Field("read,write", description="Comma-separated scopes")
    expires_at: Optional[datetime] = Field(None, description="Expiration date (None = never)")


class APIKeyResponse(BaseModel):
    """Schema for API key response (without the actual key)."""

    id: int
    tenant_id: int
    key_prefix: str
    name: str
    description: Optional[str]
    scopes: str
    is_active: bool
    last_used_at: Optional[datetime]
    created_at: datetime
    expires_at: Optional[datetime]

    class Config:
        from_attributes = True


class APIKeyCreateResponse(BaseModel):
    """Schema for API key creation response (includes actual key once)."""

    key: str = Field(..., description="The actual API key - save it now, won't be shown again!")
    key_info: APIKeyResponse


class TenantResponse(BaseModel):
    """Schema for tenant response."""

    id: int
    name: str
    slug: str
    plan: str
    max_projects: int
    max_pages_per_crawl: int
    max_api_calls_per_month: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True
