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


# SEO Content Generation Endpoints


class GenerateContentRequest(BaseModel):
    """Request to generate SEO content."""
    keyword: str = Field(..., description="Target keyword")
    page_type: str = Field(..., description="Page type (homepage, article, product, etc.)")
    tone: str = Field("professional", description="Content tone")
    length: int = Field(1000, ge=300, le=5000, description="Target word count")
    language: str = Field("en", description="Content language")
    context: str = Field(None, description="Additional context")
    competitor_urls: List[str] = Field(None, description="Competitor URLs for analysis")
    provider: str = Field("openai", description="LLM provider")


class OptimizeContentRequest(BaseModel):
    """Request to optimize existing content."""
    content: str = Field(..., description="Content to optimize")
    keyword: str = Field(..., description="Target keyword")
    page_type: str = Field(..., description="Page type")
    language: str = Field("en", description="Content language")
    provider: str = Field("openai", description="LLM provider")


class ValidateContentRequest(BaseModel):
    """Request to validate content."""
    content: str = Field(..., description="Content to validate")
    keyword: str = Field(..., description="Target keyword")
    meta_title: str = Field(None, description="Meta title")
    meta_description: str = Field(None, description="Meta description")
    min_words: int = Field(300, description="Minimum word count")
    max_words: int = Field(2500, description="Maximum word count")


@router.post("/generate")
async def generate_seo_content(
    request: GenerateContentRequest,
    tenant: Tenant = Depends(get_current_tenant),
) -> Dict[str, Any]:
    """
    Generate complete SEO-optimized content.

    Creates structured content with proper headings, meta tags,
    and optimized keyword usage based on the specified page type.

    Args:
        request: Content generation request
        tenant: Current tenant

    Returns:
        Generated content with structure and metadata
    """
    from app.services.seo_content_generator import seo_content_generator

    print(f"[API generate-content] Request for keyword '{request.keyword}', type={request.page_type}")

    try:
        content = await seo_content_generator.generate_content(
            keyword=request.keyword,
            page_type=request.page_type,
            tone=request.tone,
            length=request.length,
            language=request.language,
            context=request.context,
            competitor_urls=request.competitor_urls or [],
            provider=request.provider
        )

        print(f"[API generate-content] Content generated successfully")

        return content

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        print(f"[API generate-content] Error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate content: {str(e)}"
        )


@router.post("/optimize")
async def optimize_seo_content(
    request: OptimizeContentRequest,
    tenant: Tenant = Depends(get_current_tenant),
) -> Dict[str, Any]:
    """
    Optimize existing content for SEO.

    Analyzes and improves content for better search engine visibility
    while preserving the core message.

    Args:
        request: Content optimization request
        tenant: Current tenant

    Returns:
        Optimized content with improvements and suggestions
    """
    from app.services.seo_content_generator import seo_content_generator

    print(f"[API optimize-content] Request for keyword '{request.keyword}'")

    try:
        result = await seo_content_generator.optimize_content(
            content=request.content,
            keyword=request.keyword,
            page_type=request.page_type,
            language=request.language,
            provider=request.provider
        )

        print(f"[API optimize-content] Content optimized successfully")

        return result

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        print(f"[API optimize-content] Error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to optimize content: {str(e)}"
        )


@router.post("/validate")
async def validate_seo_content(
    request: ValidateContentRequest,
    tenant: Tenant = Depends(get_current_tenant),
) -> Dict[str, Any]:
    """
    Validate content for SEO best practices.

    Checks keyword usage, readability, structure, and provides
    an SEO score with actionable suggestions.

    Args:
        request: Content validation request
        tenant: Current tenant

    Returns:
        Validation result with score and suggestions
    """
    from app.services.content_validator import content_validator

    print(f"[API validate-content] Request for keyword '{request.keyword}'")

    try:
        result = content_validator.validate_content(
            content=request.content,
            keyword=request.keyword,
            meta_title=request.meta_title,
            meta_description=request.meta_description,
            min_words=request.min_words,
            max_words=request.max_words
        )

        return {
            "score": result.score,
            "issues": result.issues,
            "suggestions": result.suggestions,
            "metrics": result.metrics
        }

    except Exception as e:
        print(f"[API validate-content] Error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to validate content: {str(e)}"
        )


@router.get("/templates")
async def list_content_templates(
    tenant: Tenant = Depends(get_current_tenant),
) -> Dict[str, Any]:
    """
    List available content templates.

    Returns information about available page types and content tones.

    Args:
        tenant: Current tenant

    Returns:
        Available templates and options
    """
    from app.services.content_templates import content_template_service

    return {
        "page_types": content_template_service.get_available_page_types(),
        "tones": content_template_service.get_available_tones()
    }
