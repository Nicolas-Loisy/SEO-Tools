"""Base repository with common CRUD operations."""

from typing import Generic, Type, TypeVar, Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.core.database import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """
    Base repository implementing common CRUD operations.

    Generic repository that can be subclassed for specific models.
    """

    def __init__(self, model: Type[ModelType], db: AsyncSession):
        """
        Initialize repository.

        Args:
            model: SQLAlchemy model class
            db: Database session
        """
        self.model = model
        self.db = db

    async def create(self, obj: ModelType) -> ModelType:
        """
        Create a new object.

        Args:
            obj: Object to create

        Returns:
            Created object with ID
        """
        self.db.add(obj)
        await self.db.flush()
        await self.db.refresh(obj)
        return obj

    async def get_by_id(self, id: int) -> Optional[ModelType]:
        """
        Get object by ID.

        Args:
            id: Object ID

        Returns:
            Object or None if not found
        """
        result = await self.db.execute(select(self.model).where(self.model.id == id))
        return result.scalar_one_or_none()

    async def get_all(self, skip: int = 0, limit: int = 100) -> List[ModelType]:
        """
        Get all objects with pagination.

        Args:
            skip: Number of records to skip
            limit: Maximum number of records

        Returns:
            List of objects
        """
        result = await self.db.execute(select(self.model).offset(skip).limit(limit))
        return list(result.scalars().all())

    async def count(self) -> int:
        """
        Count total objects.

        Returns:
            Total count
        """
        result = await self.db.execute(select(func.count()).select_from(self.model))
        return result.scalar()

    async def update(self, obj: ModelType) -> ModelType:
        """
        Update an object.

        Args:
            obj: Object to update

        Returns:
            Updated object
        """
        await self.db.flush()
        await self.db.refresh(obj)
        return obj

    async def delete(self, obj: ModelType) -> None:
        """
        Delete an object.

        Args:
            obj: Object to delete
        """
        await self.db.delete(obj)
        await self.db.flush()

    async def delete_by_id(self, id: int) -> bool:
        """
        Delete object by ID.

        Args:
            id: Object ID

        Returns:
            True if deleted, False if not found
        """
        obj = await self.get_by_id(id)
        if obj:
            await self.delete(obj)
            return True
        return False
