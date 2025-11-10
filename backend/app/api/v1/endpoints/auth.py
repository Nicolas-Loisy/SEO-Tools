"""Authentication endpoints."""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_tenant
from app.core.security import generate_api_key, hash_api_key, get_key_prefix
from app.models.tenant import Tenant
from app.models.api_key import APIKey
from app.repositories.api_key import APIKeyRepository
from app.api.v1.schemas.auth import (
    APIKeyCreate,
    APIKeyResponse,
    APIKeyCreateResponse,
    TenantResponse,
)

router = APIRouter()


@router.post("/keys", response_model=APIKeyCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_api_key(
    key_data: APIKeyCreate,
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new API key.

    ⚠️ The API key will only be shown once! Save it securely.

    Args:
        key_data: API key configuration
        tenant: Current tenant (from authentication)
        db: Database session

    Returns:
        Created API key with actual key value
    """
    # Generate new API key
    raw_key = generate_api_key()
    key_hash = hash_api_key(raw_key)
    key_prefix = get_key_prefix(raw_key)

    # Create key object
    api_key = APIKey(
        tenant_id=tenant.id,
        key_hash=key_hash,
        key_prefix=key_prefix,
        name=key_data.name,
        description=key_data.description,
        scopes=key_data.scopes,
        expires_at=key_data.expires_at,
    )

    repo = APIKeyRepository(db)
    api_key = await repo.create(api_key)

    return APIKeyCreateResponse(
        key=raw_key,
        key_info=APIKeyResponse.model_validate(api_key),
    )


@router.get("/keys", response_model=List[APIKeyResponse])
async def list_api_keys(
    active_only: bool = True,
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    """
    List API keys for current tenant.

    Args:
        active_only: Only return active keys
        tenant: Current tenant (from authentication)
        db: Database session

    Returns:
        List of API keys (without actual key values)
    """
    repo = APIKeyRepository(db)
    keys = await repo.get_by_tenant(tenant.id, active_only=active_only)
    return keys


@router.get("/keys/{key_id}", response_model=APIKeyResponse)
async def get_api_key(
    key_id: int,
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    """
    Get API key details.

    Args:
        key_id: API key ID
        tenant: Current tenant (from authentication)
        db: Database session

    Returns:
        API key details (without actual key value)
    """
    repo = APIKeyRepository(db)
    key = await repo.get_by_id(key_id)

    if not key or key.tenant_id != tenant.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found",
        )

    return key


@router.delete("/keys/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def deactivate_api_key(
    key_id: int,
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    """
    Deactivate an API key.

    Args:
        key_id: API key ID
        tenant: Current tenant (from authentication)
        db: Database session
    """
    repo = APIKeyRepository(db)
    key = await repo.get_by_id(key_id)

    if not key or key.tenant_id != tenant.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found",
        )

    await repo.deactivate(key_id)


@router.get("/me", response_model=TenantResponse)
async def get_current_tenant_info(
    tenant: Tenant = Depends(get_current_tenant),
):
    """
    Get current tenant information.

    Args:
        tenant: Current tenant (from authentication)

    Returns:
        Tenant details
    """
    return tenant
