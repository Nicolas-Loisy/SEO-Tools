"""Site tree schemas for API."""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class SiteTreeGenerateRequest(BaseModel):
    """Request to generate a new site tree."""

    project_id: Optional[int] = Field(None, description="Associated project ID")
    name: str = Field(..., min_length=1, max_length=255, description="Tree name")
    keyword: str = Field(..., min_length=1, description="Primary keyword/topic")
    theme: Optional[str] = Field(None, description="Business theme or niche")
    depth: int = Field(3, ge=1, le=5, description="Maximum tree depth (1-5)")
    max_nodes_per_level: int = Field(
        7, ge=3, le=15, description="Maximum children per node (3-15)"
    )
    language: str = Field("en", description="Content language (en, fr, etc.)")
    business_type: Optional[str] = Field(
        None, description="Business type (ecommerce, blog, saas, etc.)"
    )
    llm_provider: str = Field("openai", description="LLM provider to use")

    class Config:
        json_schema_extra = {
            "example": {
                "project_id": 1,
                "name": "Main Site Architecture",
                "keyword": "sustainable fashion",
                "theme": "eco-friendly clothing",
                "depth": 3,
                "max_nodes_per_level": 7,
                "language": "en",
                "business_type": "ecommerce",
                "llm_provider": "openai",
            }
        }


class SiteTreeNode(BaseModel):
    """Individual node in site tree."""

    name: str
    slug: str
    keyword: Optional[str] = None
    title: Optional[str] = None
    meta_description: Optional[str] = None
    priority: str = "medium"
    level: int = 0
    target_word_count: Optional[int] = None
    url: Optional[str] = None
    children: List["SiteTreeNode"] = []

    class Config:
        from_attributes = True


# Enable forward references
SiteTreeNode.model_rebuild()


class SiteTreeResponse(BaseModel):
    """Response containing site tree data."""

    id: int
    project_id: Optional[int]
    name: str
    description: Optional[str]
    keyword: Optional[str]
    theme: Optional[str]
    depth: int
    tree_json: Dict[str, Any]  # Hierarchical tree structure
    llm_provider: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class SiteTreeListResponse(BaseModel):
    """List of site trees."""

    trees: List[SiteTreeResponse]
    total: int


class SiteTreeExportRequest(BaseModel):
    """Request to export site tree."""

    format: str = Field(
        ...,
        description="Export format (json, csv, xml, mermaid, html, sitemap)",
        pattern="^(json|csv|xml|mermaid|html|sitemap)$",
    )
    base_url: Optional[str] = Field(
        None, description="Base URL for sitemap export (required for sitemap format)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "format": "json",
                "base_url": "https://example.com",
            }
        }


class SiteTreeUpdateRequest(BaseModel):
    """Request to update site tree."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    tree_json: Optional[Dict[str, Any]] = None

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Updated Site Architecture",
                "description": "Revised structure for Q2 2024",
                "tree_json": {
                    "name": "Homepage",
                    "slug": "/",
                    "children": [],
                },
            }
        }
