"""
Hotspot Analysis Service for F.A.R.O.
Spatial aggregation of vehicle observations to identify criminal hotspots.
Uses PostGIS spatial clustering and density analysis.
"""
from __future__ import annotations

import asyncio

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List, Optional
from uuid import UUID

from geoalchemy2.shape import to_shape
from geoalchemy2.functions import ST_DWithin, ST_ClusterDBSCAN, ST_Centroid, ST_NumGeometries
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import VehicleObservation, SuspicionReport
from app.schemas.common import GeolocationPoint


@dataclass
class HotspotPoint:
    latitude: float
    longitude: float
    observation_count: int
    suspicion_count: int
    unique_plates: int
    radius_meters: float
    intensity_score: float


@dataclass
class HotspotAnalysisResult:
    hotspots: List[HotspotPoint]
    total_observations: int
    total_suspicions: int
    analysis_period_days: int
    cluster_radius_meters: float
    min_points_per_cluster: int


async def analyze_hotspots(
    db: AsyncSession,
    agency_id: UUID,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    cluster_radius_meters: float = 500,
    min_points_per_cluster: int = 5,
) -> HotspotAnalysisResult:
    """
    Analyze spatial hotspots of vehicle observations using PostGIS ST_ClusterDBSCAN.
    Returns clustered areas with high observation density.
    Optimized to use database-side clustering instead of Python.
    """
    if not start_date:
        start_date = datetime.utcnow() - timedelta(days=30)
    if not end_date:
        end_date = datetime.utcnow()
    
    analysis_period_days = (end_date - start_date).days
    
    # Optimized query using PostGIS ST_ClusterDBSCAN
    # Get clusters with statistics in single query
    from sqlalchemy import text
    
    query = text("""
        WITH clusters AS (
            SELECT 
                ST_ClusterDBSCAN(location, eps := :radius, minpoints := :min_points) OVER () as cluster_id,
                id,
                location,
                plate_number
            FROM vehicleobservation
            WHERE agency_id = :agency_id
                AND observed_at_local >= :start_date
                AND observed_at_local <= :end_date
        ),
        cluster_stats AS (
            SELECT 
                cluster_id,
                COUNT(*) as observation_count,
                COUNT(DISTINCT plate_number) as unique_plates,
                ST_X(ST_Centroid(ST_Collect(location))) as centroid_longitude,
                ST_Y(ST_Centroid(ST_Collect(location))) as centroid_latitude,
                array_agg(id) as observation_ids
            FROM clusters
            WHERE cluster_id IS NOT NULL
            GROUP BY cluster_id
            HAVING COUNT(*) >= :min_points
        ),
        suspicion_counts AS (
            SELECT 
                cs.cluster_id,
                COUNT(sr.id) as suspicion_count
            FROM cluster_stats cs
            LEFT JOIN unnest(cs.observation_ids) as obs_id ON true
            LEFT JOIN suspicionreport sr ON sr.observation_id = obs_id
            GROUP BY cs.cluster_id
        )
        SELECT 
            cs.cluster_id,
            cs.observation_count,
            cs.unique_plates,
            cs.centroid_latitude,
            cs.centroid_longitude,
            COALESCE(sc.suspicion_count, 0) as suspicion_count,
            LEAST(1.0, (cs.observation_count::float / 50.0) + 
                   COALESCE((sc.suspicion_count::float / GREATEST(cs.observation_count, 1)) * 0.5, 0)) as intensity_score
        FROM cluster_stats cs
        LEFT JOIN suspicion_counts sc ON sc.cluster_id = cs.cluster_id
        ORDER BY intensity_score DESC
        LIMIT 20
    """)
    
    result = await db.execute(query, {
        "agency_id": str(agency_id),
        "start_date": start_date,
        "end_date": end_date,
        "radius": cluster_radius_meters,
        "min_points": min_points_per_cluster,
    })
    
    hotspots = []
    total_observations = 0
    total_suspicions = 0
    
    for row in result:
        hotspots.append(
            HotspotPoint(
                latitude=row.centroid_latitude,
                longitude=row.centroid_longitude,
                observation_count=row.observation_count,
                suspicion_count=row.suspicion_count,
                unique_plates=row.unique_plates,
                radius_meters=cluster_radius_meters,
                intensity_score=row.intensity_score,
            )
        )
        total_observations += row.observation_count
        total_suspicions += row.suspicion_count
    
    return HotspotAnalysisResult(
        hotspots=hotspots,
        total_observations=total_observations,
        total_suspicions=total_suspicions,
        analysis_period_days=analysis_period_days,
        cluster_radius_meters=cluster_radius_meters,
        min_points_per_cluster=min_points_per_cluster,
    )


async def get_hotspot_timeline(
    db: AsyncSession,
    agency_id: UUID,
    latitude: float,
    longitude: float,
    radius_meters: float = 500,
    days: int = 7,
) -> dict:
    """
    Get temporal distribution of observations around a specific location.
    Returns hourly and daily patterns.
    """
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # Query observations within radius
    from sqlalchemy import text
    
    query = text("""
        SELECT 
            DATE_TRUNC('hour', observed_at_local) as hour,
            COUNT(*) as count,
            COUNT(DISTINCT plate_number) as unique_plates
        FROM vehicleobservation
        WHERE 
            agency_id = :agency_id
            AND ST_DWithin(
                location, 
                ST_SetSRID(ST_MakePoint(:lng, :lat), 4326), 
                :radius
            )
            AND observed_at_local >= :start_date
        GROUP BY DATE_TRUNC('hour', observed_at_local)
        ORDER BY hour
    """)
    
    result = await db.execute(
        query,
        {
            "agency_id": str(agency_id),
            "lat": latitude,
            "lng": longitude,
            "radius": radius_meters,
            "start_date": start_date,
        },
    )
    
    hourly_data = [
        {"hour": row.hour.isoformat(), "count": row.count, "unique_plates": row.unique_plates}
        for row in result
    ]
    
    # Calculate daily pattern
    daily_pattern = [0] * 24
    for row in hourly_data:
        hour = datetime.fromisoformat(row["hour"]).hour
        daily_pattern[hour] += row["count"]
    
    return {
        "hourly_data": hourly_data,
        "daily_pattern": daily_pattern,
        "total_observations": sum(row["count"] for row in hourly_data),
        "peak_hour": daily_pattern.index(max(daily_pattern)) if daily_pattern else None,
    }


async def get_hotspot_plates(
    db: AsyncSession,
    agency_id: UUID,
    latitude: float,
    longitude: float,
    radius_meters: float = 500,
    limit: int = 50,
) -> List[dict]:
    """
    Get most frequent plates observed in a hotspot area.
    """
    from sqlalchemy import text
    
    query = text("""
        SELECT 
            plate_number,
            COUNT(*) as observation_count,
            MAX(observed_at_local) as last_seen,
            MIN(observed_at_local) as first_seen
        FROM vehicleobservation
        WHERE 
            agency_id = :agency_id
            AND ST_DWithin(
                location, 
                ST_SetSRID(ST_MakePoint(:lng, :lat), 4326), 
                :radius
            )
        GROUP BY plate_number
        ORDER BY observation_count DESC
        LIMIT :limit
    """)
    
    result = await db.execute(
        query,
        {
            "agency_id": str(agency_id),
            "lat": latitude,
            "lng": longitude,
            "radius": radius_meters,
            "limit": limit,
        },
    )
    
    return [
        {
            "plate_number": row.plate_number,
            "observation_count": row.observation_count,
            "last_seen": row.last_seen.isoformat() if row.last_seen else None,
            "first_seen": row.first_seen.isoformat() if row.first_seen else None,
        }
        for row in result
    ]


# CPU-bound clustering function for ProcessPoolExecutor
def _cluster_observations_sync(
    observations: list,
    cluster_radius_meters: float,
    min_points_per_cluster: int,
    suspicion_counts: dict
) -> list[HotspotPoint]:
    """
    Synchronous version of clustering for ProcessPoolExecutor.
    """
    from collections import defaultdict
    
    location_clusters = defaultdict(list)
    for obs in observations:
        point = to_shape(obs.location)
        # Simple grid-based clustering
        grid_key = (
            int(point.y / (cluster_radius_meters / 111000)),
            int(point.x / (cluster_radius_meters / 111000)),
        )
        location_clusters[grid_key].append(obs)
    
    hotspots = []
    
    for cluster_observations in location_clusters.values():
        if len(cluster_observations) < min_points_per_cluster:
            continue
        
        # Calculate cluster centroid
        lats = [to_shape(obs.location).y for obs in cluster_observations]
        lngs = [to_shape(obs.location).x for obs in cluster_observations]
        centroid_lat = sum(lats) / len(lats)
        centroid_lng = sum(lngs) / len(lngs)
        
        # Calculate cluster statistics
        cluster_suspicion_count = sum(
            suspicion_counts.get(obs.id, 0) for obs in cluster_observations
        )
        unique_plates = len(set(obs.plate_number for obs in cluster_observations))
        
        # Calculate intensity score (0-1)
        intensity_score = min(1.0, len(cluster_observations) / 50.0)
        if cluster_suspicion_count > 0:
            intensity_score = min(1.0, intensity_score + (cluster_suspicion_count / len(cluster_observations)) * 0.5)
        
        hotspots.append(
            HotspotPoint(
                latitude=centroid_lat,
                longitude=centroid_lng,
                observation_count=len(cluster_observations),
                suspicion_count=cluster_suspicion_count,
                unique_plates=unique_plates,
                radius_meters=cluster_radius_meters,
                intensity_score=intensity_score,
            )
        )
    
    # Sort hotspots by intensity score
    hotspots.sort(key=lambda h: h.intensity_score, reverse=True)
    
    return hotspots[:20]  # Top 20 hotspots


async def analyze_hotspots_parallel(
    db: AsyncSession,
    agency_id: UUID,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    cluster_radius_meters: float = 500,
    min_points_per_cluster: int = 5,
) -> HotspotAnalysisResult:
    """
    Analyze spatial hotspots with parallel CPU-bound clustering.
    
    Uses ProcessPoolExecutor for CPU-intensive spatial clustering.
    """
    from app.utils.process_pool import run_in_process_pool
    
    if not start_date:
        start_date = datetime.utcnow() - timedelta(days=30)
    if not end_date:
        end_date = datetime.utcnow()
    
    analysis_period_days = (end_date - start_date).days
    
    # Query observations
    query = (
        select(
            VehicleObservation.id,
            VehicleObservation.location,
            VehicleObservation.plate_number,
        )
        .where(
            and_(
                VehicleObservation.agency_id == agency_id,
                VehicleObservation.observed_at_local >= start_date,
                VehicleObservation.observed_at_local <= end_date,
            )
        )
    )
    
    observations = (await db.execute(query)).all()
    
    if not observations:
        return HotspotAnalysisResult(
            hotspots=[],
            total_observations=0,
            total_suspicions=0,
            analysis_period_days=analysis_period_days,
            cluster_radius_meters=cluster_radius_meters,
            min_points_per_cluster=min_points_per_cluster,
        )
    
    # Get suspicion counts
    observation_ids = [obs.id for obs in observations]
    suspicion_query = (
        select(
            SuspicionReport.observation_id,
            func.count(SuspicionReport.id).label("suspicion_count"),
        )
        .where(SuspicionReport.observation_id.in_(observation_ids))
        .group_by(SuspicionReport.observation_id)
    )
    suspicion_counts = {
        row.observation_id: row.suspicion_count
        for row in (await db.execute(suspicion_query)).all()
    }
    
    total_suspicions = sum(suspicion_counts.values())
    
    # Run clustering in process pool with monitoring
    hotspots = await run_in_process_pool(
        _cluster_observations_sync,
        observations,
        cluster_radius_meters,
        min_points_per_cluster,
        suspicion_counts,
        task_type="hotspot_clustering",
        enable_monitoring=True,
        enable_circuit_breaker=True,
    )
    
    return HotspotAnalysisResult(
        hotspots=hotspots,
        total_observations=len(observations),
        total_suspicions=total_suspicions,
        analysis_period_days=analysis_period_days,
        cluster_radius_meters=cluster_radius_meters,
        min_points_per_cluster=min_points_per_cluster,
    )
