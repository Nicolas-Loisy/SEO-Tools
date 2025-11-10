"""API Key repository."""

from typing import Optional, List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.api_key import APIKey
from app.repositories.base import BaseRepository


class APIKeyRepository(BaseRepository[APIKey]):
    """Repository for APIKey model."""

    def __init__(self, db: AsyncSession):
        """Initialize with APIKey model."""
        super().__init__(APIKey, db)

    async def get_by_hash(self, key_hash: str) -> Optional[APIKey]:
        """
        Get API key by hash.

        Args:
            key_hash: SHA256 hash of key

        Returns:
            API key or None
        """
        result = await self.db.execute(select(APIKey).where(APIKey.key_hash == key_hash))
        return result.scalar_one_or_none()

    async def get_by_tenant(
        self, tenant_id: int, active_only: bool = True
    ) -> List[APIKey]:
        """
        Get all API keys for a tenant.

        Args:
            tenant_id: Tenant ID
            active_only: Only return active keys

        Returns:
            List of API keys
        """
        query = select(APIKey).where(APIKey.tenant_id == tenant_id)

        if active_only:
            query = query.where(APIKey.is_active == True)

        result = await self.db.execute(query.order_by(APIKey.created_at.desc()))
        return list(result.scalars().all())

    async def deactivate(self, key_id: int) -> bool:
        """
        Deactivate an API key.

        Args:
            key_id: API key ID

        Returns:
            True if deactivated
        """
        key = await self.get_by_id(key_id)
        if key:
            key.is_active = False
            await self.update(key)
            return True
        return False
