"""
Agent Movement Analysis Schemas - Response models for agent movement patterns
"""
from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import UUID

from pydantic import BaseModel, Field


class AgentMovementPoint(BaseModel):
    """Single point in agent movement trajectory."""
    latitude: float
    longitude: float
    recorded_at: datetime
    battery_level: Optional[float] = None
    connectivity_status: Optional[str] = None


class PatrolArea(BaseModel):
    """Area where agent frequently patrols."""
    centroid_latitude: float
    centroid_longitude: float
    radius_meters: float
    observation_count: int
    unique_hours: int
    coverage_percentage: float
    first_seen: datetime
    last_seen: datetime


class AgentMovementSummary(BaseModel):
    """Summary of agent movement patterns."""
    agent_id: UUID
    agent_name: str
    total_locations: int
    total_distance_km: float
    average_speed_kmh: Optional[float] = None
    patrol_areas: List[PatrolArea] = []
    battery_stats: Dict[str, Any] = {}
    connectivity_stats: Dict[str, Any] = {}
    analysis_period_days: int


class MovementAnomaly(BaseModel):
    """Detected anomaly in agent movement."""
    anomaly_type: str
    location_latitude: float
    location_longitude: float
    recorded_at: datetime
    description: str
    severity: str


class AgentMovementAnalysisResult(BaseModel):
    """Complete result of agent movement analysis."""
    summaries: List[AgentMovementSummary] = []
    total_agents: int
    total_locations_analyzed: int
    analysis_period_days: int
    anomalies: List[MovementAnomaly] = []


class CoverageMapCell(BaseModel):
    """Single cell in coverage map grid."""
    latitude: float
    longitude: float
    location_count: int
    cell_geometry: str


class AgentMovementAnalysisRequest(BaseModel):
    """Request parameters for agent movement analysis."""
    agent_id: Optional[UUID] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    cluster_radius_meters: float = Field(default=500, ge=100, le=5000)
    min_points_per_cluster: int = Field(default=5, ge=3, le=50)


class CoverageMapRequest(BaseModel):
    """Request parameters for coverage map generation."""
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    grid_size_meters: float = Field(default=100, ge=50, le=1000)


class AgentObservationCorrelation(BaseModel):
    """Correlation between agent locations and observations."""
    agent_id: UUID
    agent_name: str
    total_observations: int
    total_agent_locations: int
    observations_near_agent: int
    correlation_rate: float
    average_distance_to_observations: float
    most_productive_areas: List[Dict[str, Any]] = []
    peak_detection_hours: List[int] = []


class TacticalPositioningRecommendation(BaseModel):
    """Tactical positioning recommendation."""
    recommended_latitude: float
    recommended_longitude: float
    reason: str
    expected_impact: str
    hotspot_proximity_km: float
    coverage_gap_score: float
    priority: str


class CorrelationAnalysisRequest(BaseModel):
    """Request parameters for correlation analysis."""
    agent_id: Optional[UUID] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    proximity_radius_meters: float = Field(default=500, ge=100, le=2000)


class TacticalPositioningRequest(BaseModel):
    """Request parameters for tactical positioning recommendations."""
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
