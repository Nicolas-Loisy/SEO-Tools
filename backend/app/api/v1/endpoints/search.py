"""Search endpoints for full-text search."""

from fastapi import APIRouter, Query
from typing import Optional
from app.services.meilisearch_service import meilisearch_service

router = APIRouter()


@router.get("/")
async def search_pages(
    q: str = Query(..., min_length=1, description="Search query"),
    project_id: Optional[int] = Query(None, description="Filter by project ID"),
    status_code: Optional[int] = Query(None, description="Filter by status code"),
    min_seo_score: Optional[float] = Query(None, ge=0, le=100, description="Minimum SEO score"),
    max_seo_score: Optional[float] = Query(None, ge=0, le=100, description="Maximum SEO score"),
    min_word_count: Optional[int] = Query(None, ge=0, description="Minimum word count"),
    limit: int = Query(20, ge=1, le=100, description="Number of results"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
):
    """
    Search pages using full-text search.

    Args:
        q: Search query
        project_id: Filter by project ID
        status_code: Filter by HTTP status code
        min_seo_score: Minimum SEO score filter
        max_seo_score: Maximum SEO score filter
        min_word_count: Minimum word count filter
        limit: Number of results to return (1-100)
        offset: Pagination offset

    Returns:
        Search results with highlighted matches
    """
    # Build filters
    filters = {}
    if status_code is not None:
        filters["status_code"] = status_code
    if min_seo_score is not None:
        filters["min_seo_score"] = min_seo_score
    if max_seo_score is not None:
        filters["max_seo_score"] = max_seo_score
    if min_word_count is not None:
        filters["min_word_count"] = min_word_count

    # Execute search
    results = meilisearch_service.search(
        query=q,
        project_id=project_id,
        filters=filters,
        limit=limit,
        offset=offset,
    )

    return {
        "query": q,
        "hits": results.get("hits", []),
        "total": results.get("estimatedTotalHits", 0),
        "limit": limit,
        "offset": offset,
        "processing_time_ms": results.get("processingTimeMs", 0),
    }
