"""User repository implementation."""

from __future__ import annotations

from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import User
from src.database.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    """Repository handling CRUD operations and queries for User entity."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(User, session)

    async def get_by_email(self, email: str) -> Optional[User]:
        """Fetch a user record by email address."""
        result = await self.session.execute(
            select(User).where(User.email == email)
        )
        return result.scalars().first()

