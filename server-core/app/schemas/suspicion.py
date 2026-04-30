"""
F.A.R.O. Suspicion Schemas - Structured suspicion reporting
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict

from app.db.base import SuspicionLevel, SuspicionReason, UrgencyLevel


class SuspicionReportBase(BaseModel):
    """Base suspicion report data."""

    model_config = ConfigDict(from_attributes=True)

    reason: SuspicionReason
    level: SuspicionLevel
    urgency: UrgencyLevel
    notes: Optional[str] = Field(None, max_length=1000)

    # --- Campos de Abordagem (Field Approach) ---
    abordado: Optional[bool] = Field(
        None, description="Whether the vehicle was approached"
    )
    nivel_abordagem: Optional[int] = Field(
        None, ge=1, le=10, description="Suspicion level during approach (1-10)"
    )
    ocorrencia_registrada: Optional[bool] = Field(
        None, description="Whether an occurrence was registered"
    )
    texto_ocorrencia: Optional[str] = Field(
        None, max_length=2000, description="Details of the registered occurrence"
    )
    # -------------------------------------------


class SuspicionReportCreate(SuspicionReportBase):
    """Schema for creating a suspicion report."""

    observation_client_id: str = Field(
        ..., max_length=255
    )  # Client-generated observation ID
    image_base64: Optional[str] = None  # Optional evidence image
    audio_base64: Optional[str] = None  # Optional audio note
    audio_duration_seconds: Optional[int] = Field(None, ge=0, le=300)  # Max 5 minutes


class SuspicionReportResponse(SuspicionReportBase):
    """Schema for suspicion report response."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    observation_id: UUID
    image_url: Optional[str] = None
    audio_url: Optional[str] = None
    audio_duration_seconds: Optional[int] = None
    system_relevance_score: Optional[float] = None
    created_at: datetime
    updated_at: datetime


class SuspicionFilter(BaseModel):
    """Filter for suspicion reports."""

    model_config = ConfigDict(from_attributes=True)

    reason: Optional[SuspicionReason] = None
    level: Optional[SuspicionLevel] = None
    urgency: Optional[UrgencyLevel] = None
    has_review: Optional[bool] = None
    # Filter by approach fields
    abordado: Optional[bool] = None
    ocorrencia_registrada: Optional[bool] = None
