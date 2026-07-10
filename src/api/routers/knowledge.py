"""Knowledge Router handles document uploads and OKF metadata storage."""

from __future__ import annotations

from fastapi import APIRouter, Depends, status

from src.api.dependencies import get_current_user
from src.api.schemas.common import APIResponse
from src.database.models import User
from src.observability.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/knowledge", tags=["knowledge"])


@router.get("", response_model=APIResponse[list])
async def list_knowledge_documents(
    current_user: User = Depends(get_current_user),
) -> APIResponse[list]:
    """Retrieve list of registered knowledge documents (OKF format packages)."""
    logger.info("Listing knowledge assets", requester_id=str(current_user.id))
    # Stub listing: will interface with OKF modules in subsequent phases
    return APIResponse(data=[])
