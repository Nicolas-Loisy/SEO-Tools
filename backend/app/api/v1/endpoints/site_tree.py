"""Site tree generation and management API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
import os

from app.core.database import get_db
from app.core.deps import get_current_tenant
from app.models.tenant import Tenant
from app.models.content import SiteTree
from app.api.v1.schemas.site_tree import (
    SiteTreeGenerateRequest,
    SiteTreeResponse,
    SiteTreeListResponse,
    SiteTreeUpdateRequest,
    SiteTreeExportRequest,
)
from app.services.site_tree_generator import SiteTreeGenerator
from app.services.site_tree_exporter import SiteTreeExporter

router = APIRouter()


@router.post("/generate", response_model=SiteTreeResponse, status_code=201)
async def generate_site_tree(
    request: SiteTreeGenerateRequest,
    db: AsyncSession = Depends(get_db),
    tenant: Tenant = Depends(get_current_tenant),
):
    """
    Generate a new site architecture tree using LLM.

    Generates a hierarchical site structure based on:
    - Primary keyword
    - Business theme/niche
    - Target depth
    - SEO best practices

    Returns complete tree with:
    - Page titles and slugs
    - URL structure
    - Meta descriptions
    - Content briefs
    """
    # Get LLM API key from environment
    provider = request.llm_provider.lower()
    api_key = None

    if provider == "openai":
        api_key = os.getenv("OPENAI_API_KEY")
    elif provider == "anthropic":
        api_key = os.getenv("ANTHROPIC_API_KEY")
    elif provider == "huggingface":
        api_key = os.getenv("HUGGINGFACE_API_KEY")

    if not api_key:
        raise HTTPException(
            status_code=400,
            detail=f"LLM provider '{provider}' is not configured. Please set API key in environment.",
        )

    # Initialize generator
    generator = SiteTreeGenerator(
        provider=provider,
        api_key=api_key,
    )

    # Generate tree
    try:
        tree_data = await generator.generate_tree(
            keyword=request.keyword,
            theme=request.theme,
            depth=request.depth,
            max_nodes_per_level=request.max_nodes_per_level,
            language=request.language,
            business_type=request.business_type,
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to generate site tree: {str(e)}"
        )

    # Save to database
    site_tree = SiteTree(
        tenant_id=tenant.id,
        project_id=request.project_id,
        name=request.name,
        keyword=request.keyword,
        theme=request.theme,
        depth=request.depth,
        tree_json=tree_data,
        llm_provider=provider,
        generation_prompt=f"Keyword: {request.keyword}, Theme: {request.theme}, Depth: {request.depth}",
    )

    db.add(site_tree)
    await db.commit()
    await db.refresh(site_tree)

    return site_tree


@router.get("/", response_model=SiteTreeListResponse)
async def list_site_trees(
    project_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    tenant: Tenant = Depends(get_current_tenant),
):
    """
    List all site trees for the current tenant.

    Optionally filter by project_id.
    """
    from sqlalchemy import select, func

    query = select(SiteTree).where(SiteTree.tenant_id == tenant.id)

    if project_id is not None:
        query = query.where(SiteTree.project_id == project_id)

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    result = await db.execute(count_query)
    total = result.scalar() or 0

    # Get trees
    query = query.offset(skip).limit(limit).order_by(SiteTree.created_at.desc())
    result = await db.execute(query)
    trees = result.scalars().all()

    return SiteTreeListResponse(trees=trees, total=total)


@router.get("/{tree_id}", response_model=SiteTreeResponse)
async def get_site_tree(
    tree_id: int,
    db: AsyncSession = Depends(get_db),
    tenant: Tenant = Depends(get_current_tenant),
):
    """Get a specific site tree by ID."""
    from sqlalchemy import select

    query = select(SiteTree).where(
        SiteTree.id == tree_id, SiteTree.tenant_id == tenant.id
    )
    result = await db.execute(query)
    tree = result.scalar_one_or_none()

    if not tree:
        raise HTTPException(status_code=404, detail="Site tree not found")

    return tree


@router.put("/{tree_id}", response_model=SiteTreeResponse)
async def update_site_tree(
    tree_id: int,
    request: SiteTreeUpdateRequest,
    db: AsyncSession = Depends(get_db),
    tenant: Tenant = Depends(get_current_tenant),
):
    """Update an existing site tree."""
    from sqlalchemy import select

    query = select(SiteTree).where(
        SiteTree.id == tree_id, SiteTree.tenant_id == tenant.id
    )
    result = await db.execute(query)
    tree = result.scalar_one_or_none()

    if not tree:
        raise HTTPException(status_code=404, detail="Site tree not found")

    # Update fields
    if request.name is not None:
        tree.name = request.name
    if request.description is not None:
        tree.description = request.description
    if request.tree_json is not None:
        tree.tree_json = request.tree_json

    await db.commit()
    await db.refresh(tree)

    return tree


@router.delete("/{tree_id}", status_code=204)
async def delete_site_tree(
    tree_id: int,
    db: AsyncSession = Depends(get_db),
    tenant: Tenant = Depends(get_current_tenant),
):
    """Delete a site tree."""
    from sqlalchemy import select, delete

    query = select(SiteTree).where(
        SiteTree.id == tree_id, SiteTree.tenant_id == tenant.id
    )
    result = await db.execute(query)
    tree = result.scalar_one_or_none()

    if not tree:
        raise HTTPException(status_code=404, detail="Site tree not found")

    await db.execute(delete(SiteTree).where(SiteTree.id == tree_id))
    await db.commit()

    return Response(status_code=204)


@router.post("/{tree_id}/export")
async def export_site_tree(
    tree_id: int,
    request: SiteTreeExportRequest,
    db: AsyncSession = Depends(get_db),
    tenant: Tenant = Depends(get_current_tenant),
):
    """
    Export site tree to various formats.

    Supported formats:
    - json: Hierarchical JSON structure
    - csv: Flat CSV with all nodes
    - xml: Hierarchical XML
    - mermaid: Mermaid flowchart diagram code
    - html: HTML nested list with styling
    - sitemap: XML sitemap format (requires base_url)
    """
    from sqlalchemy import select

    query = select(SiteTree).where(
        SiteTree.id == tree_id, SiteTree.tenant_id == tenant.id
    )
    result = await db.execute(query)
    tree = result.scalar_one_or_none()

    if not tree:
        raise HTTPException(status_code=404, detail="Site tree not found")

    # Export to requested format
    exporter = SiteTreeExporter()
    tree_data = tree.tree_json
    format_type = request.format.lower()

    try:
        if format_type == "json":
            content = exporter.to_json(tree_data, pretty=True)
            media_type = "application/json"
            filename = f"site_tree_{tree_id}.json"

        elif format_type == "csv":
            content = exporter.to_csv(tree_data)
            media_type = "text/csv"
            filename = f"site_tree_{tree_id}.csv"

        elif format_type == "xml":
            content = exporter.to_xml(tree_data)
            media_type = "application/xml"
            filename = f"site_tree_{tree_id}.xml"

        elif format_type == "mermaid":
            content = exporter.to_mermaid(tree_data)
            media_type = "text/plain"
            filename = f"site_tree_{tree_id}.mmd"

        elif format_type == "html":
            content = exporter.to_html(tree_data)
            media_type = "text/html"
            filename = f"site_tree_{tree_id}.html"

        elif format_type == "sitemap":
            if not request.base_url:
                raise HTTPException(
                    status_code=400, detail="base_url is required for sitemap export"
                )
            content = exporter.to_sitemap_xml(tree_data, request.base_url)
            media_type = "application/xml"
            filename = f"sitemap_{tree_id}.xml"

        else:
            raise HTTPException(status_code=400, detail=f"Unsupported format: {format_type}")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")

    # Return file as download
    return Response(
        content=content,
        media_type=media_type,
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
        },
    )
