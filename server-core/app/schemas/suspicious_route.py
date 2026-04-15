"""
F.A.R.O. Suspicious Route Schemas - Manual route registration for intelligence
"""
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict

from app.schemas.common import GeolocationPoint


class SuspiciousRouteCreate(BaseModel):
    """Request to create a suspicious route."""
    model_config = ConfigDict(from_attributes=True)
    
    name: str = Field(..., min_length=3, max_length=255)
    crime_type: str = Field(..., pattern="^(drug_trafficking|contraband|escape|weapons_trafficking|kidnapping|car_theft|stolen_vehicle|gang_activity|human_trafficking|money_laundering|other)$")
    direction: str = Field(..., pattern="^(inbound|outbound|bidirectional)$")
    risk_level: str = Field(..., pattern="^(low|medium|high|critical)$")
    
    # Spatial geometry (array of [lat, lng] points)
    route_points: List[GeolocationPoint] = Field(..., min_length=2)
    buffer_distance_meters: Optional[float] = Field(None, ge=0, le=5000)
    
    # Active period
    active_from_hour: Optional[int] = Field(None, ge=0, le=23)
    active_to_hour: Optional[int] = Field(None, ge=0, le=23)
    active_days: Optional[List[int]] = Field(None, min_length=1, max_length=7)  # 0=Monday, 6=Sunday
    
    justification: Optional[str] = Field(None, max_length=2000)


class SuspiciousRouteUpdate(BaseModel):
    """Request to update a suspicious route."""
    model_config = ConfigDict(from_attributes=True)
    
    name: Optional[str] = Field(None, min_length=3, max_length=255)
    crime_type: Optional[str] = Field(None, pattern="^(drug_trafficking|contraband|escape|weapons_trafficking|kidnapping|car_theft|stolen_vehicle|gang_activity|human_trafficking|money_laundering|other)$")
    direction: Optional[str] = Field(None, pattern="^(inbound|outbound|bidirectional)$")
    risk_level: Optional[str] = Field(None, pattern="^(low|medium|high|critical)$")
    
    route_points: Optional[List[GeolocationPoint]] = Field(None, min_length=2)
    buffer_distance_meters: Optional[float] = Field(None, ge=0, le=5000)
    
    active_from_hour: Optional[int] = Field(None, ge=0, le=23)
    active_to_hour: Optional[int] = Field(None, ge=0, le=23)
    active_days: Optional[List[int]] = Field(None, min_length=1, max_length=7)
    
    justification: Optional[str] = Field(None, max_length=2000)
    is_active: Optional[bool] = None


class SuspiciousRouteResponse(BaseModel):
    """Response for suspicious route."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    agency_id: UUID
    name: str
    crime_type: str
    direction: str
    risk_level: str
    
    # Spatial geometry
    route_points: List[GeolocationPoint]
    buffer_distance_meters: Optional[float]
    
    # Active period
    active_from_hour: Optional[int]
    active_to_hour: Optional[int]
    active_days: Optional[List[int]]
    
    # Metadata
    justification: Optional[str]
    created_by: UUID
    approved_by: Optional[UUID]
    approval_status: str
    is_active: bool
    
    created_at: datetime
    updated_at: datetime


class SuspiciousRouteMatchRequest(BaseModel):
    """Request to check if observation matches suspicious route."""
    model_config = ConfigDict(from_attributes=True)
    
    observation_id: UUID
    plate_number: str
    location: GeolocationPoint
    observed_at: datetime


class SuspiciousRouteMatchResponse(BaseModel):
    """Response for route match check."""
    model_config = ConfigDict(from_attributes=True)
    
    matches: bool
    matched_routes: List[Dict[str, Any]] = []
    distance_meters: Optional[float] = None
    alert_triggered: bool = False


class SuspiciousRouteListResponse(BaseModel):
    """Response for listing suspicious routes."""
    model_config = ConfigDict(from_attributes=True)
    
    routes: List[SuspiciousRouteResponse]
    total_count: int
    page: int
    page_size: int


class RouteApprovalRequest(BaseModel):
    """Request to approve/reject a suspicious route."""
    model_config = ConfigDict(from_attributes=True)
    
    approval_status: str = Field(..., pattern="^(approved|rejected)$")
    justification: Optional[str] = Field(None, max_length=2000)
