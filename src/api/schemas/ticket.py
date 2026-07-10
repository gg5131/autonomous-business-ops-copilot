"""Ticket API request and response validation schemas."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, ConfigDict, Field


class TicketCreate(BaseModel):

    """Payload to submit a new ticket for processing."""

    title: str = Field(..., min_length=3, max_length=255, description="Title of the ticket.")
    description: str = Field(..., min_length=10, description="Detailed problem description.")
    customer_id: str = Field(..., min_length=1, max_length=100, description="Unique customer ID.")
    category: str = Field(default="general", max_length=100, description="Assigned category type.")
    priority: str = Field(default="medium", max_length=50, description="Priority level classification.")
    metadata_json: Optional[Dict[str, Any]] = Field(default=None, description="Optional diagnostic attributes.")


class TicketResponse(BaseModel):
    """Standard representation of ticket data returned to API callers."""

    id: uuid.UUID = Field(..., description="Unique generated UUID identifier.")
    title: str = Field(..., description="Title of the ticket.")
    description: str = Field(..., description="Detailed problem description.")
    customer_id: str = Field(..., description="Unique customer ID.")
    category: str = Field(..., description="Assigned category type.")
    priority: str = Field(..., description="Priority level classification.")
    status: str = Field(..., description="Current status flag of ticket.")
    created_at: datetime = Field(..., description="Ticket ingestion timestamp.")
    metadata_json: Optional[Dict[str, Any]] = Field(default=None, description="Optional diagnostic attributes.")

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

