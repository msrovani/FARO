"""
Agent Movement Analysis Service for F.A.R.O.
Spatial analysis of agent location logs to identify movement patterns, patrol coverage, and anomalies.
Uses PostGIS spatial functions with existing GIST indexes.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List, Optional
from uuid import UUID

from geoalchemy2.shape import to_shape
from geoalchemy2.functions import (
    ST_DWithin, ST_Distance, ST_Buffer, ST_Centroid, ST_NumGeometries,
    ST_ClusterDBSCAN, ST_X, ST_Y, ST_MakePoint, ST_SetSRID
)
from sqlalchemy import and_, func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import AgentLocationLog, User, VehicleObservation


@dataclass
class AgentMovementPoint:
    latitude: float
    longitude: float
    recorded_at: datetime
    battery_level: Optional[float]
    connectivity_status: Optional[str]


@dataclass
class PatrolArea:
    centroid_latitude: float
    centroid_longitude: float
    radius_meters: float
    observation_count: int
    unique_hours: int
    coverage_percentage: float
    first_seen: datetime
    last_seen: datetime


@dataclass
class AgentMovementSummary:
    agent_id: UUID
    agent_name: str
    total_locations: int
    total_distance_km: float
    average_speed_kmh: Optional[float]
    patrol_areas: List[PatrolArea]
    battery_stats: dict
    connectivity_stats: dict
    analysis_period_days: int


@dataclass
class MovementAnomaly:
    anomaly_type: str
    location_latitude: float
    location_longitude: float
    recorded_at: datetime
    description: str
    severity: str


@dataclass
class AgentObservationCorrelation:
    agent_id: UUID
    agent_name: str
    total_observations: int
    total_agent_locations: int
    observations_near_agent: int
    correlation_rate: float
    average_distance_to_observations: float
    most_productive_areas: List[dict]
    peak_detection_hours: List[int]


@dataclass
class TacticalPositioningRecommendation:
    recommended_latitude: float
    recommended_longitude: float
    reason: str
    expected_impact: str
    hotspot_proximity_km: float
    coverage_gap_score: float
    priority: str


@dataclass
class AgentMovementAnalysisResult:
    summaries: List[AgentMovementSummary]
    total_agents: int
    total_locations_analyzed: int
    analysis_period_days: int
    anomalies: List[MovementAnomaly]


async def analyze_agent_movement(
    db: AsyncSession,
    agency_id: UUID,
    agent_id: Optional[UUID] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    cluster_radius_meters: float = 500,
    min_points_per_cluster: int = 5,
) -> AgentMovementAnalysisResult:
    """
    Analyze agent movement patterns using spatial clustering on AgentLocationLog.
    Returns patrol areas, movement statistics, and anomalies.
    Optimized to reduce database roundtrips and use PostGIS functions.
    """
    if not start_date:
        start_date = datetime.utcnow() - timedelta(days=7)
    if not end_date:
        end_date = datetime.utcnow()
    
    analysis_period_days = (end_date - start_date).days
    
    # Optimized query: get all data in single query with aggregation
    # Use PostGIS functions directly in SQL for better performance
    base_query = (
        select(
            AgentLocationLog.agent_id,
            User.full_name,
            func.count(AgentLocationLog.id).label('total_locations'),
            func.avg(AgentLocationLog.battery_level).label('avg_battery'),
            func.min(AgentLocationLog.battery_level).label('min_battery'),
            func.max(AgentLocationLog.battery_level).label('max_battery'),
            func.ST_ClusterDBSCAN(
                AgentLocationLog.location,
                eps=cluster_radius_meters,
                minpoints=min_points_per_cluster
            ).label('cluster_id')
        )
        .join(User, User.id == AgentLocationLog.agent_id)
        .where(
            and_(
                User.agency_id == agency_id,
                AgentLocationLog.recorded_at >= start_date,
                AgentLocationLog.recorded_at <= end_date,
            )
        )
        .group_by(AgentLocationLog.agent_id, User.full_name)
    )
    
    if agent_id:
        base_query = base_query.where(AgentLocationLog.agent_id == agent_id)
    
    result = await db.execute(base_query)
    agent_stats = result.all()
    
    if not agent_stats:
        return AgentMovementAnalysisResult(
            summaries=[],
            total_agents=0,
            total_locations_analyzed=0,
            analysis_period_days=analysis_period_days,
            anomalies=[],
        )
    
    total_locations = sum(stat.total_locations for stat in agent_stats)
    
    # For each agent, get detailed location data for clustering
    # This is still necessary for detailed analysis but done per agent
    summaries = []
    anomalies = []
    
    for stat in agent_stats:
        agent_uuid = stat.agent_id
        agent_name = stat.full_name
        
        # Get locations for this agent only
        locations_query = (
            select(AgentLocationLog)
            .where(
                and_(
                    AgentLocationLog.agent_id == agent_uuid,
                    AgentLocationLog.recorded_at >= start_date,
                    AgentLocationLog.recorded_at <= end_date,
                )
            )
            .order_by(AgentLocationLog.recorded_at)
        )
        locations = (await db.execute(locations_query)).scalars().all()
        
        points = []
        for loc in locations:
            point = to_shape(loc.location)
            points.append(
                AgentMovementPoint(
                    latitude=point.y,
                    longitude=point.x,
                    recorded_at=loc.recorded_at,
                    battery_level=loc.battery_level,
                    connectivity_status=loc.connectivity_status,
                )
            )
        
        # Calculate patrol areas using grid-based clustering
        patrol_areas = _identify_patrol_areas(
            points, cluster_radius_meters, min_points_per_cluster
        )
        
        # Calculate movement statistics
        total_distance_km = _calculate_total_distance(points)
        avg_speed = _calculate_average_speed(points) if len(points) > 1 else None
        
        # Battery stats from aggregated query
        battery_stats = {
            "avg": stat.avg_battery,
            "min": stat.min_battery,
            "max": stat.max_battery,
        }
        
        # Connectivity stats
        connectivity_counts = {}
        for p in points:
            conn = p.connectivity_status or "unknown"
            connectivity_counts[conn] = connectivity_counts.get(conn, 0) + 1
        connectivity_stats = {
            "counts": connectivity_counts,
            "most_common": max(connectivity_counts, key=connectivity_counts.get) if connectivity_counts else None,
        }
        
        summaries.append(
            AgentMovementSummary(
                agent_id=agent_uuid,
                agent_name=agent_name,
                total_locations=stat.total_locations,
                total_distance_km=total_distance_km,
                average_speed_kmh=avg_speed,
                patrol_areas=patrol_areas,
                battery_stats=battery_stats,
                connectivity_stats=connectivity_stats,
                analysis_period_days=analysis_period_days,
            )
        )
        
        # Detect anomalies
        agent_anomalies = _detect_movement_anomalies(points)
        anomalies.extend(agent_anomalies)
    
    return AgentMovementAnalysisResult(
        summaries=summaries,
        total_agents=len(agent_stats),
        total_locations_analyzed=total_locations,
        analysis_period_days=analysis_period_days,
        anomalies=anomalies,
    )


async def get_agent_coverage_map(
    db: AsyncSession,
    agency_id: UUID,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    grid_size_meters: float = 100,
) -> List[dict]:
    """
    Generate a grid-based coverage map showing where agents have been.
    Returns grid cells with observation counts.
    Optimized to use simple grid aggregation without ST_SquareGrid.
    """
    if not start_date:
        start_date = datetime.utcnow() - timedelta(days=7)
    if not end_date:
        end_date = datetime.utcnow()
    
    # Get all locations first
    query = (
        select(
            AgentLocationLog.location,
            AgentLocationLog.recorded_at,
        )
        .join(User, User.id == AgentLocationLog.agent_id)
        .where(
            and_(
                User.agency_id == agency_id,
                AgentLocationLog.recorded_at >= start_date,
                AgentLocationLog.recorded_at <= end_date,
            )
        )
    )
    
    locations = (await db.execute(query)).all()
    
    if not locations:
        return []
    
    # Simple grid-based aggregation in Python
    # Convert meters to approximate degrees at equator
    grid_size_degrees = grid_size_meters / 111000.0
    
    from collections import defaultdict
    grid_counts = defaultdict(int)
    
    for loc in locations:
        point = to_shape(loc.location)
        grid_x = int(point.x / grid_size_degrees)
        grid_y = int(point.y / grid_size_degrees)
        grid_counts[(grid_x, grid_y)] += 1
    
    # Convert grid cells to output format
    result = []
    for (grid_x, grid_y), count in grid_counts.items():
        if count > 0:
            centroid_lat = (grid_y + 0.5) * grid_size_degrees
            centroid_lng = (grid_x + 0.5) * grid_size_degrees
            
            result.append({
                "latitude": centroid_lat,
                "longitude": centroid_lng,
                "location_count": count,
                "cell_geometry": None,  # Can be added if needed
            })
    
    # Sort by count descending
    result.sort(key=lambda x: x["location_count"], reverse=True)
    
    return result


def _identify_patrol_areas(
    points: List[AgentMovementPoint],
    radius_meters: float,
    min_points: int,
) -> List[PatrolArea]:
    """Identify patrol areas using grid-based clustering."""
    from collections import defaultdict
    
    # Simple grid-based clustering
    grid_size_degrees = radius_meters / 111000  # Approximate conversion
    location_clusters = defaultdict(list)
    
    for point in points:
        grid_key = (
            int(point.latitude / grid_size_degrees),
            int(point.longitude / grid_size_degrees),
        )
        location_clusters[grid_key].append(point)
    
    patrol_areas = []
    for cluster_points in location_clusters.values():
        if len(cluster_points) < min_points:
            continue
        
        # Calculate centroid
        lats = [p.latitude for p in cluster_points]
        lngs = [p.longitude for p in cluster_points]
        centroid_lat = sum(lats) / len(lats)
        centroid_lng = sum(lngs) / len(lngs)
        
        # Calculate unique hours
        unique_hours = len(set(p.recorded_at.hour for p in cluster_points))
        
        # Estimate coverage percentage (simplified)
        coverage_percentage = min(100.0, (len(cluster_points) / 50.0) * 100)
        
        patrol_areas.append(
            PatrolArea(
                centroid_latitude=centroid_lat,
                centroid_longitude=centroid_lng,
                radius_meters=radius_meters,
                observation_count=len(cluster_points),
                unique_hours=unique_hours,
                coverage_percentage=coverage_percentage,
                first_seen=min(p.recorded_at for p in cluster_points),
                last_seen=max(p.recorded_at for p in cluster_points),
            )
        )
    
    # Sort by observation count
    patrol_areas.sort(key=lambda a: a.observation_count, reverse=True)
    return patrol_areas[:10]  # Top 10 patrol areas


def _calculate_total_distance(points: List[AgentMovementPoint]) -> float:
    """Calculate total distance traveled using Haversine formula."""
    if len(points) < 2:
        return 0.0
    
    total_distance = 0.0
    for i in range(1, len(points)):
        total_distance += _haversine_distance(
            points[i - 1].latitude,
            points[i - 1].longitude,
            points[i].latitude,
            points[i].longitude,
        )
    
    return total_distance


def _haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance between two points in kilometers using Haversine formula."""
    from math import radians, sin, cos, sqrt, asin
    
    R = 6371  # Earth radius in kilometers
    
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    c = 2 * asin(sqrt(a))
    
    return R * c


def _calculate_average_speed(points: List[AgentMovementPoint]) -> Optional[float]:
    """Calculate average speed in km/h."""
    if len(points) < 2:
        return None
    
    total_distance = _calculate_total_distance(points)
    time_span = (points[-1].recorded_at - points[0].recorded_at).total_seconds() / 3600  # hours
    
    if time_span == 0:
        return None
    
    return total_distance / time_span


def _detect_movement_anomalies(points: List[AgentMovementPoint]) -> List[MovementAnomaly]:
    """Detect movement anomalies (rapid jumps, stationary for long periods, etc.)."""
    anomalies = []
    
    if len(points) < 2:
        return anomalies
    
    # Detect rapid location jumps (impossible travel)
    for i in range(1, len(points)):
        distance = _haversine_distance(
            points[i - 1].latitude,
            points[i - 1].longitude,
            points[i].latitude,
            points[i].longitude,
        )
        time_span = (points[i].recorded_at - points[i - 1].recorded_at).total_seconds() / 3600  # hours
        
        if time_span > 0:
            speed = distance / time_span  # km/h
            if speed > 200:  # Unlikely speed for ground vehicle
                anomalies.append(
                    MovementAnomaly(
                        anomaly_type="rapid_movement",
                        location_latitude=points[i].latitude,
                        location_longitude=points[i].longitude,
                        recorded_at=points[i].recorded_at,
                        description=f"Rapid movement detected: {speed:.1f} km/h over {time_span:.1f} hours",
                        severity="warning",
                    )
                )
    
    # Detect low battery anomalies
    low_battery_points = [p for p in points if p.battery_level is not None and p.battery_level < 10]
    if len(low_battery_points) > 5:
        anomalies.append(
            MovementAnomaly(
                anomaly_type="low_battery",
                location_latitude=low_battery_points[0].latitude,
                location_longitude=low_battery_points[0].longitude,
                recorded_at=low_battery_points[0].recorded_at,
                description=f"Multiple low battery readings ({len(low_battery_points)} points < 10%)",
                severity="info",
            )
        )
    
    return anomalies


async def analyze_agent_observation_correlation(
    db: AsyncSession,
    agency_id: UUID,
    agent_id: Optional[UUID] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    proximity_radius_meters: float = 500,
) -> List[AgentObservationCorrelation]:
    """
    Analyze correlation between agent locations and vehicle observations.
    Identifies which agents are most effective at detecting observations in their patrol areas.
    """
    from collections import defaultdict
    
    if not start_date:
        start_date = datetime.utcnow() - timedelta(days=30)
    if not end_date:
        end_date = datetime.utcnow()

    # Get all agents in the agency
    agent_query = select(User.id, User.full_name).where(User.agency_id == agency_id)
    if agent_id:
        agent_query = agent_query.where(User.id == agent_id)

    agents = (await db.execute(agent_query)).all()

    correlations = []

    for agent in agents:
        agent_uuid = agent.id
        agent_name = agent.full_name

        # Get agent locations in the period
        agent_locations_query = select(AgentLocationLog).where(
            and_(
                AgentLocationLog.agent_id == agent_uuid,
                AgentLocationLog.recorded_at >= start_date,
                AgentLocationLog.recorded_at <= end_date,
            )
        )
        agent_locations = (await db.execute(agent_locations_query)).scalars().all()

        if not agent_locations:
            continue

        # Get observations in the period
        observations_query = select(VehicleObservation).where(
            and_(
                VehicleObservation.agent_id == agent_uuid,
                VehicleObservation.observed_at_local >= start_date,
                VehicleObservation.observed_at_local <= end_date,
            )
        )
        observations = (await db.execute(observations_query)).scalars().all()

        # Count observations near agent locations
        observations_near_agent = 0
        total_distance = 0
        productive_areas = defaultdict(int)
        peak_hours = defaultdict(int)

        for obs in observations:
            obs_point = to_shape(obs.location)
            # Find nearest agent location
            min_distance = float("inf")
            nearest_area_key = None

            for loc in agent_locations:
                loc_point = to_shape(loc.location)
                distance = _haversine_distance(
                    loc_point.y, loc_point.x, obs_point.y, obs_point.x
                )
                if distance < min_distance:
                    min_distance = distance
                    # Grid key for area
                    grid_size = proximity_radius_meters / 111000
                    nearest_area_key = (
                        int(obs_point.y / grid_size),
                        int(obs_point.x / grid_size),
                    )

            if min_distance <= proximity_radius_meters:
                observations_near_agent += 1
                total_distance += min_distance
                if nearest_area_key:
                    productive_areas[nearest_area_key] += 1
                peak_hours[obs.observed_at_local.hour] += 1

        total_observations = len(observations)
        total_agent_locations = len(agent_locations)

        correlation_rate = (
            observations_near_agent / total_observations if total_observations > 0 else 0
        )
        avg_distance = (
            total_distance / observations_near_agent if observations_near_agent > 0 else 0
        )

        # Get top productive areas
        top_areas = sorted(productive_areas.items(), key=lambda x: x[1], reverse=True)[:5]
        most_productive_areas = [
            {"grid_key": str(area), "count": count} for area, count in top_areas
        ]

        # Get peak hours
        top_hours = sorted(peak_hours.items(), key=lambda x: x[1], reverse=True)[:3]
        peak_detection_hours = [hour for hour, count in top_hours]

        correlations.append(
            AgentObservationCorrelation(
                agent_id=agent_uuid,
                agent_name=agent_name,
                total_observations=total_observations,
                total_agent_locations=total_agent_locations,
                observations_near_agent=observations_near_agent,
                correlation_rate=correlation_rate,
                average_distance_to_observations=avg_distance,
                most_productive_areas=most_productive_areas,
                peak_detection_hours=peak_detection_hours,
            )
        )

    return correlations


async def generate_tactical_positioning_recommendations(
    db: AsyncSession,
    agency_id: UUID,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
) -> List[TacticalPositioningRecommendation]:
    """
    Generate tactical positioning recommendations based on:
    1. Hotspot locations (high observation density)
    2. Agent coverage gaps (areas with low agent presence)
    3. Route patterns (high traffic corridors)
    """
    if not start_date:
        start_date = datetime.utcnow() - timedelta(days=30)
    if not end_date:
        end_date = datetime.utcnow()

    recommendations = []

    # Find hotspots with high observation density but low agent coverage
    hotspot_query = text("""
        WITH hotspots AS (
            SELECT
                ST_X(ST_Centroid(ST_ClusterWithin(location, 500))) as longitude,
                ST_Y(ST_Centroid(ST_ClusterWithin(location, 500))) as latitude,
                COUNT(*) as observation_count
            FROM vehicleobservation
            JOIN "user" ON "user".id = vehicleobservation.agent_id
            WHERE "user".agency_id = :agency_id
                AND vehicleobservation.observed_at_local >= :start_date
                AND vehicleobservation.observed_at_local <= :end_date
            GROUP BY ST_ClusterWithin(location, 500)
            HAVING COUNT(*) >= 10
            ORDER BY observation_count DESC
            LIMIT 20
        ),
        coverage AS (
            SELECT
                h.latitude,
                h.longitude,
                h.observation_count,
                COUNT(al.id) as agent_presence_count
            FROM hotspots h
            LEFT JOIN agentlocationlog al
                ON ST_DWithin(
                    al.location,
                    ST_SetSRID(ST_MakePoint(h.longitude, h.latitude), 4326),
                    1000
                )
                AND al.recorded_at >= :start_date
                AND al.recorded_at <= :end_date
            GROUP BY h.latitude, h.longitude, h.observation_count
        )
        SELECT
            latitude,
            longitude,
            observation_count,
            agent_presence_count,
            (observation_count::float / GREATEST(agent_presence_count, 1)) as coverage_gap_score
        FROM coverage
        WHERE agent_presence_count < 5 OR coverage_gap_score > 5
        ORDER BY coverage_gap_score DESC
        LIMIT 10
    """)

    result = await db.execute(
        hotspot_query,
        {"agency_id": str(agency_id), "start_date": start_date, "end_date": end_date},
    )

    for row in result:
        priority = "high" if row.coverage_gap_score > 10 else "medium"
        recommendations.append(
            TacticalPositioningRecommendation(
                recommended_latitude=row.latitude,
                recommended_longitude=row.longitude,
                reason=f"High observation density ({row.observation_count}) with low agent coverage ({row.agent_presence_count})",
                expected_impact=f"Increase detection rate in underserved hotspot area",
                hotspot_proximity_km=0.0,  # Already at hotspot
                coverage_gap_score=row.coverage_gap_score,
                priority=priority,
            )
        )

    return recommendations
