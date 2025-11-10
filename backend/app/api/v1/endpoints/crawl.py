"""Crawl job endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.models.project import Project
from app.models.crawl import CrawlJob
from app.api.v1.schemas.crawl import CrawlJobCreate, CrawlJobResponse

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
    crawl_job = CrawlJob(
        project_id=crawl_data.project_id,
        mode=crawl_data.mode,
        config=crawl_data.config or {},
        status="pending",
    )

    db.add(crawl_job)
    await db.commit()
    await db.refresh(crawl_job)

    # Enqueue Celery task
    from app.workers.crawler_tasks import crawl_site

    task = crawl_site.delay(crawl_job.id)
    crawl_job.celery_task_id = task.id
    await db.commit()

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
