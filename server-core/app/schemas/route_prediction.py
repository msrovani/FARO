"""
Route Prediction Schemas for F.A.R.O.
"""
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict


class RoutePredictionRequest(BaseModel):
    """Request for route prediction."""
    model_config = ConfigDict(from_attributes=True)
    
    plate_number: str = Field(..., min_length=1, max_length=20)
    min_observations: int = Field(default=5, ge=3, le=50)


class RoutePredictionResponse(BaseModel):
    """Response for route prediction."""
    model_config = ConfigDict(from_attributes=True)
    
    plate_number: str
    predicted_corridor: List[tuple[float, float]]
    confidence: float = Field(..., ge=0, le=1)
    predicted_hours: List[int]
    predicted_days: List[int]
    last_pattern_analyzed: datetime
    pattern_strength: float


class RoutePredictionForPlateRequest(BaseModel):
    """Request for route predictions for next N days."""
    model_config = ConfigDict(from_attributes=True)
    
    plate_number: str = Field(..., min_length=1, max_length=20)
    days_ahead: int = Field(default=7, ge=1, le=30)


class RoutePredictionForPlateResponse(BaseModel):
    """Response for route predictions for next N days."""
    model_config = ConfigDict(from_attributes=True)
    
    predictions: List[dict]


class PatternDriftAlertResponse(BaseModel):
    """Response for pattern drift alert."""
    model_config = ConfigDict(from_attributes=True)
    
    plate_number: str
    drift_percent: float
    threshold_percent: float
    out_of_corridor_count: int
    total_recent_observations: int
    pattern_analyzed_at: str
    alert_type: str


class RecurringRouteAlertResponse(BaseModel):
    """Response for recurring route alert."""
    model_config = ConfigDict(from_attributes=True)
    
    plate_number: str
    recurrence_score: float
    pattern_strength: float
    primary_corridor: Optional[str]
    predominant_direction: Optional[str]
    observation_count: int
    analyzed_at: str
    alert_type: str
