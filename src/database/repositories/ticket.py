"""Ticket repository implementation."""

from __future__ import annotations

from typing import List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import Ticket
from src.database.repositories.base import BaseRepository


class TicketRepository(BaseRepository[Ticket]):
    """Repository handling CRUD operations and queries for Ticket entity."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Ticket, session)

    async def get_by_customer(self, customer_id: str) -> List[Ticket]:
        """Retrieve all tickets belonging to a specific customer."""
        result = await self.session.execute(
            select(Ticket).where(Ticket.customer_id == customer_id)
        )
        return list(result.scalars().all())

    async def get_by_status(self, status: str) -> List[Ticket]:
        """Retrieve all tickets filterable by status."""
        result = await self.session.execute(
            select(Ticket).where(Ticket.status == status)
        )
        return list(result.scalars().all())

