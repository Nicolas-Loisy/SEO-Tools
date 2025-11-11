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


@router.get("/projects/{project_id}/link-recommendations")
async def get_link_recommendations_for_project(
    project_id: int,
    page_id: int = None,
    limit: int = 20,
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    Get internal link recommendations for a page or entire project.

    Uses keyword extraction and content similarity to suggest where to add internal links.

    Args:
        project_id: Project ID
        page_id: Optional page ID to get recommendations for (if None, returns for all pages)
        limit: Maximum number of recommendations
        tenant: Current tenant
        db: Database session

    Returns:
        Link recommendations
    """
    from app.services.link_recommender import link_recommender
    from sqlalchemy import select
    from app.models.page import Page

    # Verify project belongs to tenant
    project_repo = ProjectRepository(db)
    project = await project_repo.get_by_id(project_id)

    if not project or project.tenant_id != tenant.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    # Get sync session for the recommender
    from app.core.database import SessionLocal
    sync_db = SessionLocal()

    try:
        if page_id:
            # Get recommendations for specific page
            recommendations = link_recommender.get_recommendations(
                sync_db,
                page_id,
                project_id,
                max_suggestions=limit
            )

            return {
                "page_id": page_id,
                "project_id": project_id,
                "recommendations": [
                    {
                        "target_page_id": rec.target_page_id,
                        "target_url": rec.target_url,
                        "target_title": rec.target_title,
                        "keyword": rec.keyword,
                        "context": rec.context,
                        "score": rec.score,
                        "reason": rec.reason
                    }
                    for rec in recommendations
                ],
                "count": len(recommendations)
            }
        else:
            # Get recommendations for all pages (limited)
            # Get first 10 pages and generate recommendations
            result = await db.execute(
                select(Page).filter(Page.project_id == project_id).limit(10)
            )
            pages = result.scalars().all()

            all_recommendations = []
            for page in pages:
                recs = link_recommender.get_recommendations(
                    sync_db,
                    page.id,
                    project_id,
                    max_suggestions=5
                )
                for rec in recs[:3]:  # Top 3 per page
                    all_recommendations.append({
                        "source_page_id": rec.source_page_id,
                        "source_url": rec.source_url,
                        "target_page_id": rec.target_page_id,
                        "target_url": rec.target_url,
                        "target_title": rec.target_title,
                        "keyword": rec.keyword,
                        "context": rec.context,
                        "score": rec.score,
                        "reason": rec.reason
                    })

            # Sort by score
            all_recommendations.sort(key=lambda x: x['score'], reverse=True)

            return {
                "project_id": project_id,
                "recommendations": all_recommendations[:limit],
                "count": len(all_recommendations[:limit])
            }
    finally:
        sync_db.close()


@router.get("/projects/{project_id}/link-graph")
async def get_link_graph_analysis(
    project_id: int,
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    Get link graph analysis and statistics.

    Returns PageRank, hub pages, authority pages, and orphan pages.

    Args:
        project_id: Project ID
        tenant: Current tenant
        db: Database session

    Returns:
        Graph statistics and analysis
    """
    from app.services.link_graph import link_graph_service
    from app.core.database import SessionLocal

    # Verify project belongs to tenant
    project_repo = ProjectRepository(db)
    project = await project_repo.get_by_id(project_id)

    if not project or project.tenant_id != tenant.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    # Get sync session for the graph service
    sync_db = SessionLocal()

    try:
        stats = link_graph_service.get_graph_stats(sync_db, project_id)

        return {
            "project_id": project_id,
            "total_pages": stats.total_pages,
            "total_links": stats.total_links,
            "avg_links_per_page": round(stats.avg_links_per_page, 2),
            "orphan_pages": stats.orphan_pages,
            "hub_pages": [
                {
                    "page_id": node.page_id,
                    "url": node.url,
                    "title": node.title,
                    "seo_score": node.seo_score,
                    "pagerank": round(node.pagerank, 4),
                    "in_degree": node.in_degree,
                    "out_degree": node.out_degree
                }
                for node in stats.hub_pages
            ],
            "authority_pages": [
                {
                    "page_id": node.page_id,
                    "url": node.url,
                    "title": node.title,
                    "seo_score": node.seo_score,
                    "pagerank": round(node.pagerank, 4),
                    "in_degree": node.in_degree,
                    "out_degree": node.out_degree
                }
                for node in stats.authority_pages
            ]
        }
    finally:
        sync_db.close()


@router.get("/projects/{project_id}/link-graph/export")
async def export_link_graph_visualization(
    project_id: int,
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    Export link graph data for visualization (D3.js/Cytoscape format).

    Args:
        project_id: Project ID
        tenant: Current tenant
        db: Database session

    Returns:
        Graph data (nodes and edges)
    """
    from app.services.link_graph import link_graph_service
    from app.core.database import SessionLocal

    # Verify project belongs to tenant
    project_repo = ProjectRepository(db)
    project = await project_repo.get_by_id(project_id)

    if not project or project.tenant_id != tenant.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    # Get sync session
    sync_db = SessionLocal()

    try:
        graph_data = link_graph_service.export_graph_for_visualization(
            sync_db,
            project_id
        )

        return {
            "project_id": project_id,
            "graph": graph_data
        }
    finally:
        sync_db.close()
