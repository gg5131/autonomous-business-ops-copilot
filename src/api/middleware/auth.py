"""FastAPI dependency checks for user authentication utilizing IAuthenticationProvider."""

from __future__ import annotations

from fastapi import Depends
from fastapi.security import APIKeyHeader
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.exceptions import AuthenticationError
from src.api.dependencies import get_auth_provider, get_db
from src.database.models import User
from src.security.interfaces import IAuthenticationProvider

# Check for Authorization header (can be standard API Key format for simplicity)
api_key_header = APIKeyHeader(name="Authorization", auto_error=False)


async def get_current_user(
    token: str | None = Depends(api_key_header),
    auth_provider: IAuthenticationProvider = Depends(get_auth_provider),
    db: AsyncSession = Depends(get_db),
) -> User:
    """FastAPI security dependency extracting and validating the authorization token."""
    if not token:
        raise AuthenticationError("Authorization header is missing.")

    # Scrub potential bearer prefix if supplied by client
    cleaned_token = token
    if token.lower().startswith("bearer "):
        cleaned_token = token[7:].strip()

    user = await auth_provider.authenticate(cleaned_token, db)
    if not user:
        raise AuthenticationError("Invalid or expired authentication token.")

    return user

