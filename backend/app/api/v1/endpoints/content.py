"""Content generation endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, Field
from typing import List, Dict, Any

from app.core.database import get_db
from app.models.page import Page
from app.models.tenant import Tenant
from app.core.deps import get_current_tenant
from app.services.content_generation import ContentGenerationService
from app.core.config import settings

router = APIRouter()


class MetaDescriptionRequest(BaseModel):
    """Request to generate meta description."""

    page_id: int = Field(..., description="Page ID")
    max_length: int = Field(160, ge=50, le=320, description="Maximum length")
    provider: str = Field("openai", description="LLM provider")
    model: str = Field(None, description="Specific model (optional)")


class MetaDescriptionResponse(BaseModel):
    """Meta description generation response."""

    page_id: int
    generated_description: str
    original_description: str = None
    length: int


class TitleSuggestionsRequest(BaseModel):
    """Request to generate title suggestions."""

    page_id: int = Field(..., description="Page ID")
    count: int = Field(3, ge=1, le=10, description="Number of suggestions")
    max_length: int = Field(60, ge=30, le=100, description="Maximum length")
    provider: str = Field("openai", description="LLM provider")
    model: str = Field(None, description="Specific model (optional)")


class TitleSuggestionsResponse(BaseModel):
    """Title suggestions response."""

    page_id: int
    suggestions: List[str]
    original_title: str = None


class ContentRecommendationsRequest(BaseModel):
    """Request for content recommendations."""

    page_id: int = Field(..., description="Page ID")
    provider: str = Field("openai", description="LLM provider")
    model: str = Field(None, description="Specific model (optional)")


class ContentRecommendationsResponse(BaseModel):
    """Content recommendations response."""

    page_id: int
    recommendations: Dict[str, Any]


@router.post("/meta-description", response_model=MetaDescriptionResponse)
async def generate_meta_description(
    request: MetaDescriptionRequest,
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    """
    Generate SEO-optimized meta description for a page.

    Uses LLM to create a compelling meta description based on page content.
    """
    # Get page
    result = await db.execute(select(Page).where(Page.id == request.page_id))
    page = result.scalar_one_or_none()

    if not page:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Page {request.page_id} not found",
        )

    # Check if page belongs to tenant's project
    # TODO: Add proper authorization check

    # Get API key based on provider
    api_key = _get_api_key(request.provider)

    # Generate description
    service = ContentGenerationService(
        provider=request.provider,
        api_key=api_key,
        model=request.model,
    )

    generated_description = await service.generate_meta_description(
        page=page,
        max_length=request.max_length,
        language=page.lang or "en",
    )

    return MetaDescriptionResponse(
        page_id=page.id,
        generated_description=generated_description,
        original_description=page.meta_description,
        length=len(generated_description),
    )


@router.post("/title-suggestions", response_model=TitleSuggestionsResponse)
async def generate_title_suggestions(
    request: TitleSuggestionsRequest,
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    """
    Generate SEO-optimized title tag suggestions.

    Uses LLM to create multiple title options based on page content.
    """
    # Get page
    result = await db.execute(select(Page).where(Page.id == request.page_id))
    page = result.scalar_one_or_none()

    if not page:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Page {request.page_id} not found",
        )

    # Get API key
    api_key = _get_api_key(request.provider)

    # Generate suggestions
    service = ContentGenerationService(
        provider=request.provider,
        api_key=api_key,
        model=request.model,
    )

    suggestions = await service.generate_title_suggestions(
        page=page,
        count=request.count,
        max_length=request.max_length,
        language=page.lang or "en",
    )

    return TitleSuggestionsResponse(
        page_id=page.id,
        suggestions=suggestions,
        original_title=page.title,
    )


@router.post("/recommendations", response_model=ContentRecommendationsResponse)
async def generate_recommendations(
    request: ContentRecommendationsRequest,
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    """
    Generate comprehensive content improvement recommendations.

    Analyzes page content and provides SEO optimization suggestions.
    """
    # Get page
    result = await db.execute(select(Page).where(Page.id == request.page_id))
    page = result.scalar_one_or_none()

    if not page:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Page {request.page_id} not found",
        )

    # Get API key
    api_key = _get_api_key(request.provider)

    # Generate recommendations
    service = ContentGenerationService(
        provider=request.provider,
        api_key=api_key,
        model=request.model,
    )

    recommendations = await service.generate_content_recommendations(
        page=page,
        language=page.lang or "en",
    )

    return ContentRecommendationsResponse(
        page_id=page.id,
        recommendations=recommendations,
    )


@router.get("/providers")
async def list_providers(tenant: Tenant = Depends(get_current_tenant)):
    """
    List available LLM providers and their models.

    Returns information about supported providers and models.
    """
    from app.services.llm import LLMFactory

    providers = {}
    for provider_name in LLMFactory.get_available_providers():
        providers[provider_name] = {
            "models": LLMFactory.get_provider_models(provider_name),
            "available": _check_provider_availability(provider_name),
        }

    return {
        "providers": providers,
        "default": "openai",
    }


def _get_api_key(provider: str) -> str:
    """
    Get API key for LLM provider from settings.

    Args:
        provider: Provider name

    Returns:
        API key

    Raises:
        HTTPException: If API key not configured
    """
    if provider == "openai":
        api_key = getattr(settings, "OPENAI_API_KEY", None)
    elif provider == "anthropic":
        api_key = getattr(settings, "ANTHROPIC_API_KEY", None)
    elif provider == "huggingface":
        api_key = getattr(settings, "HUGGINGFACE_API_KEY", None)
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown provider: {provider}",
        )

    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"{provider} API key not configured",
        )

    return api_key


def _check_provider_availability(provider: str) -> bool:
    """Check if provider API key is configured."""
    try:
        _get_api_key(provider)
        return True
    except HTTPException:
        return False
