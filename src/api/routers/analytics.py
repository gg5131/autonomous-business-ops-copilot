"""Analytics Router handles query statistics and dashboard data."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from src.api.dependencies import (
    get_current_user,
    get_ticket_repository,
    get_processing_run_repository,
)
from src.api.schemas.common import APIResponse
from src.api.schemas.analytics import AnalyticsOverview
from src.database.models import User
from src.database.repositories.ticket import TicketRepository
from src.database.repositories.processing import ProcessingRunRepository
from src.observability.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("", response_model=APIResponse[AnalyticsOverview])
async def get_analytics_overview(
    current_user: User = Depends(get_current_user),
    ticket_repo: TicketRepository = Depends(get_ticket_repository),
    run_repo: ProcessingRunRepository = Depends(get_processing_run_repository),
) -> APIResponse[AnalyticsOverview]:
    """Retrieve summarized system performance and volumes metrics."""
    logger.info("Fetching system analytics overview", requester_id=str(current_user.id))

    # Fetch counts from repositories (basic count calculation)
    tickets = await ticket_repo.get_all(limit=1000)
    runs = await run_repo.get_all(limit=1000)

    total_tickets = len(tickets)
    processed_runs = len(runs)
    open_tickets = len([t for t in tickets if t.status == "open"])

    # Aggregate latency and confidence
    avg_latency = 0.0
    if processed_runs > 0:
        avg_latency = sum(r.total_latency_ms for r in runs) / processed_runs

    # Mock savings estimation (e.g. $10 saved per ticket compared to manual support)
    cost_saved = total_tickets * 10.0

    overview = AnalyticsOverview(
        total_tickets=total_tickets,
        open_tickets=open_tickets,
        processed_tickets=processed_runs,
        avg_latency_ms=avg_latency,
        avg_confidence=88.5,  # Default base confidence placeholder
        cost_saved_usd=cost_saved,
    )

    return APIResponse(data=overview)
