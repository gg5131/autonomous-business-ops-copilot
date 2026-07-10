"""Standard JSON response wrappers and pagination schemas."""

from __future__ import annotations

from typing import Generic, TypeVar

from pydantic import BaseModel, Field

DataT = TypeVar("DataT")


class APIErrorDetails(BaseModel):
    """Pydantic model representing error sub-fields."""

    type: str = Field(..., description="Exception class or category type.")
    message: str = Field(..., description="Detail explanation of what failed.")
    details: dict = Field(default_factory=dict, description="Diagnostic payload fields.")


class APIResponse(BaseModel, Generic[DataT]):
    """Standard envelope wrapping all successful JSON endpoints."""

    success: bool = Field(default=True, description="Indicating call execution status.")
    data: DataT = Field(..., description="The main response payload data structure.")
    error: APIErrorDetails | None = Field(default=None, description="Detailed error object if success is False.")


class ErrorResponse(BaseModel):
    """Standard envelope wrapping all failed API endpoint responses."""

    success: bool = Field(default=False, description="Indicating call execution status.")
    data: None = Field(default=None, description="Empty payload data.")
    error: APIErrorDetails = Field(..., description="Details explaining failure.")
