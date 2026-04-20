"""
F.A.R.O. Audit API - trilha de auditoria e governanca.
"""
from __future__ import annotations

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_db
from app.api.v1.endpoints.auth import get_current_user
from app.db.base import AuditLog, User, UserRole, AgentLocationLog
from app.schemas.analytics import AuditLogResponse, AgentLocationResponse, GeolocationAuditFilter
from app.schemas.common import PaginationParams
from app.services.report_service import report_service
from fastapi.responses import StreamingResponse
from geoalchemy2.functions import ST_X, ST_Y
import io

router = APIRouter()


def require_governance_role(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role not in {UserRole.INTELLIGENCE, UserRole.SUPERVISOR, UserRole.ADMIN}:
        raise HTTPException(status_code=403, detail="Acesso de auditoria restrito")
    return current_user


@router.get("/logs", response_model=list[AuditLogResponse])
async def list_audit_logs(
    action: str | None = None,
    resource_type: str | None = None,
    resource_id: UUID | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    ttl_days: int = 30,
    pagination: PaginationParams = Depends(),
    current_user: User = Depends(require_governance_role),
    db: AsyncSession = Depends(get_db),
):
    from datetime import timedelta
    
    # Calculate date range from TTL if not provided
    query_start = None
    if start_date:
        try:
            query_start = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
        except:
            pass
    elif ttl_days:
        query_start = datetime.utcnow() - timedelta(days=ttl_days)
    
    query_end = None
    if end_date:
        try:
            query_end = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
        except:
            pass
    
    query = (
        select(AuditLog, User)
        .outerjoin(User, User.id == AuditLog.user_id)
        .order_by(desc(AuditLog.created_at))
        .offset(pagination.offset)
        .limit(pagination.page_size)
    )
    if action:
        query = query.where(AuditLog.action == action)
    if resource_type:
        query = query.where(AuditLog.resource_type == resource_type)
    if resource_id:
        query = query.where(AuditLog.resource_id == resource_id)
    if query_start:
        query = query.where(AuditLog.created_at >= query_start)
    if query_end:
        query = query.where(AuditLog.created_at <= query_end)

    rows = (await db.execute(query)).all()
    return [
        AuditLogResponse(
            id=entry.id,
            actor_user_id=entry.user_id,
            actor_name=user.full_name if user else None,
            action=entry.action,
            entity_type=entry.resource_type,
            entity_id=entry.resource_id,
            details=entry.details,
            justification=entry.justification,
            created_at=entry.created_at,
        )
        for entry, user in rows
    ]


@router.get("/geolocation", response_model=list[AgentLocationResponse])
async def search_agent_location_history(
    agent_id: UUID | None = None,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    min_accuracy: float | None = None,
    current_user: User = Depends(require_governance_role),
    db: AsyncSession = Depends(get_db),
):
    """Search historical geolocation logs for agents (ALI/ARI/DINT)."""
    query = (
        select(AgentLocationLog, User.full_name)
        .join(User, User.id == AgentLocationLog.agent_id)
        .order_by(desc(AgentLocationLog.recorded_at))
    )
    
    if agent_id:
        query = query.where(AgentLocationLog.agent_id == agent_id)
    if start_date:
        query = query.where(AgentLocationLog.recorded_at >= start_date)
    if end_date:
        query = query.where(AgentLocationLog.recorded_at <= end_date)
        
    rows = (await db.execute(query)).all()
    
    return [
        AgentLocationResponse(
            id=entry.id,
            agent_id=entry.agent_id,
            agent_name=agent_name,
            location={
                "latitude": (await db.scalar(select(ST_Y(entry.location)))),
                "longitude": (await db.scalar(select(ST_X(entry.location))))
            },
            recorded_at=entry.recorded_at,
            connectivity_status=entry.connectivity_status,
            battery_level=entry.battery_level,
            agency_id=current_user.agency_id # Simplifying for now
        )
        for entry, agent_name in rows
    ]


@router.get("/geolocation/export/{format}")
async def export_certified_geotrail(
    format: str,
    agent_id: UUID,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    current_user: User = Depends(require_governance_role),
    db: AsyncSession = Depends(get_db),
):
    """Generates a certified report (PDF/DOCX/XLSX) for geolocation audit."""
    if format not in {"pdf", "docx", "xlsx"}:
        raise HTTPException(status_code=400, detail="Formato nao suportado")

    # Reuse history search logic (optimized for export)
    # Note: In production, we'd fetch in a single query with ST_AsText or similar
    history = await search_agent_location_history(
        agent_id=agent_id, 
        start_date=start_date, 
        end_date=end_date, 
        current_user=current_user, 
        db=db
    )
    
    if not history:
        raise HTTPException(status_code=404, detail="Nenhum dado encontrado para os filtros")

    # Data transformation for service
    data = [item.model_dump() for item in history]
    agent_name = history[0].agent_name
    
    # Generate file
    if format == "xlsx":
        content = await report_service.generate_xlsx(data, agent_name)
        media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    elif format == "pdf":
        content = await report_service.generate_pdf(data, agent_name, {"start_date": start_date, "end_date": end_date})
        media_type = "application/pdf"
    else: # docx
        content = await report_service.generate_docx(data, agent_name)
        media_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"

    # Certification & Audit Trail
    file_hash = report_service.calculate_hash(content)
    await report_service.create_audit_entry(
        db=db,
        user_id=current_user.id,
        action=f"Exportacao Geotrail {format.upper()}",
        file_hash=file_hash,
        filters={"agent_id": str(agent_id), "start_date": str(start_date), "end_date": str(end_date)}
    )

    return StreamingResponse(
        io.BytesIO(content),
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename=geotrail_certified_{agent_id}.{format}"}
    )
