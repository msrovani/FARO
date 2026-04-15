"""
F.A.R.O. Common Schemas - Shared Pydantic models
"""
from datetime import datetime
from typing import Any, Dict, Generic, List, Optional, TypeVar
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, ConfigDict


T = TypeVar("T")


class GeolocationPoint(BaseModel):
    """Geographic coordinate point."""
    model_config = ConfigDict(from_attributes=True)
    
    latitude: float = Field(..., ge=-90, le=90, description="Latitude in decimal degrees")
    longitude: float = Field(..., ge=-180, le=180, description="Longitude in decimal degrees")
    accuracy: Optional[float] = Field(None, ge=0, description="Accuracy in meters")


class PaginationParams(BaseModel):
    """Pagination parameters for list endpoints."""
    page: int = Field(default=1, ge=1, description="Page number (1-indexed)")
    page_size: int = Field(default=20, ge=1, le=100, description="Items per page")
    
    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size


class FilterParams(BaseModel):
    """Common filter parameters."""
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    search: Optional[str] = None
    sort_by: Optional[str] = Field(default="created_at")
    sort_order: str = Field(default="desc", pattern="^(asc|desc)$")
    
    @field_validator("end_date")
    @classmethod
    def validate_date_range(cls, v: Optional[datetime], info) -> Optional[datetime]:
        if v and info.data.get("start_date") and v < info.data["start_date"]:
            raise ValueError("end_date must be after start_date")
        return v


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response."""
    model_config = ConfigDict(from_attributes=True)
    
    items: List[T]
    total: int
    page: int
    page_size: int
    pages: int
    has_next: bool
    has_prev: bool
    
    @classmethod
    def create(
        cls,
        items: List[T],
        total: int,
        pagination: PaginationParams,
    ) -> "PaginatedResponse[T]":
        pages = (total + pagination.page_size - 1) // pagination.page_size
        return cls(
            items=items,
            total=total,
            page=pagination.page,
            page_size=pagination.page_size,
            pages=pages,
            has_next=pagination.page < pages,
            has_prev=pagination.page > 1,
        )


class ErrorDetail(BaseModel):
    """Error detail for validation errors."""
    loc: List[str]
    msg: str
    type: str


class ErrorResponse(BaseModel):
    """Standard error response."""
    error: str
    message: str
    details: Optional[List[ErrorDetail]] = None
    code: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    request_id: Optional[str] = None


class SuccessResponse(BaseModel):
    """Standard success response."""
    success: bool = True
    message: str
    data: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class BaseSchema(BaseModel):
    """Base schema with common configuration."""
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        str_strip_whitespace=True,
    )


class TimestampedSchema(BaseSchema):
    """Schema with timestamp fields."""
    id: UUID
    created_at: datetime
    updated_at: datetime
