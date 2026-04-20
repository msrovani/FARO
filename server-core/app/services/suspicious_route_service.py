"""
Suspicious Route Service for F.A.R.O.
Manually registered suspicious routes for intelligence analysis with PostGIS integration.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, List, Optional
from uuid import UUID

from geoalchemy2.shape import from_shape, to_shape
from geoalchemy2.functions import ST_Distance, ST_Intersects, ST_Buffer
from shapely.geometry import LineString, Point
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import (
    SuspiciousRoute,
    User,
    VehicleObservation,
)
from app.schemas.common import GeolocationPoint
from app.schemas.suspicious_route import (
    SuspiciousRouteCreate,
    SuspiciousRouteUpdate,
    SuspiciousRouteResponse,
    SuspiciousRouteMatchRequest,
    SuspiciousRouteMatchResponse,
)


async def create_suspicious_route(
    db: AsyncSession,
    route_data: SuspiciousRouteCreate,
    agency_id: UUID,
    created_by: UUID,
) -> SuspiciousRoute:
    """Create a new suspicious route with PostGIS geometry."""
    # Convert route points to LineString
    coords = [(point.longitude, point.latitude) for point in route_data.route_points]
    line_string = LineString(coords)
    
    route = SuspiciousRoute(
        agency_id=agency_id,
        name=route_data.name,
        crime_type=route_data.crime_type,
        direction=route_data.direction,
        risk_level=route_data.risk_level,
        route_geometry=from_shape(line_string, srid=4326),
        buffer_distance_meters=route_data.buffer_distance_meters,
        active_from_hour=route_data.active_from_hour,
        active_to_hour=route_data.active_to_hour,
        active_days=route_data.active_days,
        justification=route_data.justification,
        created_by=created_by,
        approval_status="pending",
        is_active=True,
    )
    db.add(route)
    await db.flush()
    return route


async def get_suspicious_route(
    db: AsyncSession,
    route_id: UUID,
    agency_id: UUID,
) -> Optional[SuspiciousRoute]:
    """Get a suspicious route by ID."""
    query = select(SuspiciousRoute).where(
        and_(
            SuspiciousRoute.id == route_id,
            SuspiciousRoute.agency_id == agency_id,
        )
    )
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def list_suspicious_routes(
    db: AsyncSession,
    agency_id: UUID,
    crime_type: Optional[str] = None,
    risk_level: Optional[str] = None,
    approval_status: Optional[str] = None,
    is_active: Optional[bool] = None,
    offset: int = 0,
    limit: int = 50,
) -> tuple[List[SuspiciousRoute], int]:
    """List suspicious routes with filters."""
    query = select(SuspiciousRoute).where(SuspiciousRoute.agency_id == agency_id)
    
    if crime_type:
        query = query.where(SuspiciousRoute.crime_type == crime_type)
    if risk_level:
        query = query.where(SuspiciousRoute.risk_level == risk_level)
    if approval_status:
        query = query.where(SuspiciousRoute.approval_status == approval_status)
    if is_active is not None:
        query = query.where(SuspiciousRoute.is_active == is_active)
    
    query = query.order_by(SuspiciousRoute.created_at.desc())
    
    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_count = (await db.execute(count_query)).scalar()
    
    # Get paginated results
    query = query.offset(offset).limit(limit)
    routes = (await db.execute(query)).scalars().all()
    
    return list(routes), total_count


async def update_suspicious_route(
    db: AsyncSession,
    route_id: UUID,
    agency_id: UUID,
    update_data: SuspiciousRouteUpdate,
) -> Optional[SuspiciousRoute]:
    """Update a suspicious route."""
    route = await get_suspicious_route(db, route_id, agency_id)
    if not route:
        return None
    
    update_dict = update_data.model_dump(exclude_unset=True)
    
    # Handle geometry update if provided
    if "route_points" in update_dict:
        coords = [(point.longitude, point.latitude) for point in update_dict["route_points"]]
        line_string = LineString(coords)
        route.route_geometry = from_shape(line_string, srid=4326)
        del update_dict["route_points"]
    
    for field, value in update_dict.items():
        setattr(route, field, value)
    
    await db.flush()
    return route


async def delete_suspicious_route(
    db: AsyncSession,
    route_id: UUID,
    agency_id: UUID,
) -> bool:
    """Soft delete (deactivate) a suspicious route."""
    route = await get_suspicious_route(db, route_id, agency_id)
    if not route:
        return False
    
    route.is_active = False
    await db.flush()
    return True


async def check_route_match(
    db: AsyncSession,
    match_request: SuspiciousRouteMatchRequest,
    agency_id: UUID,
) -> SuspiciousRouteMatchResponse:
    """
    Check if an observation matches any suspicious route using PostGIS.
    Uses single SQL query with ST_Intersects and ST_DWithin for batch processing.
    """
    from sqlalchemy import text
    
    # Convert observation point to PostGIS Point
    obs_point = Point(match_request.location.longitude, match_request.location.latitude)
    obs_geom = from_shape(obs_point, srid=4326)
    
    # Check time-based constraints
    obs_hour = match_request.observed_at.hour
    obs_day = match_request.observed_at.weekday()
    
    # Single query to find all matching routes
    # Uses ST_Intersects for direct intersection and ST_DWithin for proximity
    query = text("""
        SELECT 
            id, name, crime_type, risk_level,
            CASE 
                WHEN ST_Intersects(route_geometry, :obs_geom) THEN 'intersection'
                WHEN buffer_distance_meters IS NOT NULL 
                     AND ST_DWithin(route_geometry, :obs_geom, buffer_distance_meters) 
                THEN 'proximity'
                ELSE NULL
            END as match_type,
            CASE 
                WHEN buffer_distance_meters IS NOT NULL 
                     AND ST_DWithin(route_geometry, :obs_geom, buffer_distance_meters) 
                THEN ST_Distance(route_geometry, :obs_geom)
                ELSE NULL
            END as distance_meters
        FROM suspiciousroute
        WHERE 
            agency_id = :agency_id
            AND is_active = true
            AND approval_status = 'approved'
            AND (
                active_from_hour IS NULL OR :obs_hour >= active_from_hour
            )
            AND (
                active_to_hour IS NULL OR :obs_hour <= active_to_hour
            )
            AND (
                active_days IS NULL OR :obs_day = ANY(active_days)
            )
            AND (
                ST_Intersects(route_geometry, :obs_geom)
                OR (buffer_distance_meters IS NOT NULL 
                    AND ST_DWithin(route_geometry, :obs_geom, buffer_distance_meters))
            )
    """)
    
    # Convert geometry to WKT for SQL
    from geoalchemy2.shape import to_shape
    obs_geom_wkt = to_shape(obs_geom).to_wkt()
    
    result = await db.execute(query, {
        "agency_id": str(agency_id),
        "obs_geom": obs_geom_wkt,
        "obs_hour": obs_hour,
        "obs_day": obs_day,
    })
    
    matched_routes = []
    min_distance = None
    
    for row in result:
        match_data = {
            "route_id": str(row.id),
            "route_name": row.name,
            "crime_type": row.crime_type,
            "risk_level": row.risk_level,
            "match_type": row.match_type,
        }
        if row.distance_meters is not None:
            match_data["distance_meters"] = row.distance_meters
            if min_distance is None or row.distance_meters < min_distance:
                min_distance = row.distance_meters
        matched_routes.append(match_data)
    
    return SuspiciousRouteMatchResponse(
        matches=len(matched_routes) > 0,
        matched_routes=matched_routes,
        distance_meters=min_distance,
        alert_triggered=len(matched_routes) > 0,
    )


async def approve_route(
    db: AsyncSession,
    route_id: UUID,
    agency_id: UUID,
    approved_by: UUID,
    approval_status: str,
    justification: Optional[str] = None,
) -> Optional[SuspiciousRoute]:
    """Approve or reject a suspicious route."""
    route = await get_suspicious_route(db, route_id, agency_id)
    if not route:
        return None
    
    route.approval_status = approval_status
    route.approved_by = approved_by
    if justification:
        route.justification = justification
    
    await db.flush()
    return route


def route_to_response(route: SuspiciousRoute) -> SuspiciousRouteResponse:
    """Convert SuspiciousRoute model to response schema."""
    line_shape = to_shape(route.route_geometry)
    route_points = [
        GeolocationPoint(latitude=lat, longitude=lng)
        for lng, lat in line_shape.coords
    ]
    
    return SuspiciousRouteResponse(
        id=route.id,
        agency_id=route.agency_id,
        name=route.name,
        crime_type=route.crime_type,
        direction=route.direction,
        risk_level=route.risk_level,
        route_points=route_points,
        buffer_distance_meters=route.buffer_distance_meters,
        active_from_hour=route.active_from_hour,
        active_to_hour=route.active_to_hour,
        active_days=route.active_days,
        justification=route.justification,
        created_by=route.created_by,
        approved_by=route.approved_by,
        approval_status=route.approval_status,
        is_active=route.is_active,
        created_at=route.created_at,
        updated_at=route.updated_at,
    )
