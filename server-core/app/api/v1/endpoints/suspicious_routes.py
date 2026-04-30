"""
F.A.R.O. Suspicious Routes API - Manual route registration for intelligence analysis.
"""
from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_db
from app.api.v1.endpoints.auth import get_current_user
from app.db.base import User, UserRole
from app.schemas.suspicious_route import (
    SuspiciousRouteCreate,
    SuspiciousRouteUpdate,
    SuspiciousRouteResponse,
    SuspiciousRouteMatchRequest,
    SuspiciousRouteMatchResponse,
    SuspiciousRouteListResponse,
    RouteApprovalRequest,
)
from app.services.audit_service import log_audit_event
from app.services.suspicious_route_service import (
    create_suspicious_route,
    get_suspicious_route,
    list_suspicious_routes,
    update_suspicious_route,
    delete_suspicious_route,
    check_route_match,
    approve_route,
    route_to_response,
)

router = APIRouter()


def require_intelligence_role(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role not in {UserRole.INTELLIGENCE, UserRole.SUPERVISOR, UserRole.ADMIN}:
        raise HTTPException(status_code=403, detail="Acesso de inteligencia requerido")
    if current_user.role != UserRole.ADMIN and current_user.agency_id is None:
        raise HTTPException(status_code=403, detail="Usuario sem vinculacao de agencia")
    return current_user


@router.post("/suspicious-routes", response_model=SuspiciousRouteResponse)
async def create_suspicious_route_endpoint(
    route_data: SuspiciousRouteCreate,
    current_user: User = Depends(require_intelligence_role),
    db: AsyncSession = Depends(get_db),
):
    """Create a new suspicious route for intelligence analysis."""
    if current_user.agency_id is None:
        raise HTTPException(status_code=403, detail="Usuario sem vinculacao de agencia")
    
    route = await create_suspicious_route(
        db,
        route_data=route_data,
        agency_id=current_user.agency_id,
        created_by=current_user.id,
    )
    
    await log_audit_event(
        db,
        actor=current_user,
        action="create_suspicious_route",
        resource_type="suspicious_route",
        resource_id=route.id,
        details={"route_name": route.name, "crime_type": route.crime_type},
    )
    
    return route_to_response(route)


@router.get("/suspicious-routes", response_model=SuspiciousRouteListResponse)
async def list_suspicious_routes_endpoint(
    crime_type: str | None = None,
    risk_level: str | None = None,
    approval_status: str | None = None,
    is_active: bool | None = None,
    page: int = 1,
    page_size: int = 50,
    current_user: User = Depends(require_intelligence_role),
    db: AsyncSession = Depends(get_db),
):
    """List suspicious routes with filters."""
    if current_user.agency_id is None:
        raise HTTPException(status_code=403, detail="Usuario sem vinculacao de agencia")
    
    offset = (page - 1) * page_size
    routes, total_count = await list_suspicious_routes(
        db,
        agency_id=current_user.agency_id,
        crime_type=crime_type,
        risk_level=risk_level,
        approval_status=approval_status,
        is_active=is_active,
        offset=offset,
        limit=page_size,
    )
    
    return SuspiciousRouteListResponse(
        routes=[route_to_response(route) for route in routes],
        total_count=total_count,
        page=page,
        page_size=page_size,
    )


@router.get("/suspicious-routes/{route_id}", response_model=SuspiciousRouteResponse)
async def get_suspicious_route_endpoint(
    route_id: UUID,
    current_user: User = Depends(require_intelligence_role),
    db: AsyncSession = Depends(get_db),
):
    """Get details of a specific suspicious route."""
    if current_user.agency_id is None:
        raise HTTPException(status_code=403, detail="Usuario sem vinculacao de agencia")
    
    route = await get_suspicious_route(db, route_id, current_user.agency_id)
    if not route:
        raise HTTPException(status_code=404, detail="Rota suspeita nao encontrada")
    
    return route_to_response(route)


@router.put("/suspicious-routes/{route_id}", response_model=SuspiciousRouteResponse)
async def update_suspicious_route_endpoint(
    route_id: UUID,
    update_data: SuspiciousRouteUpdate,
    current_user: User = Depends(require_intelligence_role),
    db: AsyncSession = Depends(get_db),
):
    """Update a suspicious route."""
    if current_user.agency_id is None:
        raise HTTPException(status_code=403, detail="Usuario sem vinculacao de agencia")
    
    route = await update_suspicious_route(
        db,
        route_id=route_id,
        agency_id=current_user.agency_id,
        update_data=update_data,
    )
    if not route:
        raise HTTPException(status_code=404, detail="Rota suspeita nao encontrada")
    
    await log_audit_event(
        db,
        actor=current_user,
        action="update_suspicious_route",
        resource_type="suspicious_route",
        resource_id=route.id,
        details={"route_name": route.name},
    )
    
    return route_to_response(route)


@router.delete("/suspicious-routes/{route_id}")
async def delete_suspicious_route_endpoint(
    route_id: UUID,
    current_user: User = Depends(require_intelligence_role),
    db: AsyncSession = Depends(get_db),
):
    """Deactivate (soft delete) a suspicious route."""
    if current_user.agency_id is None:
        raise HTTPException(status_code=403, detail="Usuario sem vinculacao de agencia")
    
    success = await delete_suspicious_route(db, route_id, current_user.agency_id)
    if not success:
        raise HTTPException(status_code=404, detail="Rota suspeita nao encontrada")
    
    await log_audit_event(
        db,
        actor=current_user,
        action="delete_suspicious_route",
        resource_type="suspicious_route",
        resource_id=route_id,
        details={},
    )
    
    return {"message": "Rota desativada com sucesso"}


@router.post("/suspicious-routes/{route_id}/approve")
async def approve_suspicious_route_endpoint(
    route_id: UUID,
    approval_data: RouteApprovalRequest,
    current_user: User = Depends(require_intelligence_role),
    db: AsyncSession = Depends(get_db),
):
    """Approve or reject a suspicious route."""
    if current_user.agency_id is None:
        raise HTTPException(status_code=403, detail="Usuario sem vinculacao de agencia")
    
    route = await approve_route(
        db,
        route_id=route_id,
        agency_id=current_user.agency_id,
        approved_by=current_user.id,
        approval_status=approval_data.approval_status,
        justification=approval_data.justification,
    )
    if not route:
        raise HTTPException(status_code=404, detail="Rota suspeita nao encontrada")
    
    await log_audit_event(
        db,
        actor=current_user,
        action=f"approve_route_{approval_data.approval_status}",
        resource_type="suspicious_route",
        resource_id=route.id,
        details={"route_name": route.name, "status": approval_data.approval_status},
    )
    
    return route_to_response(route)


@router.post("/suspicious-routes/match", response_model=SuspiciousRouteMatchResponse)
async def check_suspicious_route_match_endpoint(
    match_request: SuspiciousRouteMatchRequest,
    current_user: User = Depends(require_intelligence_role),
    db: AsyncSession = Depends(get_db),
):
    """Check if an observation matches any suspicious route using PostGIS."""
    if current_user.agency_id is None:
        raise HTTPException(status_code=403, detail="Usuario sem vinculacao de agencia")
    
    match_result = await check_route_match(
        db,
        match_request=match_request,
        agency_id=current_user.agency_id,
    )
    
    # Log alert if triggered
    if match_result.alert_triggered:
        await log_audit_event(
            db,
            actor=current_user,
            action="suspicious_route_alert",
            resource_type="observation",
            resource_id=match_request.observation_id,
            details={
                "plate_number": match_request.plate_number,
                "matched_routes": match_result.matched_routes,
            },
        )
    
    return match_result
