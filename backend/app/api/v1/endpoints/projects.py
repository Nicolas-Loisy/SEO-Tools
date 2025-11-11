"""Project management endpoints."""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.models.project import Project
from app.models.tenant import Tenant
from app.api.v1.schemas.project import ProjectCreate, ProjectUpdate, ProjectResponse

router = APIRouter()


@router.post("/", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    project_data: ProjectCreate,
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new project.

    Args:
        project_data: Project creation data
        db: Database session

    Returns:
        Created project
    """
    # For MVP, create default tenant if not exists
    # In production, get tenant_id from authenticated user
    result = await db.execute(select(Tenant).where(Tenant.slug == "default"))
    tenant = result.scalar_one_or_none()

    if not tenant:
        tenant = Tenant(
            name="Default Tenant",
            slug="default",
            plan="free",
        )
        db.add(tenant)
        await db.flush()

    # Convert Pydantic model to dict and convert HttpUrl objects to strings
    project_dict = project_data.model_dump()

    # Convert HttpUrl objects to strings (Pydantic v2 returns Url objects)
    if project_dict.get('domain'):
        project_dict['domain'] = str(project_dict['domain'])
    if project_dict.get('sitemap_url'):
        project_dict['sitemap_url'] = str(project_dict['sitemap_url'])
    if project_dict.get('robots_txt_url'):
        project_dict['robots_txt_url'] = str(project_dict['robots_txt_url'])

    # Create project
    project = Project(
        tenant_id=tenant.id,
        **project_dict,
    )
    db.add(project)
    await db.commit()
    await db.refresh(project)

    return project


@router.get("/", response_model=List[ProjectResponse])
async def list_projects(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
):
    """
    List all projects.

    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        db: Database session

    Returns:
        List of projects
    """
    result = await db.execute(
        select(Project)
        .offset(skip)
        .limit(limit)
        .order_by(Project.created_at.desc())
    )
    projects = result.scalars().all()
    return projects


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    Get project by ID.

    Args:
        project_id: Project ID
        db: Database session

    Returns:
        Project details
    """
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {project_id} not found",
        )

    return project


@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: int,
    project_data: ProjectUpdate,
    db: AsyncSession = Depends(get_db),
):
    """
    Update project.

    Args:
        project_id: Project ID
        project_data: Update data
        db: Database session

    Returns:
        Updated project
    """
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {project_id} not found",
        )

    # Convert to dict and handle HttpUrl objects
    update_dict = project_data.model_dump(exclude_unset=True)

    # Convert HttpUrl objects to strings (Pydantic v2 returns Url objects)
    if 'domain' in update_dict and update_dict['domain']:
        update_dict['domain'] = str(update_dict['domain'])
    if 'sitemap_url' in update_dict and update_dict['sitemap_url']:
        update_dict['sitemap_url'] = str(update_dict['sitemap_url'])
    if 'robots_txt_url' in update_dict and update_dict['robots_txt_url']:
        update_dict['robots_txt_url'] = str(update_dict['robots_txt_url'])

    # Update fields
    for field, value in update_dict.items():
        setattr(project, field, value)

    await db.commit()
    await db.refresh(project)

    return project


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    Delete project.

    Args:
        project_id: Project ID
        db: Database session
    """
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {project_id} not found",
        )

    await db.delete(project)
    await db.commit()
