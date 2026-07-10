"""Processing run repository implementation."""

from __future__ import annotations

import uuid
from typing import List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import ProcessingRun
from src.database.repositories.base import BaseRepository


class ProcessingRunRepository(BaseRepository[ProcessingRun]):
    """Repository handling CRUD operations and queries for ProcessingRun entity."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(ProcessingRun, session)

    async def get_by_ticket_id(self, ticket_id: uuid.UUID) -> List[ProcessingRun]:
        """Fetch all agent execution runs associated with a given ticket."""
        result = await self.session.execute(
            select(ProcessingRun).where(ProcessingRun.ticket_id == ticket_id)
        )
        return list(result.scalars().all())

