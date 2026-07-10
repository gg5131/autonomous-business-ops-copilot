"""Analytics metrics response schemas."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class AnalyticsOverview(BaseModel):
    """Aggregate statistics for business dashboard visualization."""

    total_tickets: int = Field(..., description="Total tickets received.")
    open_tickets: int = Field(..., description="Currently unresolved ticket count.")
    processed_tickets: int = Field(..., description="Total runs executed to draft response.")
    avg_latency_ms: float = Field(..., description="Average processing runtime duration in ms.")
    avg_confidence: float = Field(..., description="Average overall confidence score of drafts.")
    cost_saved_usd: float = Field(..., description="Estimated cost savings against manual processing.")

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

