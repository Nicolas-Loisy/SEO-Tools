"""SEO analysis endpoints."""

from typing import Dict, Any, Optional
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
            print(f"[API link-recommendations] Getting recommendations for page {page_id}")

            recommendations = link_recommender.get_recommendations(
                sync_db,
                page_id,
                project_id,
                max_suggestions=limit,
                max_target_pages=500  # Limit target pages to prevent timeout
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
            # Get recommendations for all pages (very limited to prevent timeout)
            print(f"[API link-recommendations] Getting recommendations for all pages (limited)")

            # OPTIMIZATION: Only process top 5 pages by SEO score (was 10)
            result = await db.execute(
                select(Page).filter(
                    Page.project_id == project_id
                ).order_by(
                    Page.seo_score.desc().nullslast()
                ).limit(5)  # Reduced from 10 to 5
            )
            pages = result.scalars().all()

            print(f"[API link-recommendations] Processing {len(pages)} pages")

            all_recommendations = []
            for page in pages:
                # OPTIMIZATION: Reduce max_suggestions and max_target_pages
                recs = link_recommender.get_recommendations(
                    sync_db,
                    page.id,
                    project_id,
                    max_suggestions=3,  # Reduced from 5
                    max_target_pages=200  # Much smaller for "all pages" mode
                )
                for rec in recs[:2]:  # Top 2 per page (was 3)
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

            print(f"[API link-recommendations] Returning {len(all_recommendations[:limit])} recommendations")

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
    max_pages: int = 1000,
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    Get link graph analysis and statistics.

    Returns PageRank, hub pages, authority pages, and orphan pages.

    Args:
        project_id: Project ID
        max_pages: Maximum number of pages to analyze (default 1000, prevents timeout)
        tenant: Current tenant
        db: Database session

    Returns:
        Graph statistics and analysis
    """
    from app.services.link_graph import link_graph_service
    from app.core.database import SessionLocal

    print(f"[API link-graph] Request for project {project_id}, max_pages={max_pages}")

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
        stats = link_graph_service.get_graph_stats(sync_db, project_id, max_pages=max_pages)

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
    max_pages: int = 500,
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    Export link graph data for visualization (D3.js/Cytoscape format).

    Args:
        project_id: Project ID
        max_pages: Maximum pages for visualization (default 500, smaller for performance)
        tenant: Current tenant
        db: Database session

    Returns:
        Graph data (nodes and edges)
    """
    from app.services.link_graph import link_graph_service
    from app.core.database import SessionLocal

    print(f"[API link-graph/export] Request for project {project_id}, max_pages={max_pages}")

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
            project_id,
            max_pages=max_pages
        )

        return {
            "project_id": project_id,
            "graph": graph_data
        }
    finally:
        sync_db.close()


@router.get("/projects/{project_id}/pages/{page_id}/schema/detect")
async def detect_schema_types(
    project_id: int,
    page_id: int,
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    Detect appropriate schema types for a page.

    Analyzes page content and suggests suitable Schema.org types.

    Args:
        project_id: Project ID
        page_id: Page ID
        tenant: Current tenant
        db: Database session

    Returns:
        List of detected schema types with priorities
    """
    from app.repositories.page import PageRepository
    from app.services.schema_detector import schema_detector

    # Verify project belongs to tenant
    project_repo = ProjectRepository(db)
    project = await project_repo.get_by_id(project_id)

    if not project or project.tenant_id != tenant.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    # Get page
    page_repo = PageRepository(db)
    page = await page_repo.get_by_id(page_id)

    if not page or page.project_id != project_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Page not found",
        )

    # Detect schema types
    detected_types = schema_detector.detect_schema_type(
        url=page.url,
        title=page.title or "",
        content=page.text_content or "",
        meta_description=page.meta_description,
        h1=page.h1
    )

    return {
        "page_id": page_id,
        "url": page.url,
        "detected_types": [
            {
                "type": schema_type.value,
                "priority": schema_detector.get_schema_priority(schema_type)
            }
            for schema_type in detected_types
        ]
    }


@router.post("/projects/{project_id}/pages/{page_id}/schema/generate")
async def generate_jsonld_schema(
    project_id: int,
    page_id: int,
    schema_type: str,
    additional_data: Optional[Dict[str, Any]] = None,
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    Generate JSON-LD schema for a page.

    Args:
        project_id: Project ID
        page_id: Page ID
        schema_type: Schema.org type (e.g., "Article", "Product")
        additional_data: Optional additional data for schema generation
        tenant: Current tenant
        db: Database session

    Returns:
        Generated JSON-LD schema
    """
    from app.repositories.page import PageRepository
    from app.services.jsonld_generator import jsonld_generator
    from app.services.schema_detector import SchemaType

    # Verify project belongs to tenant
    project_repo = ProjectRepository(db)
    project = await project_repo.get_by_id(project_id)

    if not project or project.tenant_id != tenant.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    # Get page - use sync session for page data
    from app.core.database import SessionLocal
    sync_db = SessionLocal()

    try:
        # Get page using sync query
        from app.models.page import Page
        page = sync_db.query(Page).filter(
            Page.id == page_id,
            Page.project_id == project_id
        ).first()

        if not page:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Page not found",
            )

        # Validate schema type
        try:
            schema_type_enum = SchemaType(schema_type)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid schema type: {schema_type}",
            )

        # Generate schema
        schema = jsonld_generator.generate_schema(
            page=page,
            schema_type=schema_type_enum,
            additional_data=additional_data
        )

        # Validate schema
        validation_result = jsonld_generator.validate_schema(schema)

        # Format for HTML
        html_output = jsonld_generator.format_for_html(schema)

        return {
            "page_id": page_id,
            "schema_type": schema_type,
            "schema": schema,
            "html": html_output,
            "validation": validation_result
        }
    finally:
        sync_db.close()


@router.post("/projects/{project_id}/pages/{page_id}/schema/validate")
async def validate_jsonld_schema(
    project_id: int,
    page_id: int,
    schema: Dict[str, Any],
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    Validate a JSON-LD schema.

    Args:
        project_id: Project ID
        page_id: Page ID
        schema: JSON-LD schema to validate
        tenant: Current tenant
        db: Database session

    Returns:
        Validation result
    """
    from app.services.jsonld_generator import jsonld_generator

    # Verify project belongs to tenant
    project_repo = ProjectRepository(db)
    project = await project_repo.get_by_id(project_id)

    if not project or project.tenant_id != tenant.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    # Validate schema
    validation_result = jsonld_generator.validate_schema(schema)

    return {
        "page_id": page_id,
        "validation": validation_result
    }


@router.get("/projects/{project_id}/schema/bulk-detect")
async def bulk_detect_schemas(
    project_id: int,
    limit: int = 50,
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    Detect schema types for all pages in a project.

    Args:
        project_id: Project ID
        limit: Maximum number of pages to analyze
        tenant: Current tenant
        db: Database session

    Returns:
        Schema detection results for all pages
    """
    from app.repositories.page import PageRepository
    from app.services.schema_detector import schema_detector
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

    # Get pages
    result = await db.execute(
        select(Page)
        .filter(Page.project_id == project_id)
        .limit(limit)
    )
    pages = result.scalars().all()

    # Detect schemas for each page
    results = []
    for page in pages:
        detected_types = schema_detector.detect_schema_type(
            url=page.url,
            title=page.title or "",
            content=page.text_content or "",
            meta_description=page.meta_description,
            h1=page.h1
        )

        results.append({
            "page_id": page.id,
            "url": page.url,
            "title": page.title,
            "detected_types": [schema_type.value for schema_type in detected_types[:2]]
        })

    return {
        "project_id": project_id,
        "total_pages": len(results),
        "pages": results
    }


@router.post("/projects/{project_id}/pages/{page_id}/schema/enhance")
async def enhance_jsonld_with_ai(
    project_id: int,
    page_id: int,
    schema: Dict[str, Any],
    provider: str = "openai",
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    Enhance a JSON-LD schema using AI/LLM.

    Args:
        project_id: Project ID
        page_id: Page ID
        schema: Base JSON-LD schema to enhance
        provider: LLM provider (openai, anthropic)
        tenant: Current tenant
        db: Database session

    Returns:
        Enhanced JSON-LD schema with improvements and recommendations
    """
    from app.services.schema_enhancer import schema_enhancer

    # Verify project belongs to tenant
    project_repo = ProjectRepository(db)
    project = await project_repo.get_by_id(project_id)

    if not project or project.tenant_id != tenant.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    # Get page - use sync session
    from app.core.database import SessionLocal
    from app.models.page import Page

    sync_db = SessionLocal()

    try:
        # Get page using sync query
        page = sync_db.query(Page).filter(
            Page.id == page_id,
            Page.project_id == project_id
        ).first()

        if not page:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Page not found",
            )

        # Log the input schema structure for debugging
        print(f"[API enhance] Input schema keys: {list(schema.keys())[:10]}")
        print(f"[API enhance] Input has @context: {'@context' in schema}")
        print(f"[API enhance] Input has nested schema: {'schema' in schema and '@context' not in schema}")

        # Enhance schema with AI
        result = await schema_enhancer.enhance_with_suggestions(
            page=page,
            base_schema=schema,
            provider=provider
        )

        # Get the enhanced schema and ensure it's unwrapped
        enhanced = result.get("enhanced_schema", schema)

        # Double-check: unwrap any remaining nested schema keys
        from app.services.schema_enhancer import schema_enhancer as se
        enhanced = se._unwrap_nested_schema(enhanced)

        print(f"[API enhance] Output enhanced_schema keys: {list(enhanced.keys())[:10]}")
        print(f"[API enhance] Output has @context: {'@context' in enhanced}")
        print(f"[API enhance] Output has nested schema: {'schema' in enhanced and '@context' not in enhanced}")

        return {
            "page_id": page_id,
            "enhanced_schema": enhanced,
            "improvements": result.get("improvements", []),
            "recommendations": result.get("recommendations", []),
            "provider": provider
        }

    finally:
        sync_db.close()
