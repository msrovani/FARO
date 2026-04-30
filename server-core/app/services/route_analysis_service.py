"""
Route analysis service for F.A.R.O.
Implements geospatial pattern detection and route correlation without placeholders.
"""
from __future__ import annotations

import asyncio

import math
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from uuid import UUID

from geoalchemy2.shape import from_shape, to_shape
from geoalchemy2.functions import (
    ST_Centroid, ST_Extent, ST_Azimuth, ST_StartPoint, ST_EndPoint,
    ST_MakePoint, ST_SetSRID, ST_X, ST_Y
)
from shapely.geometry import LineString, Point, Polygon
from sqlalchemy import and_, func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import (
    AlgorithmType,
    RoutePattern,
    SuspicionReport,
    Unit,
    User,
    VehicleObservation,
)
from app.schemas.common import GeolocationPoint
from app.schemas.route import RouteTimelineItem
from app.services.analytics_service import _register_run
from app.services.event_bus import event_bus


@dataclass
class RouteAnalysisResult:
    plate_number: str
    observation_count: int
    first_observed_at: datetime
    last_observed_at: datetime
    centroid_lat: float
    centroid_lng: float
    bounding_box: list[tuple[float, float]]  # (lat, lng) - 4 corners
    corridor_points: list[tuple[float, float]] | None
    recurrence_score: float
    pattern_strength: str
    common_hours: list[int]
    common_days: list[int]
    predominant_direction: float | None


def _calculate_recurrence_score(timestamps: list[datetime]) -> float:
    if len(timestamps) < 2:
        return 0.0

    intervals = [
        (timestamps[idx] - timestamps[idx - 1]).total_seconds() / 3600.0
        for idx in range(1, len(timestamps))
    ]
    if not intervals:
        return 0.0

    mean_interval = sum(intervals) / len(intervals)
    if mean_interval <= 0:
        return 1.0

    variance = sum((value - mean_interval) ** 2 for value in intervals) / len(intervals)
    coefficient_variation = math.sqrt(variance) / mean_interval
    return max(0.0, min(1.0, 1.0 - coefficient_variation))


def _determine_pattern_strength(
    observation_count: int,
    recurrence_score: float,
    bounding_box: list[tuple[float, float]],
) -> str:
    lat_range = max(point[0] for point in bounding_box) - min(point[0] for point in bounding_box)
    lng_range = max(point[1] for point in bounding_box) - min(point[1] for point in bounding_box)
    area = lat_range * lng_range

    score = 0.0
    if observation_count >= 10:
        score += 0.4
    elif observation_count >= 5:
        score += 0.2

    score += recurrence_score * 0.4

    if area < 0.01:
        score += 0.2
    elif area < 0.1:
        score += 0.1

    if score >= 0.7:
        return "strong"
    if score >= 0.4:
        return "moderate"
    return "weak"


def _calculate_corridor(points: list[tuple[float, float]]) -> list[tuple[float, float]]:
    # Keep original temporal ordering but collapse exact duplicates.
    if not points:
        return []
    corridor: list[tuple[float, float]] = [points[0]]
    for point in points[1:]:
        if point != corridor[-1]:
            corridor.append(point)
    return corridor


def _calculate_predominant_direction(points: list[tuple[float, float]]) -> float | None:
    if len(points) < 2:
        return None
    start_lat, start_lng = points[0]
    end_lat, end_lng = points[-1]
    delta_lng = math.radians(end_lng - start_lng)
    start_lat_rad = math.radians(start_lat)
    end_lat_rad = math.radians(end_lat)
    x_axis = math.sin(delta_lng) * math.cos(end_lat_rad)
    y_axis = (
        math.cos(start_lat_rad) * math.sin(end_lat_rad)
        - math.sin(start_lat_rad) * math.cos(end_lat_rad) * math.cos(delta_lng)
    )
    bearing = math.degrees(math.atan2(x_axis, y_axis))
    return (bearing + 360.0) % 360.0


def _extract_common_hours_days(timestamps: list[datetime]) -> tuple[list[int], list[int]]:
    hour_counts: dict[int, int] = {}
    day_counts: dict[int, int] = {}
    for timestamp in timestamps:
        hour_counts[timestamp.hour] = hour_counts.get(timestamp.hour, 0) + 1
        day_counts[timestamp.weekday()] = day_counts.get(timestamp.weekday(), 0) + 1

    common_hours = [
        hour for hour, _ in sorted(hour_counts.items(), key=lambda item: item[1], reverse=True)[:5]
    ]
    common_days = [
        day for day, _ in sorted(day_counts.items(), key=lambda item: item[1], reverse=True)[:3]
    ]
    return common_hours, common_days


async def analyze_vehicle_route(
    db: AsyncSession,
    plate_number: str,
    agency_id: UUID,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    min_observations: int = 3,
) -> Optional[RouteAnalysisResult]:
    """
    Analyze vehicle route using PostGIS functions for spatial calculations.
    Optimized to use database-side calculations instead of Python.
    """
    normalized_plate = plate_number.upper().strip()
    
    # Use PostGIS for spatial calculations in single query
    from sqlalchemy import text
    
    date_filter = ""
    params = {
        "plate": normalized_plate,
        "agency_id": str(agency_id),
        "min_obs": min_observations,
    }
    
    if start_date:
        date_filter += " AND observed_at_local >= :start_date"
        params["start_date"] = start_date
    if end_date:
        date_filter += " AND observed_at_local <= :end_date"
        params["end_date"] = end_date
    
    query = text(f"""
        WITH route_data AS (
            SELECT 
                id,
                location,
                observed_at_local,
                plate_number
            FROM vehicleobservation
            WHERE plate_number = :plate
                AND agency_id = :agency_id
                {date_filter}
            ORDER BY observed_at_local
        ),
        stats AS (
            SELECT 
                COUNT(*) as observation_count,
                MIN(observed_at_local) as first_observed_at,
                MAX(observed_at_local) as last_observed_at,
                ST_X(ST_Centroid(ST_Collect(location))) as centroid_lng,
                ST_Y(ST_Centroid(ST_Collect(location))) as centroid_lat,
                ST_XMin(ST_Extent(location)) as min_lng,
                ST_XMax(ST_Extent(location)) as max_lng,
                ST_YMin(ST_Extent(location)) as min_lat,
                ST_YMax(ST_Extent(location)) as max_lat
            FROM route_data
        ),
        bearing AS (
            SELECT 
                degrees(ST_Azimuth(
                    ST_StartPoint(ST_MakeLine(location ORDER BY observed_at_local)),
                    ST_EndPoint(ST_MakeLine(location ORDER BY observed_at_local))
                )) as predominant_direction
            FROM route_data
        )
        SELECT 
            s.observation_count,
            s.first_observed_at,
            s.last_observed_at,
            s.centroid_lat,
            s.centroid_lng,
            s.min_lat, s.max_lat, s.min_lng, s.max_lng,
            b.predominant_direction
        FROM stats s, bearing b
        HAVING s.observation_count >= :min_obs
    """)
    
    result = await db.execute(query, params)
    row = result.first()
    
    if not row:
        return None
    
    # Get timestamps for recurrence calculation (still need Python for this)
    timestamp_query = select(VehicleObservation.observed_at_local).where(
        VehicleObservation.plate_number == normalized_plate,
        VehicleObservation.agency_id == agency_id,
    )
    if start_date:
        timestamp_query = timestamp_query.where(VehicleObservation.observed_at_local >= start_date)
    if end_date:
        timestamp_query = timestamp_query.where(VehicleObservation.observed_at_local <= end_date)
    timestamp_query = timestamp_query.order_by(VehicleObservation.observed_at_local)
    
    timestamps = [t[0] for t in (await db.execute(timestamp_query)).all()]
    
    bounding_box = [
        (row.min_lat, row.min_lng),
        (row.max_lat, row.min_lng),
        (row.max_lat, row.max_lng),
        (row.min_lat, row.max_lng),
    ]
    
    recurrence_score = _calculate_recurrence_score(timestamps)
    pattern_strength = _determine_pattern_strength(row.observation_count, recurrence_score, bounding_box)
    
    # Get points for corridor calculation
    points_query = select(VehicleObservation.location).where(
        VehicleObservation.plate_number == normalized_plate,
        VehicleObservation.agency_id == agency_id,
    )
    if start_date:
        points_query = points_query.where(VehicleObservation.observed_at_local >= start_date)
    if end_date:
        points_query = points_query.where(VehicleObservation.observed_at_local <= end_date)
    points_query = points_query.order_by(VehicleObservation.observed_at_local)
    
    points = []
    for obs in (await db.execute(points_query)).scalars().all():
        point = to_shape(obs)
        points.append((point.y, point.x))
    
    corridor_points = _calculate_corridor(points) if pattern_strength in {"moderate", "strong"} else None
    common_hours, common_days = _extract_common_hours_days(timestamps)
    
    return RouteAnalysisResult(
        plate_number=normalized_plate,
        observation_count=row.observation_count,
        first_observed_at=row.first_observed_at,
        last_observed_at=row.last_observed_at,
        centroid_lat=row.centroid_lat,
        centroid_lng=row.centroid_lng,
        bounding_box=bounding_box,
        corridor_points=corridor_points,
        recurrence_score=recurrence_score,
        pattern_strength=pattern_strength,
        common_hours=common_hours,
        common_days=common_days,
        predominant_direction=row.predominant_direction,
    )


async def save_route_pattern(db: AsyncSession, result: RouteAnalysisResult, agency_id: UUID) -> RoutePattern:
    polygon_ring = result.bounding_box + [result.bounding_box[0]]
    polygon_shape = Polygon([(lng, lat) for lat, lng in polygon_ring])
    centroid_shape = Point(result.centroid_lng, result.centroid_lat)

    corridor_geom = None
    if result.corridor_points and len(result.corridor_points) >= 2:
        corridor_geom = from_shape(
            LineString([(lng, lat) for lat, lng in result.corridor_points]),
            srid=4326,
        )

    pattern = RoutePattern(
        agency_id=agency_id,
        plate_number=result.plate_number,
        observation_count=result.observation_count,
        first_observed_at=result.first_observed_at,
        last_observed_at=result.last_observed_at,
        centroid_location=from_shape(centroid_shape, srid=4326),
        bounding_box=from_shape(polygon_shape, srid=4326),
        corridor=corridor_geom,
        recurrence_score=result.recurrence_score,
        pattern_strength=result.pattern_strength,
        common_hours=result.common_hours,
        common_days=result.common_days,
        primary_corridor_name=None,
        predominant_direction=result.predominant_direction,
        analyzed_at=datetime.utcnow(),
        analysis_version="1.1",
    )
    db.add(pattern)
    await db.flush()

    await _register_run(
        db,
        algorithm_type=AlgorithmType.ROUTE_ANOMALY,
        observation_id=None,
        payload={
            "payload_version": "v1",
            "analysis_type": "route_pattern",
            "plate_number": result.plate_number,
            "observation_count": result.observation_count,
            "pattern_strength": result.pattern_strength,
            "recurrence_score": result.recurrence_score,
        },
        outcome=None,
    )
    await event_bus.publish(
        "route_pattern_updated",
        {
            "payload_version": "v1",
            "plate_number": result.plate_number,
            "pattern_id": str(pattern.id),
            "pattern_strength": result.pattern_strength,
            "recurrence_score": result.recurrence_score,
        },
    )
    return pattern


async def get_route_timeline(
    db: AsyncSession,
    plate_number: str,
    agency_id: UUID,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
) -> list[RouteTimelineItem]:
    normalized_plate = plate_number.upper().strip()
    query = (
        select(VehicleObservation, User.full_name, Unit.name, SuspicionReport.level)
        .join(User, User.id == VehicleObservation.agent_id)
        .outerjoin(Unit, Unit.id == User.unit_id)
        .outerjoin(SuspicionReport, SuspicionReport.observation_id == VehicleObservation.id)
        .where(
            VehicleObservation.plate_number == normalized_plate,
            VehicleObservation.agency_id == agency_id,
        )
    )
    if start_date:
        query = query.where(VehicleObservation.observed_at_local >= start_date)
    if end_date:
        query = query.where(VehicleObservation.observed_at_local <= end_date)
    query = query.order_by(VehicleObservation.observed_at_local)

    rows = (await db.execute(query)).all()
    timeline_items: list[RouteTimelineItem] = []
    for observation, agent_name, unit_name, suspicion_level in rows:
        point = to_shape(observation.location)
        timeline_items.append(
            RouteTimelineItem(
                observation_id=observation.id,
                timestamp=observation.observed_at_local,
                location=GeolocationPoint(
                    latitude=point.y,
                    longitude=point.x,
                    accuracy=observation.location_accuracy,
                ),
                plate_number=observation.plate_number,
                agent_name=agent_name,
                unit_name=unit_name,
                has_suspicion=suspicion_level is not None,
                suspicion_level=suspicion_level.value if suspicion_level is not None else None,
            )
        )
    return timeline_items


# CPU-bound calculation functions for ProcessPoolExecutor
def _calculate_recurrence_score_sync(timestamps: list[datetime]) -> float:
    """Synchronous version for ProcessPoolExecutor."""
    return _calculate_recurrence_score(timestamps)


def _calculate_predominant_direction_sync(points: list[tuple[float, float]]) -> float | None:
    """Synchronous version for ProcessPoolExecutor."""
    return _calculate_predominant_direction(points)


async def analyze_vehicle_route_parallel(
    db: AsyncSession,
    plate_number: str,
    agency_id: UUID,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    min_observations: int = 3,
) -> Optional[RouteAnalysisResult]:
    """
    Analyze vehicle route with parallel CPU-bound calculations.
    
    Uses ProcessPoolExecutor for CPU-intensive geospatial calculations.
    """
    from app.utils.process_pool import run_in_process_pool
    
    normalized_plate = plate_number.upper().strip()
    query = select(VehicleObservation).where(
        VehicleObservation.plate_number == normalized_plate,
        VehicleObservation.agency_id == agency_id,
    )
    if start_date:
        query = query.where(VehicleObservation.observed_at_local >= start_date)
    if end_date:
        query = query.where(VehicleObservation.observed_at_local <= end_date)
    query = query.order_by(VehicleObservation.observed_at_local)

    observations = (await db.execute(query)).scalars().all()
    if len(observations) < min_observations:
        return None

    points = []
    timestamps = []
    for observation in observations:
        point = to_shape(observation.location)
        points.append((point.y, point.x))
        timestamps.append(observation.observed_at_local)

    # Parallel CPU-bound calculations with monitoring
    recurrence_score, predominant_direction = await asyncio.gather(
        run_in_process_pool(_calculate_recurrence_score_sync, timestamps, task_type="route_recurrence"),
        run_in_process_pool(_calculate_predominant_direction_sync, points, task_type="route_direction")
    )

    centroid_lat = sum(point[0] for point in points) / len(points)
    centroid_lng = sum(point[1] for point in points) / len(points)
    min_lat = min(point[0] for point in points)
    max_lat = max(point[0] for point in points)
    min_lng = min(point[1] for point in points)
    max_lng = max(point[1] for point in points)
    bounding_box = [
        (min_lat, min_lng),
        (max_lat, min_lng),
        (max_lat, max_lng),
        (min_lat, max_lng),
    ]

    pattern_strength = _determine_pattern_strength(len(observations), recurrence_score, bounding_box)
    corridor_points = _calculate_corridor(points) if pattern_strength in {"moderate", "strong"} else None
    common_hours, common_days = _extract_common_hours_days(timestamps)

    return RouteAnalysisResult(
        plate_number=normalized_plate,
        observation_count=len(observations),
        first_observed_at=timestamps[0],
        last_observed_at=timestamps[-1],
        centroid_lat=centroid_lat,
        centroid_lng=centroid_lng,
        bounding_box=bounding_box,
        corridor_points=corridor_points,
        recurrence_score=recurrence_score,
        pattern_strength=pattern_strength,
        common_hours=common_hours,
        common_days=common_days,
        predominant_direction=predominant_direction,
    )
