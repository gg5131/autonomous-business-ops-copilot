"""Generic Async Base Repository implementation using SQLAlchemy 2.0."""

from __future__ import annotations

import uuid
from typing import Any, Generic, List, Optional, Type, TypeVar

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import Base

ModelT = TypeVar("ModelT", bound=Base)


class BaseRepository(Generic[ModelT]):
    """Generic async repository providing basic CRUD operations."""

    def __init__(self, model_cls: Type[ModelT], session: AsyncSession) -> None:
        self.model_cls = model_cls
        self.session = session

    async def get_by_id(self, entity_id: uuid.UUID) -> Optional[ModelT]:
        """Fetch a single record by primary key UUID using session identity map lookup."""
        return await self.session.get(self.model_cls, entity_id)


    async def get_all(self, limit: int = 100, offset: int = 0) -> List[ModelT]:
        """Fetch all records with support for limit and offset."""
        result = await self.session.execute(
            select(self.model_cls).offset(offset).limit(limit)
        )
        return list(result.scalars().all())

    async def create(self, entity: ModelT) -> ModelT:
        """Add a new entity to the database session."""
        self.session.add(entity)
        await self.session.flush()
        return entity

    async def update(self, entity: ModelT) -> ModelT:
        """Merge an updated entity state into database session."""
        merged = await self.session.merge(entity)
        await self.session.flush()
        return merged

    async def delete(self, entity: ModelT) -> None:
        """Delete an entity from the database session."""
        await self.session.delete(entity)
        await self.session.flush()
