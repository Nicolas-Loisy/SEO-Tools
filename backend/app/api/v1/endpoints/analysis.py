"""SEO analysis endpoints."""

from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_tenant
from app.models.tenant import Tenant
from app.models.project import Project
from app.repositories.project import ProjectRepository

router = APIRouter()


@router.post("/projects/{project_id}/embeddings", status_code=status.HTTP_202_ACCEPTED)
async def compute_embeddings(
    project_id: int,
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    Compute semantic embeddings for all pages in a project.

    This is an async task that runs in the background.

    Args:
        project_id: Project ID
        tenant: Current tenant
        db: Database session

    Returns:
        Task information
    """
    # Verify project belongs to tenant
    project_repo = ProjectRepository(db)
    project = await project_repo.get_by_id(project_id)

    if not project or project.tenant_id != tenant.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    # Enqueue task
    from app.workers.analysis_tasks import compute_project_embeddings

    task = compute_project_embeddings.delay(project_id)

    return {
        "status": "accepted",
        "message": "Embedding computation started",
        "task_id": task.id,
        "project_id": project_id,
    }


@router.post("/projects/{project_id}/graph", status_code=status.HTTP_202_ACCEPTED)
async def compute_link_graph(
    project_id: int,
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    Compute internal linking graph metrics.

    Args:
        project_id: Project ID
        tenant: Current tenant
        db: Database session

    Returns:
        Task information
    """
    # Verify project belongs to tenant
    project_repo = ProjectRepository(db)
    project = await project_repo.get_by_id(project_id)

    if not project or project.tenant_id != tenant.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    # Enqueue task
    from app.workers.analysis_tasks import compute_internal_linking_graph

    task = compute_internal_linking_graph.delay(project_id)

    return {
        "status": "accepted",
        "message": "Graph computation started",
        "task_id": task.id,
        "project_id": project_id,
    }


@router.post("/projects/{project_id}/recommendations", status_code=status.HTTP_202_ACCEPTED)
async def generate_recommendations(
    project_id: int,
    top_k: int = 5,
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    Generate internal link recommendations based on semantic similarity.

    Requires embeddings to be computed first.

    Args:
        project_id: Project ID
        top_k: Number of recommendations per page
        tenant: Current tenant
        db: Database session

    Returns:
        Task information
    """
    # Verify project belongs to tenant
    project_repo = ProjectRepository(db)
    project = await project_repo.get_by_id(project_id)

    if not project or project.tenant_id != tenant.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    # Enqueue task
    from app.workers.analysis_tasks import generate_link_recommendations

    task = generate_link_recommendations.delay(project_id, top_k)

    return {
        "status": "accepted",
        "message": "Recommendation generation started",
        "task_id": task.id,
        "project_id": project_id,
        "top_k": top_k,
    }


@router.get("/projects/{project_id}/similar-pages/{page_id}")
async def find_similar_pages(
    project_id: int,
    page_id: int,
    limit: int = 10,
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    Find semantically similar pages.

    Requires embeddings to be computed.

    Args:
        project_id: Project ID
        page_id: Source page ID
        limit: Maximum number of results
        tenant: Current tenant
        db: Database session

    Returns:
        List of similar pages
    """
    from app.repositories.page import PageRepository

    # Verify project belongs to tenant
    project_repo = ProjectRepository(db)
    project = await project_repo.get_by_id(project_id)

    if not project or project.tenant_id != tenant.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    # Get source page
    page_repo = PageRepository(db)
    source_page = await page_repo.get_by_id(page_id)

    if not source_page or source_page.project_id != project_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Page not found",
        )

    if source_page.embedding is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Page does not have embeddings computed. Run POST /analysis/projects/{project_id}/embeddings first.",
        )

    # Find similar pages
    similar_pages = await page_repo.find_similar_pages(source_page, limit=limit)

    return {
        "source_page": {
            "id": source_page.id,
            "url": source_page.url,
            "title": source_page.title,
        },
        "similar_pages": [
            {
                "id": page.id,
                "url": page.url,
                "title": page.title,
                "meta_description": page.meta_description,
                # Similarity would be computed here
            }
            for page in similar_pages
        ],
        "count": len(similar_pages),
    }
