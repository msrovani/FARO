"""
F.A.R.O. Audit API - trilha de auditoria e governanca.
"""
from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_db
from app.api.v1.endpoints.auth import get_current_user
from app.db.base import AuditLog, User, UserRole
from app.schemas.analytics import AuditLogResponse
from app.schemas.common import PaginationParams

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
    pagination: PaginationParams = Depends(),
    current_user: User = Depends(require_governance_role),
    db: AsyncSession = Depends(get_db),
):
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
