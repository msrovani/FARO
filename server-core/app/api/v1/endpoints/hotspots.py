"""
F.A.R.O. Hotspots API - Criminal hotspot analysis.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_db
from app.api.v1.endpoints.auth import get_current_user
from app.db.base import User, UserRole
from app.schemas.hotspot import (
    HotspotAnalysisRequest,
    HotspotAnalysisResponse,
    HotpointTimelineRequest,
    HotspotTimelineResponse,
    HotspotPlatesRequest,
    HotspotPlatesResponse,
)
from app.services.hotspot_analysis_service import (
    analyze_hotspots,
    get_hotspot_timeline,
    get_hotspot_plates,
)

router = APIRouter()


def require_intelligence_role(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role not in {UserRole.INTELLIGENCE, UserRole.SUPERVISOR, UserRole.ADMIN}:
        raise HTTPException(status_code=403, detail="Acesso de inteligencia requerido")
    if current_user.role != UserRole.ADMIN and current_user.agency_id is None:
        raise HTTPException(status_code=403, detail="Usuario sem vinculacao de agencia")
    return current_user


@router.post("/hotspots/analyze", response_model=HotspotAnalysisResponse)
async def analyze_hotspots_endpoint(
    analysis_request: HotspotAnalysisRequest,
    current_user: User = Depends(require_intelligence_role),
    db: AsyncSession = Depends(get_db),
):
    """Analyze criminal hotspots based on observation density."""
    if current_user.agency_id is None:
        raise HTTPException(status_code=403, detail="Usuario sem vinculacao de agencia")
    
    result = await analyze_hotspots(
        db,
        agency_id=current_user.agency_id,
        start_date=analysis_request.start_date,
        end_date=analysis_request.end_date,
        cluster_radius_meters=analysis_request.cluster_radius_meters,
        min_points_per_cluster=analysis_request.min_points_per_cluster,
    )
    
    return HotspotAnalysisResponse(
        hotspots=[
            {
                "latitude": h.latitude,
                "longitude": h.longitude,
                "observation_count": h.observation_count,
                "suspicion_count": h.suspicion_count,
                "unique_plates": h.unique_plates,
                "radius_meters": h.radius_meters,
                "intensity_score": h.intensity_score,
            }
            for h in result.hotspots
        ],
        total_observations=result.total_observations,
        total_suspicions=result.total_suspicions,
        analysis_period_days=result.analysis_period_days,
        cluster_radius_meters=result.cluster_radius_meters,
        min_points_per_cluster=result.min_points_per_cluster,
    )


@router.post("/hotspots/timeline", response_model=HotspotTimelineResponse)
async def get_hotspot_timeline_endpoint(
    timeline_request: HotspotTimelineRequest,
    current_user: User = Depends(require_intelligence_role),
    db: AsyncSession = Depends(get_db),
):
    """Get temporal distribution of observations around a location."""
    if current_user.agency_id is None:
        raise HTTPException(status_code=403, detail="Usuario sem vinculacao de agencia")
    
    result = await get_hotspot_timeline(
        db,
        agency_id=current_user.agency_id,
        latitude=timeline_request.latitude,
        longitude=timeline_request.longitude,
        radius_meters=timeline_request.radius_meters,
        days=timeline_request.days,
    )
    
    return HotspotTimelineResponse(
        hourly_data=result["hourly_data"],
        daily_pattern=result["daily_pattern"],
        total_observations=result["total_observations"],
        peak_hour=result["peak_hour"],
    )


@router.post("/hotspots/plates", response_model=HotspotPlatesResponse)
async def get_hotspot_plates_endpoint(
    plates_request: HotspotPlatesRequest,
    current_user: User = Depends(require_intelligence_role),
    db: AsyncSession = Depends(get_db),
):
    """Get most frequent plates observed in a hotspot area."""
    if current_user.agency_id is None:
        raise HTTPException(status_code=403, detail="Usuario sem vinculacao de agencia")
    
    plates = await get_hotspot_plates(
        db,
        agency_id=current_user.agency_id,
        latitude=plates_request.latitude,
        longitude=plates_request.longitude,
        radius_meters=plates_request.radius_meters,
        limit=plates_request.limit,
    )
    
    return HotspotPlatesResponse(plates=plates)
