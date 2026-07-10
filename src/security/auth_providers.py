"""Mock Authentication Provider implementation for development and testing environments."""

from __future__ import annotations

import uuid
from typing import Any, Dict, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import User
from src.security.interfaces import IAuthenticationProvider


class MockAuthenticationProvider(IAuthenticationProvider):
    """Dev-only authentication provider that accepts any token starting with 'mock-'."""

    def __init__(self) -> None:
        # Create configuration dict rather than direct instances to avoid detached model errors
        self._mock_users_data: Dict[str, Dict[str, Any]] = {
            "mock-admin-token": {
                "id": uuid.UUID("00000000-0000-0000-0000-000000000001"),
                "email": "admin@copilot.example.com",
                "role": "admin",
                "permissions": ["read", "write", "approve", "configure"],
            },
            "mock-reviewer-token": {
                "id": uuid.UUID("00000000-0000-0000-0000-000000000002"),
                "email": "reviewer@copilot.example.com",
                "role": "reviewer",
                "permissions": ["read", "approve"],
            },
        }

    async def authenticate(self, credentials_token: str, session: AsyncSession) -> Optional[User]:
        """Authenticate user token and ensure user exists in DB to prevent foreign key issues."""
        if not credentials_token:
            return None

        user_data: Optional[Dict[str, Any]] = None

        # 1. Check exact match lookup
        if credentials_token in self._mock_users_data:
            user_data = self._mock_users_data[credentials_token]
        # 2. Check dynamic fallback prefix lookup
        elif credentials_token.startswith("mock-"):
            user_role = "reviewer"
            if "admin" in credentials_token:
                user_role = "admin"

            # Create stable namespace UUID based on email to ensure consistent user IDs
            email_val = f"{credentials_token[5:]}@copilot.example.com"
            user_id = uuid.uuid5(uuid.NAMESPACE_DNS, email_val)

            user_data = {
                "id": user_id,
                "email": email_val,
                "role": user_role,
                "permissions": ["read", "approve"] if user_role == "reviewer" else ["read", "write", "approve"],
            }

        if user_data:
            # Query if user exists in the database
            result = await session.execute(
                select(User).where(User.id == user_data["id"])
            )
            db_user = result.scalars().first()

            if not db_user:
                # User does not exist, insert it
                db_user = User(
                    id=user_data["id"],
                    email=user_data["email"],
                    role=user_data["role"],
                    permissions=user_data["permissions"],
                )
                session.add(db_user)
                await session.flush()

            return db_user

        return None

    def generate_token(self, payload: Dict[str, Any]) -> str:
        """Helper generating mock token using the payload contents."""
        username = payload.get("email", "test-user").split("@")[0]
        role = payload.get("role", "reviewer")
        return f"mock-{username}-{role}-token"

