"""Review Decision request and response validation schemas."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field



class ReviewDecisionSubmit(BaseModel):
    """Payload to record a supervisor review choice on a draft response."""

    draft_id: uuid.UUID = Field(..., description="Target response draft ID.")
    decision: Literal["approved", "edited", "rejected"] = Field(..., description="Human choice outcome.")
    edited_content: Optional[str] = Field(default=None, description="Corrected text if decision was 'edited'.")
    feedback: Optional[str] = Field(default=None, description="Explanatory notes or audit comments.")


class ReviewResponse(BaseModel):
    """Standard representation of review log data."""

    id: uuid.UUID = Field(..., description="Decision record identifier.")
    draft_id: uuid.UUID = Field(..., description="Target response draft ID.")
    reviewer_id: uuid.UUID = Field(..., description="Reviewer supervisor account ID.")
    decision: str = Field(..., description="Human choice outcome.")
    edited_content: Optional[str] = Field(default=None, description="Corrected response draft content.")
    feedback: Optional[str] = Field(default=None, description="Explanatory notes.")
    decided_at: datetime = Field(..., description="Timestamps of review choice.")

    model_config = ConfigDict(from_attributes=True)

