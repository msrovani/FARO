"""
F.A.R.O. Watchlist Schemas - cadastro independente e monitoramento.
"""
from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.db.base import WatchlistCategory, WatchlistStatus


class WatchlistEntryBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    status: WatchlistStatus = WatchlistStatus.ACTIVE
    category: WatchlistCategory
    plate_number: Optional[str] = Field(None, max_length=20)
    plate_partial: Optional[str] = Field(None, max_length=20)
    vehicle_make: Optional[str] = Field(None, max_length=100)
    vehicle_model: Optional[str] = Field(None, max_length=100)
    vehicle_color: Optional[str] = Field(None, max_length=50)
    visual_traits: Optional[str] = None
    interest_reason: str = Field(..., min_length=5, max_length=4000)
    information_source: Optional[str] = Field(None, max_length=255)
    sensitivity_level: str = Field(default="reserved", max_length=50)
    confidence_level: Optional[str] = Field(None, max_length=50)
    geographic_scope: Optional[str] = Field(None, max_length=255)
    active_time_window: Optional[str] = Field(None, max_length=255)
    priority: int = Field(default=50, ge=1, le=100)
    recommended_action: Optional[str] = Field(None, max_length=255)
    requires_approach: bool = False
    approach_guidance: Optional[str] = None
    silent_mode: bool = False
    notes: Optional[str] = None
    valid_from: Optional[datetime] = None
    valid_until: Optional[datetime] = None
    review_due_at: Optional[datetime] = None
    metadata_json: Optional[Dict[str, Any]] = None

    @field_validator("plate_number")
    @classmethod
    def normalize_plate_number(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        return value.upper().replace(" ", "").replace("-", "").strip()

    @field_validator("plate_partial")
    @classmethod
    def normalize_plate_partial(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        return value.upper().replace(" ", "").strip()


class WatchlistEntryCreate(WatchlistEntryBase):
    pass


class WatchlistEntryUpdate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    status: Optional[WatchlistStatus] = None
    category: Optional[WatchlistCategory] = None
    plate_number: Optional[str] = None
    plate_partial: Optional[str] = None
    vehicle_make: Optional[str] = None
    vehicle_model: Optional[str] = None
    vehicle_color: Optional[str] = None
    visual_traits: Optional[str] = None
    interest_reason: Optional[str] = None
    information_source: Optional[str] = None
    sensitivity_level: Optional[str] = None
    confidence_level: Optional[str] = None
    geographic_scope: Optional[str] = None
    active_time_window: Optional[str] = None
    priority: Optional[int] = Field(None, ge=1, le=100)
    recommended_action: Optional[str] = None
    requires_approach: Optional[bool] = None
    approach_guidance: Optional[str] = None
    silent_mode: Optional[bool] = None
    notes: Optional[str] = None
    valid_from: Optional[datetime] = None
    valid_until: Optional[datetime] = None
    review_due_at: Optional[datetime] = None
    metadata_json: Optional[Dict[str, Any]] = None


class WatchlistEntryResponse(WatchlistEntryBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    created_by: UUID
    created_by_name: Optional[str] = None
    created_at: datetime
    updated_at: datetime
