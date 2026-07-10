"""Pydantic schemas for the retrieval system interfaces."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class RetrievalQuery(BaseModel):
    """Payload representing a client search request."""

    model_config = ConfigDict(from_attributes=True)

    query: str = Field(..., min_length=2, description="Target search query string.")
    limit: int = Field(default=5, ge=1, le=50, description="Max candidates to return.")
    filters: Optional[Dict[str, Any]] = Field(default=None, description="Optional metadata filter parameters.")


class RetrievalResult(BaseModel):
    """Schema representing a retrieved context chunk."""

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(..., description="Unique candidate segment chunk identifier.")
    content: str = Field(..., description="Text segment contents.")
    score: float = Field(..., description="Calculated similarity or rank score.")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadata dictionary.")


class PipelinePerformanceMetrics(BaseModel):
    """Schema representing evaluation metrics score details."""

    model_config = ConfigDict(from_attributes=True)

    precision_at_k: float = Field(..., description="Precision score at specified threshold.")
    recall_at_k: float = Field(..., description="Recall score at specified threshold.")
    mrr: float = Field(..., description="Mean Reciprocal Rank score.")
    ndcg_at_k: float = Field(..., description="Normalized Discounted Cumulative Gain score.")
    latency_ms: float = Field(..., description="Retrieval runtime latency.")
