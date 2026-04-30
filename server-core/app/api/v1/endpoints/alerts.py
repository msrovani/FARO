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
from app.schemas.alert_rules import (
    AlertRuleCreate,
    AlertRuleUpdate,
    AlertRuleResponse,
    AlertRuleListResponse,
    AlertRuleStatsResponse,
)
from app.services.alert_service import (
    check_observation_alerts,
    get_aggregated_alerts,
    check_suspicious_route_recurrence_alerts,
)
from app.services.alert_rule_service import (
    create_alert_rule,
    get_alert_rule,
    list_alert_rules,
    update_alert_rule,
    delete_alert_rule,
    get_alert_rule_stats,
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


@router.post("/alerts/{alert_id}/acknowledge")
async def acknowledge_alert_endpoint(
    alert_id: str,
    current_user: User = Depends(require_intelligence_role),
    db: AsyncSession = Depends(get_db),
):
    """Acknowledge an alert (compatibility endpoint - redirects to monitoring)."""
    # Import the actual function from alert_history
    from app.api.v1.endpoints.alert_history import acknowledge_alert
    return await acknowledge_alert(alert_id, current_user, db)


@router.get("/alerts/rules", response_model=AlertRuleListResponse)
async def list_alert_rules_endpoint(
    rule_type: Optional[str] = None,
    is_active: Optional[bool] = None,
    severity: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    current_user: User = Depends(require_intelligence_role),
    db: AsyncSession = Depends(get_db),
):
    """List all alert rules with optional filters."""
    from app.schemas.alert_rules import AlertRuleTypeEnum, AlertRuleSeverityEnum
    
    # Convert string to enum if provided
    rule_type_enum = AlertRuleTypeEnum(rule_type) if rule_type else None
    severity_enum = AlertRuleSeverityEnum(severity) if severity else None
    
    # Non-admin users can only see rules for their agency or global rules
    agency_id = None if current_user.role == UserRole.ADMIN else current_user.agency_id
    
    rules, total = await list_alert_rules(
        db,
        agency_id=agency_id,
        rule_type=rule_type_enum,
        is_active=is_active,
        severity=severity_enum,
        limit=limit,
        offset=offset,
    )
    
    return AlertRuleListResponse(total=total, rules=rules)


@router.post("/alerts/rules", response_model=AlertRuleResponse)
async def create_alert_rule_endpoint(
    rule_data: AlertRuleCreate,
    current_user: User = Depends(require_intelligence_role),
    db: AsyncSession = Depends(get_db),
):
    """Create a new alert rule."""
    # Non-admin users can only create rules for their agency
    agency_id = None if current_user.role == UserRole.ADMIN else current_user.agency_id
    
    if agency_id is None and current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Apenas admins podem criar regras globais")
    
    rule = await create_alert_rule(
        db,
        rule_data=rule_data,
        created_by=current_user.id,
        agency_id=agency_id,
    )
    
    return rule


@router.get("/alerts/rules/{rule_id}", response_model=AlertRuleResponse)
async def get_alert_rule_endpoint(
    rule_id: str,
    current_user: User = Depends(require_intelligence_role),
    db: AsyncSession = Depends(get_db),
):
    """Get a specific alert rule by ID."""
    from uuid import UUID
    
    rule = await get_alert_rule(db, UUID(rule_id))
    
    if not rule:
        raise HTTPException(status_code=404, detail="Regra não encontrada")
    
    # Check permission
    if current_user.role != UserRole.ADMIN:
        if rule.agency_id != current_user.agency_id and rule.agency_id is not None:
            raise HTTPException(status_code=403, detail="Acesso negado a esta regra")
    
    return rule


@router.patch("/alerts/rules/{rule_id}", response_model=AlertRuleResponse)
async def update_alert_rule_endpoint(
    rule_id: str,
    rule_data: AlertRuleUpdate,
    current_user: User = Depends(require_intelligence_role),
    db: AsyncSession = Depends(get_db),
):
    """Update an existing alert rule."""
    from uuid import UUID
    
    # First check if rule exists and user has permission
    existing_rule = await get_alert_rule(db, UUID(rule_id))
    
    if not existing_rule:
        raise HTTPException(status_code=404, detail="Regra não encontrada")
    
    # Check permission
    if current_user.role != UserRole.ADMIN:
        if existing_rule.agency_id != current_user.agency_id and existing_rule.agency_id is not None:
            raise HTTPException(status_code=403, detail="Acesso negado a esta regra")
    
    rule = await update_alert_rule(db, UUID(rule_id), rule_data)
    
    return rule


@router.delete("/alerts/rules/{rule_id}")
async def delete_alert_rule_endpoint(
    rule_id: str,
    current_user: User = Depends(require_intelligence_role),
    db: AsyncSession = Depends(get_db),
):
    """Delete an alert rule."""
    from uuid import UUID
    
    # First check if rule exists and user has permission
    existing_rule = await get_alert_rule(db, UUID(rule_id))
    
    if not existing_rule:
        raise HTTPException(status_code=404, detail="Regra não encontrada")
    
    # Check permission
    if current_user.role != UserRole.ADMIN:
        if existing_rule.agency_id != current_user.agency_id and existing_rule.agency_id is not None:
            raise HTTPException(status_code=403, detail="Acesso negado a esta regra")
    
    deleted = await delete_alert_rule(db, UUID(rule_id))
    
    if not deleted:
        raise HTTPException(status_code=404, detail="Regra não encontrada")
    
    return {"message": "Regra deletada com sucesso"}


@router.get("/alerts/rules/stats", response_model=AlertRuleStatsResponse)
async def get_alert_rule_stats_endpoint(
    current_user: User = Depends(require_intelligence_role),
    db: AsyncSession = Depends(get_db),
):
    """Get statistics about alert rules."""
    # Non-admin users can only see stats for their agency
    agency_id = None if current_user.role == UserRole.ADMIN else current_user.agency_id
    
    stats = await get_alert_rule_stats(db, agency_id=agency_id)
    
    return stats


@router.get("/alerts/stats")
async def get_alert_stats(
    current_user: User = Depends(require_intelligence_role),
    db: AsyncSession = Depends(get_db),
):
    """Get alert statistics (compatibility endpoint - redirects to monitoring)."""
    # Import the actual function from alert_history
    from app.api.v1.endpoints.alert_history import get_alert_stats
    return await get_alert_stats(current_user, db)
