"""Review Router handles supervisor review decisions on response drafts."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from starlette import status

from src.api.exceptions import AuthorizationError
from src.api.dependencies import get_current_user, get_review_repository, get_audit_service
from src.api.schemas.common import APIResponse
from src.api.schemas.review import ReviewDecisionSubmit, ReviewResponse
from src.database.models import ReviewDecision, User
from src.database.repositories.review import ReviewRepository
from src.security.interfaces import IAuditService
from src.observability.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/review", tags=["review"])


@router.post("", response_model=APIResponse[ReviewResponse], status_code=status.HTTP_201_CREATED)
async def submit_review(
    payload: ReviewDecisionSubmit,
    current_user: User = Depends(get_current_user),
    review_repo: ReviewRepository = Depends(get_review_repository),
    audit_service: IAuditService = Depends(get_audit_service),
) -> APIResponse[ReviewResponse]:
    """Submit a supervisor review choice (approve, edit, reject) on a draft response."""
    logger.info("Received review submission", reviewer_id=str(current_user.id), draft_id=str(payload.draft_id))

    # Verify authorization (reviewer or admin role required)
    if current_user.role not in ["reviewer", "admin"]:
        raise AuthorizationError("Only supervisors and admins are permitted to review responses.")

    db_decision = ReviewDecision(
        draft_id=payload.draft_id,
        reviewer_id=current_user.id,
        decision=payload.decision,
        edited_content=payload.edited_content,
        feedback=payload.feedback,
    )

    created_decision = await review_repo.create(db_decision)

    # Log review event in audit logs
    await audit_service.log_event(
        event_type="REVIEW_SUBMITTED",
        event_data={
            "review_id": str(created_decision.id),
            "draft_id": str(created_decision.draft_id),
            "decision": created_decision.decision,
            "reviewer_id": str(created_decision.reviewer_id),
        },
    )

    return APIResponse(data=ReviewResponse.model_validate(created_decision))

