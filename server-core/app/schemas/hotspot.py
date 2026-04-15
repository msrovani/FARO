"""
F.A.R.O. Hotspot Analysis Schemas
"""
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict

from app.schemas.common import GeolocationPoint


class HotspotPointResponse(BaseModel):
    """Hotspot point in analysis result."""
    model_config = ConfigDict(from_attributes=True)
    
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    observation_count: int = Field(..., ge=0)
    suspicion_count: int = Field(..., ge=0)
    unique_plates: int = Field(..., ge=0)
    radius_meters: float = Field(..., ge=0)
    intensity_score: float = Field(..., ge=0, le=1)


class HotspotAnalysisRequest(BaseModel):
    """Request for hotspot analysis."""
    model_config = ConfigDict(from_attributes=True)
    
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    cluster_radius_meters: float = Field(default=500, ge=100, le=2000)
    min_points_per_cluster: int = Field(default=5, ge=3, le=20)


class HotspotAnalysisResponse(BaseModel):
    """Response for hotspot analysis."""
    model_config = ConfigDict(from_attributes=True)
    
    hotspots: List[HotspotPointResponse]
    total_observations: int
    total_suspicions: int
    analysis_period_days: int
    cluster_radius_meters: float
    min_points_per_cluster: int


class HotspotTimelineRequest(BaseModel):
    """Request for hotspot timeline analysis."""
    model_config = ConfigDict(from_attributes=True)
    
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    radius_meters: float = Field(default=500, ge=100, le=2000)
    days: int = Field(default=7, ge=1, le=90)


class HotspotTimelineResponse(BaseModel):
    """Response for hotspot timeline."""
    model_config = ConfigDict(from_attributes=True)
    
    hourly_data: List[Dict[str, Any]]
    daily_pattern: List[int]  # 24 hours
    total_observations: int
    peak_hour: Optional[int]


class HotspotPlatesRequest(BaseModel):
    """Request for hotspot plates analysis."""
    model_config = ConfigDict(from_attributes=True)
    
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    radius_meters: float = Field(default=500, ge=100, le=2000)
    limit: int = Field(default=50, ge=10, le=200)


class HotspotPlateEntry(BaseModel):
    """Entry in hotspot plates list."""
    model_config = ConfigDict(from_attributes=True)
    
    plate_number: str
    observation_count: int
    last_seen: Optional[str]
    first_seen: Optional[str]


class HotspotPlatesResponse(BaseModel):
    """Response for hotspot plates."""
    model_config = ConfigDict(from_attributes=True)
    
    plates: List[HotspotPlateEntry]
