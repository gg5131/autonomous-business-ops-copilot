"""Dependency injection container mapping interfaces to application services and repositories."""

from __future__ import annotations

from typing import AsyncGenerator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from configs.settings import get_settings
from src.database.postgres import get_postgres_session
from src.database.sqlite_fallback import get_sqlite_session
from src.database.repositories.audit import AuditRepository
from src.database.repositories.processing import ProcessingRunRepository
from src.database.repositories.review import ReviewRepository
from src.database.repositories.ticket import TicketRepository
from src.database.repositories.user import UserRepository
from src.security.auth_providers import MockAuthenticationProvider
from src.security.audit import AuditService
from src.security.interfaces import (
    IAuditService,
    IAuthenticationProvider,
    IPIIDetector,
    ISecurityService,
)
from src.security.pii import PIIService
from src.security.pii_detectors import RegexPIIDetector
from src.security.validation import InputSanitizer
from src.security.injection import PromptInjectionDetector

settings = get_settings()


# --- Database Dependency ---
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Yield database session, choosing Postgres for production and SQLite fallback for dev."""
    if settings.is_production:
        async for session in get_postgres_session():
            yield session
    else:
        async for session in get_sqlite_session():
            yield session


# --- Provider Dependencies ---
def get_auth_provider() -> IAuthenticationProvider:
    """Return configured pluggable authentication provider."""
    # Pluggable: returns MockAuthenticationProvider for local dev/testing
    return MockAuthenticationProvider()


def get_pii_detector() -> IPIIDetector:
    """Return configured pluggable PII detector."""
    # Pluggable: returns RegexPIIDetector as default
    return RegexPIIDetector()


# --- Repository Dependencies ---
def get_ticket_repository(db: AsyncSession = Depends(get_db)) -> TicketRepository:
    """Inject TicketRepository."""
    return TicketRepository(db)


def get_user_repository(db: AsyncSession = Depends(get_db)) -> UserRepository:
    """Inject UserRepository."""
    return UserRepository(db)


def get_audit_repository(db: AsyncSession = Depends(get_db)) -> AuditRepository:
    """Inject AuditRepository."""
    return AuditRepository(db)


def get_review_repository(db: AsyncSession = Depends(get_db)) -> ReviewRepository:
    """Inject ReviewRepository."""
    return ReviewRepository(db)


def get_processing_run_repository(db: AsyncSession = Depends(get_db)) -> ProcessingRunRepository:
    """Inject ProcessingRunRepository."""
    return ProcessingRunRepository(db)


# --- Service Dependencies ---
def get_audit_service(audit_repo: AuditRepository = Depends(get_audit_repository)) -> IAuditService:
    """Inject IAuditService interface mapped to concrete database AuditService."""
    return AuditService(audit_repo)


# Concrete implementation of security service for DI injection
class SecurityService(ISecurityService):
    """Concrete ISecurityService coordinating sanitizer, PII masks, and injection filters."""

    def __init__(self, pii_detector: IPIIDetector) -> None:
        self._pii_service = PIIService(pii_detector)
        self._sanitizer = InputSanitizer()
        self._injection = PromptInjectionDetector()

    def sanitize_input(self, text: str) -> str:
        return self._sanitizer.sanitize(text)

    def detect_prompt_injection(self, text: str) -> bool:
        return self._injection.has_injection(text)

    def mask_pii(self, text: str) -> str:
        return self._pii_service.mask_pii(text)

    def has_pii(self, text: str) -> bool:
        return self._pii_service.has_pii(text)


def get_security_service(pii_detector: IPIIDetector = Depends(get_pii_detector)) -> ISecurityService:
    """Inject ISecurityService configuration."""
    return SecurityService(pii_detector)
