"""
F.A.R.O. Route Analysis Schemas - Geospatial route patterns
"""
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict

from app.schemas.common import GeolocationPoint


class RoutePoint(BaseModel):
    """Point in a route."""
    model_config = ConfigDict(from_attributes=True)
    
    timestamp: datetime
    location: GeolocationPoint
    heading: Optional[float] = None
    speed: Optional[float] = None


class RouteAnalysisRequest(BaseModel):
    """Request for route analysis."""
    model_config = ConfigDict(from_attributes=True)
    
    plate_number: str
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    min_observations: int = Field(default=3, ge=2)


class RoutePatternResponse(BaseModel):
    """Detected route pattern for a vehicle."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    plate_number: str
    
    # Pattern characteristics
    observation_count: int
    first_observed_at: datetime
    last_observed_at: datetime
    
    # Spatial analysis
    centroid: GeolocationPoint
    bounding_box: List[GeolocationPoint]  # 4 corners
    corridor_points: Optional[List[GeolocationPoint]] = None
    
    # Analysis results
    primary_corridor_name: Optional[str] = None
    predominant_direction: Optional[float] = None  # degrees
    recurrence_score: float = Field(..., ge=0.0, le=1.0)
    pattern_strength: str = Field(..., pattern="^(weak|moderate|strong)$")
    
    # Temporal patterns
    common_hours: List[int] = []  # 0-23
    common_days: List[int] = []  # 0=Monday, 6=Sunday
    
    # Metadata
    analyzed_at: datetime
    analysis_version: str


class RouteTimelineItem(BaseModel):
    """Item in route timeline."""
    model_config = ConfigDict(from_attributes=True)
    
    observation_id: UUID
    timestamp: datetime
    location: GeolocationPoint
    plate_number: str
    agent_name: str
    unit_name: Optional[str] = None
    has_suspicion: bool
    suspicion_level: Optional[str] = None


class RouteTimelineResponse(BaseModel):
    """Timeline of observations for a vehicle."""
    model_config = ConfigDict(from_attributes=True)
    
    plate_number: str
    total_observations: int
    time_span_hours: float
    items: List[RouteTimelineItem]
    
    # Aggregated stats
    unique_agents: int
    unique_units: int
    suspicion_count: int


class RouteRecurrenceAnalysis(BaseModel):
    """Recurrence analysis for a vehicle."""
    model_config = ConfigDict(from_attributes=True)
    
    plate_number: str
    observation_count: int
    
    # Spatial recurrence
    unique_locations: int
    location_clusters: List[Dict[str, Any]]
    most_visited_location: Optional[GeolocationPoint] = None
    most_visited_count: int = 0
    
    # Temporal recurrence
    daily_pattern: Dict[str, int]  # day -> count
    hourly_pattern: Dict[str, int]  # hour -> count
    peak_activity_hour: int
    peak_activity_day: int
    
    # Corridor analysis
    corridors_detected: int
    primary_corridor: Optional[str] = None
    corridor_frequency: Optional[int] = None


class RouteMapData(BaseModel):
    """Map data for route visualization."""
    model_config = ConfigDict(from_attributes=True)
    
    plate_number: str
    observations: List[RoutePoint]
    clusters: List[Dict[str, Any]]
    heatmap_data: List[Dict[str, Any]]
    corridor_lines: List[Dict[str, Any]]
    bounds: Dict[str, Any]  # map bounds


class RouteComparisonRequest(BaseModel):
    """Request to compare routes of multiple vehicles."""
    model_config = ConfigDict(from_attributes=True)
    
    plate_numbers: List[str] = Field(..., min_length=2, max_length=10)
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


class RouteComparisonResponse(BaseModel):
    """Comparison of routes between vehicles."""
    model_config = ConfigDict(from_attributes=True)
    
    plates: List[str]
    spatial_overlap: Optional[float] = None  # 0-1
    temporal_correlation: Optional[float] = None  # 0-1
    common_locations: List[GeolocationPoint] = []
    meeting_points: List[Dict[str, Any]] = []
    
    analysis_summary: str
