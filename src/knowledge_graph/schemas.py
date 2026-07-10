"""Pydantic schemas for the Knowledge Graph entity and relationship definitions."""

from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


class GraphNodeSchema(BaseModel):
    """Schema representing an extracted node."""

    model_config = ConfigDict(from_attributes=True)

    name: str = Field(..., description="Node name or unique identifier.")
    type: Literal["Document", "Chunk", "Entity", "Policy", "Department", "Person", "Product", "Process"] = Field(
        ..., description="Allowed label type."
    )
    properties: Dict[str, Any] = Field(default_factory=dict, description="Arbitrary properties.")
    confidence: float = Field(..., description="Extraction confidence score.")
    extraction_source: str = Field(..., description="Source of extraction.")
    extraction_timestamp: str = Field(..., description="Timestamp of extraction.")


class GraphRelationshipSchema(BaseModel):
    """Schema representing an extracted relationship."""

    model_config = ConfigDict(from_attributes=True)

    source_node: str = Field(..., description="Source node name.")
    source_type: str = Field(..., description="Source node type.")
    target_node: str = Field(..., description="Target node name.")
    target_type: str = Field(..., description="Target node type.")
    type: Literal["MENTIONS", "BELONGS_TO", "RELATED_TO", "REFERENCES", "DERIVED_FROM", "VERSION_OF"] = Field(
        ..., description="Allowed relationship type."
    )
    confidence: float = Field(..., description="Extraction confidence score.")
    extraction_source: str = Field(..., description="Source of extraction.")
    extraction_timestamp: str = Field(..., description="Timestamp of extraction.")


class ExtractedGraphSchema(BaseModel):
    """Schema wrapping nodes and relationships extracted from text."""

    model_config = ConfigDict(from_attributes=True)

    nodes: List[GraphNodeSchema] = Field(default_factory=list, description="Extracted nodes.")
    relationships: List[GraphRelationshipSchema] = Field(default_factory=list, description="Extracted relationships.")
