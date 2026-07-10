"""Pluggable service and provider interfaces for Auth, PII, Injection detection, and Audit Logging."""

from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import User



class IAuthenticationProvider(ABC):
    """Interface for pluggable authentication providers."""

    @abstractmethod
    async def authenticate(self, credentials_token: str, session: AsyncSession) -> Optional[User]:
        """Authenticate user credentials token and return the User entity if valid."""


    @abstractmethod
    def generate_token(self, payload: Dict[str, Any]) -> str:
        """Helper to generate JWT or token representation for authentication testing/use."""


class IPIIDetector(ABC):
    """Interface for PII (personally identifiable information) detection and redaction."""

    @abstractmethod
    def detect_pii(self, text: str) -> bool:
        """Return True if any PII elements are detected in text."""

    @abstractmethod
    def redact_pii(self, text: str) -> str:
        """Redact sensitive PII elements in text, replacing them with masks (e.g. [EMAIL])."""


class ISecurityService(ABC):
    """Abstract interface defining the complete suite of security utilities."""

    @abstractmethod
    def sanitize_input(self, text: str) -> str:
        """Remove unsafe scripts or content from raw user text input."""

    @abstractmethod
    def detect_prompt_injection(self, text: str) -> bool:
        """Identify potential prompt injection payloads or jailbreak instructions."""


class IAuditService(ABC):
    """Interface for immutable audit trail logging."""

    @abstractmethod
    async def log_event(
        self,
        event_type: str,
        event_data: Dict[str, Any],
        run_id: Optional[uuid.UUID] = None,
        agent_name: Optional[str] = None,
    ) -> None:
        """Record an operation or agent execution state in database audit logs."""
