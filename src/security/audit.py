"""Audit log service recording system events asynchronously using Repository pattern."""

from __future__ import annotations

import uuid
from typing import Any, Dict, Optional

from src.database.models import AuditEntry
from src.database.repositories.audit import AuditRepository
from src.observability.logging import get_logger
from src.security.interfaces import IAuditService

logger = get_logger(__name__)


class AuditService(IAuditService):
    """Concrete implementation of IAuditService managing database logs via AuditRepository."""

    def __init__(self, audit_repo: AuditRepository) -> None:
        self._repo = audit_repo

    async def log_event(
        self,
        event_type: str,
        event_data: Dict[str, Any],
        run_id: Optional[uuid.UUID] = None,
        agent_name: Optional[str] = None,
    ) -> None:
        """Create and persist an immutable audit entry in the database."""
        entry = AuditEntry(
            id=uuid.uuid4(),
            run_id=run_id,
            event_type=event_type,
            agent_name=agent_name,
            event_data=event_data,
        )
        try:
            await self._repo.create(entry)
            logger.info(
                "Audit event recorded",
                event_type=event_type,
                run_id=str(run_id) if run_id else None,
                agent_name=agent_name,
            )
        except Exception as e:
            logger.error("Failed to record audit event", error=str(e), event_type=event_type)
            from src.api.exceptions import DatabaseError
            raise DatabaseError("Failed to record audit event in database.", details={"error": str(e)}) from e

