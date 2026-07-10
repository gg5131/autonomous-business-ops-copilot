"""Tickets Router handling customer ticket ingestion and security scanning."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from starlette import status

from src.api.exceptions import SecurityError
from src.api.dependencies import get_security_service, get_ticket_repository, get_audit_service
from src.api.schemas.common import APIResponse
from src.api.schemas.ticket import TicketCreate, TicketResponse
from src.database.models import Ticket
from src.database.repositories.ticket import TicketRepository
from src.security.interfaces import ISecurityService, IAuditService
from src.observability.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/tickets", tags=["tickets"])


@router.post("", response_model=APIResponse[TicketResponse], status_code=status.HTTP_201_CREATED)
async def submit_ticket(
    payload: TicketCreate,
    security_service: ISecurityService = Depends(get_security_service),
    ticket_repo: TicketRepository = Depends(get_ticket_repository),
    audit_service: IAuditService = Depends(get_audit_service),
) -> APIResponse[TicketResponse]:
    """Ingest a new customer ticket, scanning for injection and redacting PII."""
    logger.info("Received ticket submission request", customer_id=payload.customer_id)

    # 1. Prompt Injection check
    if security_service.detect_prompt_injection(payload.description) or security_service.detect_prompt_injection(payload.title):
        await audit_service.log_event(
            event_type="PROMPT_INJECTION_BLOCKED",
            event_data={"customer_id": payload.customer_id, "title": payload.title},
        )
        raise SecurityError("Prompt injection payload detected in input.")

    # 2. PII Detection and masking
    clean_title = security_service.sanitize_input(payload.title)
    clean_desc = security_service.sanitize_input(payload.description)

    # Check for PII presence (log security event)
    has_pii = False
    # Using dynamic helper methods of the concrete SecurityService class safely
    # by checking hasattr or casting
    if hasattr(security_service, "has_pii") and security_service.has_pii(clean_desc):  # type: ignore
        has_pii = True
        clean_desc = security_service.mask_pii(clean_desc)  # type: ignore

    if hasattr(security_service, "has_pii") and security_service.has_pii(clean_title):  # type: ignore
        has_pii = True
        clean_title = security_service.mask_pii(clean_title)  # type: ignore

    if has_pii:
        logger.info("PII leakage detected; input masked", customer_id=payload.customer_id)
        await audit_service.log_event(
            event_type="PII_MASKED",
            event_data={"customer_id": payload.customer_id},
        )

    # 3. Persistence
    db_ticket = Ticket(
        title=clean_title,
        description=clean_desc,
        customer_id=payload.customer_id,
        category=payload.category,
        priority=payload.priority,
        metadata_json=payload.metadata_json,
    )

    created_ticket = await ticket_repo.create(db_ticket)

    # Log successful ingestion audit log
    await audit_service.log_event(
        event_type="TICKET_INGESTED",
        event_data={"ticket_id": str(created_ticket.id), "customer_id": created_ticket.customer_id},
    )

    return APIResponse(data=TicketResponse.model_validate(created_ticket))

