"""Crawl job endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.models.project import Project
from app.models.crawl import CrawlJob
from app.models.page import Page
from app.api.v1.schemas.crawl import CrawlJobCreate, CrawlJobResponse
from app.api.v1.schemas.page import PageResponse, PageListResponse

router = APIRouter()


@router.post("/", response_model=CrawlJobResponse, status_code=status.HTTP_201_CREATED)
async def start_crawl(
    crawl_data: CrawlJobCreate,
    db: AsyncSession = Depends(get_db),
):
    """
    Start a new crawl job.

    Args:
        crawl_data: Crawl configuration
        db: Database session

    Returns:
        Created crawl job
    """
    # Verify project exists
    result = await db.execute(select(Project).where(Project.id == crawl_data.project_id))
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {crawl_data.project_id} not found",
        )

    # Create crawl job
    # Convert Pydantic model to dict if needed
    config_dict = {}
    if crawl_data.config:
        if hasattr(crawl_data.config, "model_dump"):
            # Pydantic v2
            config_dict = crawl_data.config.model_dump(exclude_none=True)
        elif hasattr(crawl_data.config, "dict"):
            # Pydantic v1
            config_dict = crawl_data.config.dict(exclude_none=True)
        else:
            config_dict = crawl_data.config

    crawl_job = CrawlJob(
        project_id=crawl_data.project_id,
        mode=crawl_data.mode,
        config=config_dict,
        status="pending",
    )

    db.add(crawl_job)
    await db.commit()
    await db.refresh(crawl_job)

    # Enqueue Celery task
    try:
        from app.workers.crawler_tasks import crawl_site

        print(f"[DEBUG] Sending crawl task for job {crawl_job.id}")
        task = crawl_site.delay(crawl_job.id)
        print(f"[DEBUG] Task sent successfully with ID: {task.id}")

        crawl_job.celery_task_id = task.id
        await db.commit()
    except Exception as e:
        print(f"[ERROR] Failed to enqueue Celery task: {e}")
        import traceback
        traceback.print_exc()
        # Don't fail the request, just log the error
        # The job will stay in "pending" status

    return crawl_job


@router.get("/{job_id}", response_model=CrawlJobResponse)
async def get_crawl_job(
    job_id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    Get crawl job status and details.

    Args:
        job_id: Crawl job ID
        db: Database session

    Returns:
        Crawl job details
    """
    result = await db.execute(select(CrawlJob).where(CrawlJob.id == job_id))
    job = result.scalar_one_or_none()

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Crawl job {job_id} not found",
        )

    return job


@router.get("/project/{project_id}", response_model=list[CrawlJobResponse])
async def list_project_crawl_jobs(
    project_id: int,
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
):
    """
    List crawl jobs for a project.

    Args:
        project_id: Project ID
        skip: Number of records to skip
        limit: Maximum records to return
        db: Database session

    Returns:
        List of crawl jobs
    """
    result = await db.execute(
        select(CrawlJob)
        .where(CrawlJob.project_id == project_id)
        .offset(skip)
        .limit(limit)
        .order_by(CrawlJob.created_at.desc())
    )
    jobs = result.scalars().all()
    return jobs


@router.get("/{job_id}/pages", response_model=PageListResponse)
async def get_crawl_pages(
    job_id: int,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
):
    """
    Get pages from a crawl job with pagination.

    Args:
        job_id: Crawl job ID
        skip: Number of records to skip (default: 0)
        limit: Maximum number of records to return (default: 100, max: 500)
        db: Database session

    Returns:
        Paginated list of pages
    """
    # Verify crawl job exists
    result = await db.execute(select(CrawlJob).where(CrawlJob.id == job_id))
    job = result.scalar_one_or_none()

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Crawl job {job_id} not found",
        )

    # Limit max results
    limit = min(limit, 500)

    # Get total count
    from sqlalchemy import func
    count_query = select(func.count(Page.id)).where(Page.crawl_job_id == job_id)
    count_result = await db.execute(count_query)
    total = count_result.scalar() or 0

    # Get pages
    query = (
        select(Page)
        .where(Page.crawl_job_id == job_id)
        .order_by(Page.discovered_at.desc())
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(query)
    pages = result.scalars().all()

    return PageListResponse(
        items=pages,
        total=total,
        skip=skip,
        limit=limit,
    )
