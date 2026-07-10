"""Open Knowledge Format validation schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class OKFLineage(BaseModel):
    """Lineage metadata representing source document provenance."""

    model_config = ConfigDict(from_attributes=True)

    author: Optional[str] = Field(default=None, description="Author / Owner name.")
    date: Optional[datetime] = Field(default=None, description="Creation / Update date.")
    source: str = Field(..., description="Original file path or URL location.")
    department: str = Field(default="general", description="Owner department category.")
    language: str = Field(default="en", description="ISO language classification.")


class OKFMetadata(BaseModel):
    """General metadata properties including lineage and relationships."""

    model_config = ConfigDict(from_attributes=True)

    title: str = Field(..., description="Knowledge document title.")
    doc_type: str = Field(..., description="Type (e.g. policy, procedure, entities, metrics).")
    tags: List[str] = Field(default_factory=list, description="Taxonomy classification tags.")
    lineage: OKFLineage = Field(..., description="Document lineage.")
    relations: List[Dict[str, Any]] = Field(
        default_factory=list, description="Explicit entity/document relationships."
    )
    confidence: float = Field(default=100.0, description="Extraction confidence score.")


class OKFBundle(BaseModel):
    """Unified parsed representation of an OKF Markdown file."""

    model_config = ConfigDict(from_attributes=True)

    metadata: OKFMetadata = Field(..., description="Document frontmatter parameters.")
    content: str = Field(..., description="Markdown body contents.")
    sha256_hash: str = Field(..., description="SHA-256 checksum of content body.")
