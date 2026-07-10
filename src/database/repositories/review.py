"""Review decision repository implementation."""

from __future__ import annotations

import uuid
from typing import List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import ReviewDecision
from src.database.repositories.base import BaseRepository


class ReviewRepository(BaseRepository[ReviewDecision]):
    """Repository handling CRUD operations and queries for ReviewDecision entity."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(ReviewDecision, session)

    async def get_by_draft_id(self, draft_id: uuid.UUID) -> List[ReviewDecision]:
        """Fetch review decisions associated with a draft response."""
        result = await self.session.execute(
            select(ReviewDecision).where(ReviewDecision.draft_id == draft_id)
        )
        return list(result.scalars().all())

