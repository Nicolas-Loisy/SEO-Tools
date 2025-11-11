"""Search endpoints for full-text search."""

from fastapi import APIRouter, Query, Depends
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.services.meilisearch_service import meilisearch_service
from app.core.database import get_db
from app.models.page import Page

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


@router.get("/stats")
async def get_search_stats():
    """
    Get Meilisearch index statistics.

    Returns:
        Statistics about the search index including document count
    """
    return meilisearch_service.get_stats()


@router.post("/reindex")
async def reindex_all_pages(db: AsyncSession = Depends(get_db)):
    """
    Reindex all pages from the database to Meilisearch.

    This endpoint is useful when you need to rebuild the search index
    from scratch or after database changes.

    Returns:
        Status of the reindexing operation
    """
    try:
        # Get all pages from database
        result = await db.execute(select(Page))
        pages = result.scalars().all()

        if not pages:
            return {
                "success": True,
                "message": "No pages found in database",
                "indexed_count": 0,
            }

        # Format pages for Meilisearch
        documents = []
        for page in pages:
            documents.append({
                "id": page.id,
                "project_id": page.project_id,
                "crawl_job_id": page.crawl_job_id,
                "url": page.url,
                "title": page.title or "",
                "meta_description": page.meta_description or "",
                "h1": page.h1 or "",
                "text_content": page.text_content or "",
                "status_code": page.status_code,
                "word_count": page.word_count,
                "seo_score": page.seo_score,
                "depth": page.depth,
                "internal_links_count": page.internal_links_count,
                "external_links_count": page.external_links_count,
            })

        # Index in batches of 1000
        batch_size = 1000
        indexed_count = 0

        for i in range(0, len(documents), batch_size):
            batch = documents[i:i + batch_size]
            meilisearch_service.index_pages_bulk(batch)
            indexed_count += len(batch)

        return {
            "success": True,
            "message": f"Successfully reindexed {indexed_count} pages",
            "indexed_count": indexed_count,
        }

    except Exception as e:
        return {
            "success": False,
            "message": f"Error during reindexing: {str(e)}",
            "indexed_count": 0,
        }
