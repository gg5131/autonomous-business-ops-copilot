"""Audit entry repository implementation."""

from __future__ import annotations

import uuid
from typing import List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import AuditEntry
from src.database.repositories.base import BaseRepository


class AuditRepository(BaseRepository[AuditEntry]):
    """Repository handling CRUD operations and queries for AuditEntry entity."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(AuditEntry, session)

    async def get_by_run_id(self, run_id: uuid.UUID) -> List[AuditEntry]:
        """Fetch audit log entries associated with a processing run."""
        result = await self.session.execute(
            select(AuditEntry).where(AuditEntry.run_id == run_id).order_by(AuditEntry.timestamp.asc())
        )
        return list(result.scalars().all())

