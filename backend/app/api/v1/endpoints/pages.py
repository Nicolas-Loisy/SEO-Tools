"""Page endpoints."""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.core.database import get_db
from app.models.page import Page
from app.api.v1.schemas.page import PageResponse, PageListResponse

router = APIRouter()


@router.get("/", response_model=PageListResponse)
async def list_pages(
    project_id: Optional[int] = Query(None, description="Filter by project ID"),
    status_code: Optional[int] = Query(None, description="Filter by HTTP status code"),
    min_depth: Optional[int] = Query(None, description="Minimum crawl depth"),
    max_depth: Optional[int] = Query(None, description="Maximum crawl depth"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
):
    """
    List pages with filtering.

    Args:
        project_id: Optional project filter
        status_code: Optional HTTP status filter
        min_depth: Optional minimum depth filter
        max_depth: Optional maximum depth filter
        skip: Pagination offset
        limit: Pagination limit
        db: Database session

    Returns:
        Paginated list of pages with total count
    """
    # Build query
    query = select(Page)

    if project_id:
        query = query.where(Page.project_id == project_id)
    if status_code:
        query = query.where(Page.status_code == status_code)
    if min_depth is not None:
        query = query.where(Page.depth >= min_depth)
    if max_depth is not None:
        query = query.where(Page.depth <= max_depth)

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    # Get paginated results
    query = query.offset(skip).limit(limit).order_by(Page.discovered_at.desc())
    result = await db.execute(query)
    pages = result.scalars().all()

    return PageListResponse(
        items=pages,
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get("/{page_id}", response_model=PageResponse)
async def get_page(
    page_id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    Get page details by ID.

    Args:
        page_id: Page ID
        db: Database session

    Returns:
        Page details
    """
    result = await db.execute(select(Page).where(Page.id == page_id))
    page = result.scalar_one_or_none()

    if not page:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Page {page_id} not found",
        )

    return page
