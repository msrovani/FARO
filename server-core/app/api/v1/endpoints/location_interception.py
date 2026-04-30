"""
F.A.R.O. Location Interception API
Endpoints for location-based INTERCEPT alerts and agent coordination.
"""

import logging
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_db
from app.api.v1.endpoints.auth import get_current_user
from app.api.v1.endpoints.intelligence import require_intelligence_role
from app.db.base import User, UserRole
from app.services.location_interception_service import get_intercept_alerts_by_location

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/location-alerts", response_model=List[dict])
async def get_location_based_intercept_alerts(
    latitude: Optional[float] = Query(None, description="Center latitude for location-based alerts"),
    longitude: Optional[float] = Query(None, description="Center longitude for location-based alerts"),
    radius_km: float = Query(50.0, description="Search radius in kilometers", ge=1.0, le=200.0),
    hours: int = Query(24, description="Hours of history to include", ge=1, le=168),
    current_user: User = Depends(require_intelligence_role),
    db: AsyncSession = Depends(get_db),
):
    """
    Get INTERCEPT alerts within a geographic area.
    
    Used by Web Intelligence to show relevant alerts based on map location or agency area.
    """
    if not latitude or not longitude:
        raise HTTPException(
            status_code=400, 
            detail="Latitude and longitude are required for location-based alerts"
        )
    
    try:
        alerts = await get_intercept_alerts_by_location(
            db=db,
            user=current_user,
            latitude=latitude,
            longitude=longitude,
            radius_km=radius_km,
            hours=hours
        )
        
        return alerts
        
    except Exception as e:
        logger.error(f"Error fetching location-based alerts: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to fetch location-based alerts"
        )


@router.get("/nearby-agents/{intercept_event_id}", response_model=List[dict])
async def get_nearby_agents_for_intercept(
    intercept_event_id: UUID,
    radius_km: float = Query(25.0, description="Search radius in kilometers", ge=1.0, le=100.0),
    current_user: User = Depends(require_intelligence_role),
    db: AsyncSession = Depends(get_db),
):
    """
    Get nearby field agents for a specific INTERCEPT event.
    
    Helps intelligence analysts coordinate field response.
    """
    from app.services.location_interception_service import determine_location_context
    from app.db.base import InterceptEvent, VehicleObservation
    from sqlalchemy import select
    from geoalchemy2.shape import to_shape
    
    # Get the intercept event with observation
    query = (
        select(InterceptEvent, VehicleObservation)
        .join(VehicleObservation, VehicleObservation.id == InterceptEvent.observation_id)
        .where(InterceptEvent.id == intercept_event_id)
    )
    
    result = await db.execute(query)
    event_data = result.first()
    
    if not event_data:
        raise HTTPException(status_code=404, detail="INTERCEPT event not found")
    
    intercept_event, observation = event_data
    
    # Check agency permissions
    if current_user.role != UserRole.ADMIN and observation.agency_id != current_user.agency_id:
        raise HTTPException(status_code=403, detail="No permission to access this event")
    
    try:
        # Get location context and nearby agents
        location_context = await determine_location_context(db, observation)
        
        # Filter agents by requested radius
        nearby_agents = [
            {**agent, "within_radius": agent["distance_km"] <= radius_km}
            for agent in location_context.nearby_agents
            if agent["distance_km"] <= radius_km
        ]
        
        return nearby_agents
        
    except Exception as e:
        logger.error(f"Error fetching nearby agents for intercept {intercept_event_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to fetch nearby agents"
        )


@router.get("/alert-summary", response_model=dict)
async def get_location_interception_summary(
    agency_id: Optional[UUID] = Query(None, description="Filter by agency (admin only)"),
    hours: int = Query(24, description="Hours of history to analyze", ge=1, le=168),
    current_user: User = Depends(require_intelligence_role),
    db: AsyncSession = Depends(get_db),
):
    """
    Get summary statistics for location-based INTERCEPT alerts.
    
    Provides analytics on alert distribution and agent response patterns.
    """
    from sqlalchemy import func, and_, desc
    from app.db.base import InterceptEvent, VehicleObservation, Agency
    from datetime import datetime, timedelta
    from geoalchemy2.shape import to_shape
    
    start_time = datetime.utcnow() - timedelta(hours=hours)
    
    # Build base query
    query = (
        select(
            InterceptEvent.recommendation,
            InterceptEvent.priority_level,
            func.count(InterceptEvent.id).label("count"),
            func.avg(InterceptEvent.intercept_score).label("avg_score")
        )
        .join(VehicleObservation, VehicleObservation.id == InterceptEvent.observation_id)
        .where(
            and_(
                InterceptEvent.created_at >= start_time,
                InterceptEvent.recommendation.in_(["APPROACH", "MONITOR"])
            )
        )
        .group_by(InterceptEvent.recommendation, InterceptEvent.priority_level)
    )
    
    # Apply agency filter
    if current_user.role == UserRole.ADMIN and agency_id:
        query = query.where(VehicleObservation.agency_id == agency_id)
    elif current_user.role != UserRole.ADMIN:
        query = query.where(VehicleObservation.agency_id == current_user.agency_id)
    
    # Execute query
    result = await db.execute(query)
    stats = result.all()
    
    # Format response
    summary = {
        "time_window_hours": hours,
        "total_alerts": sum(stat.count for stat in stats),
        "by_recommendation": {},
        "by_priority": {
            "high": {"count": 0, "avg_score": 0.0},
            "medium": {"count": 0, "avg_score": 0.0},
            "low": {"count": 0, "avg_score": 0.0}
        },
        "generated_at": datetime.utcnow().isoformat()
    }
    
    for stat in stats:
        # By recommendation
        if stat.recommendation not in summary["by_recommendation"]:
            summary["by_recommendation"][stat.recommendation] = {
                "count": 0,
                "avg_score": 0.0
            }
        
        summary["by_recommendation"][stat.recommendation]["count"] += stat.count
        summary["by_recommendation"][stat.recommendation]["avg_score"] = stat.avg_score
        
        # By priority
        if stat.priority_level in summary["by_priority"]:
            summary["by_priority"][stat.priority_level]["count"] += stat.count
            summary["by_priority"][stat.priority_level]["avg_score"] = stat.avg_score
    
    return summary
