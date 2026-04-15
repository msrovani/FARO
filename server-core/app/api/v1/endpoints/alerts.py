"""
F.A.R.O. Alerts API - Automatic alert generation and management.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_db
from app.api.v1.endpoints.auth import get_current_user
from app.db.base import User, UserRole
from app.schemas.alerts import (
    AggregatedAlertsRequest,
    AggregatedAlertsResponse,
    ObservationAlertCheckRequest,
    ObservationAlertCheckResponse,
)
from app.services.alert_service import (
    check_observation_alerts,
    get_aggregated_alerts,
    check_suspicious_route_recurrence_alerts,
)
from app.schemas.common import GeolocationPoint

router = APIRouter()


def require_intelligence_role(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role not in {UserRole.INTELLIGENCE, UserRole.SUPERVISOR, UserRole.ADMIN}:
        raise HTTPException(status_code=403, detail="Acesso de inteligencia requerido")
    if current_user.role != UserRole.ADMIN and current_user.agency_id is None:
        raise HTTPException(status_code=403, detail="Usuario sem vinculacao de agencia")
    return current_user


@router.post("/alerts/check-observation", response_model=ObservationAlertCheckResponse)
async def check_observation_alerts_endpoint(
    check_request: ObservationAlertCheckRequest,
    current_user: User = Depends(require_intelligence_role),
    db: AsyncSession = Depends(get_db),
):
    """Check all alert conditions for a new observation."""
    if current_user.agency_id is None:
        raise HTTPException(status_code=403, detail="Usuario sem vinculacao de agencia")
    
    location = GeolocationPoint(
        latitude=check_request.location[0],
        longitude=check_request.location[1],
    )
    
    alerts = await check_observation_alerts(
        db,
        observation_id=check_request.observation_id,
        plate_number=check_request.plate_number,
        location=location,
        observed_at=check_request.observed_at,
        agency_id=current_user.agency_id,
    )
    
    return ObservationAlertCheckResponse(
        alerts=[
            {
                "alert_type": a.alert_type,
                "plate_number": a.plate_number,
                "severity": a.severity,
                "confidence": a.confidence,
                "details": a.details,
                "triggered_at": a.triggered_at.isoformat(),
                "requires_review": a.requires_review,
            }
            for a in alerts
        ]
    )


@router.post("/alerts/aggregated", response_model=AggregatedAlertsResponse)
async def get_aggregated_alerts_endpoint(
    request: AggregatedAlertsRequest,
    current_user: User = Depends(require_intelligence_role),
    db: AsyncSession = Depends(get_db),
):
    """Get aggregated alert summary for the agency."""
    if current_user.agency_id is None:
        raise HTTPException(status_code=403, detail="Usuario sem vinculacao de agencia")
    
    result = await get_aggregated_alerts(
        db,
        agency_id=current_user.agency_id,
        alert_type=request.alert_type,
        severity=request.severity,
        limit=request.limit,
    )
    
    return AggregatedAlertsResponse(
        total_alerts=result["total_alerts"],
        alerts=result["alerts"],
        summary=result["summary"],
    )


@router.post("/alerts/recurrence-check")
async def check_suspicious_route_recurrence_alerts_endpoint(
    hours: int = 24,
    current_user: User = Depends(require_intelligence_role),
    db: AsyncSession = Depends(get_db),
):
    """Check for plates that have matched suspicious routes multiple times recently."""
    if current_user.agency_id is None:
        raise HTTPException(status_code=403, detail="Usuario sem vinculacao de agencia")
    
    alerts = await check_suspicious_route_recurrence_alerts(
        db,
        agency_id=current_user.agency_id,
        hours=hours,
    )
    
    return {
        "total_alerts": len(alerts),
        "alerts": [
            {
                "alert_type": a.alert_type,
                "plate_number": a.plate_number,
                "severity": a.severity,
                "confidence": a.confidence,
                "details": a.details,
                "triggered_at": a.triggered_at.isoformat(),
                "requires_review": a.requires_review,
            }
            for a in alerts
        ],
    }
