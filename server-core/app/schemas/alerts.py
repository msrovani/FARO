"""
Alert Schemas for F.A.R.O.
"""
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict


class AlertResponse(BaseModel):
    """Response for a single alert."""
    model_config = ConfigDict(from_attributes=True)
    
    alert_type: str
    plate_number: str
    severity: str
    confidence: float = Field(..., ge=0, le=1)
    details: dict
    triggered_at: str
    requires_review: bool


class AggregatedAlertsRequest(BaseModel):
    """Request for aggregated alerts."""
    model_config = ConfigDict(from_attributes=True)
    
    alert_type: Optional[str] = None
    severity: Optional[str] = None
    limit: int = Field(default=100, ge=10, le=500)


class AggregatedAlertsResponse(BaseModel):
    """Response for aggregated alerts."""
    model_config = ConfigDict(from_attributes=True)
    
    total_alerts: int
    alerts: List[AlertResponse]
    summary: dict


class ObservationAlertCheckRequest(BaseModel):
    """Request to check alerts for an observation."""
    model_config = ConfigDict(from_attributes=True)
    
    observation_id: UUID
    plate_number: str
    location: tuple[float, float]  # (latitude, longitude)
    observed_at: datetime


class ObservationAlertCheckResponse(BaseModel):
    """Response for observation alert check."""
    model_config = ConfigDict(from_attributes=True)
    
    alerts: List[AlertResponse]
