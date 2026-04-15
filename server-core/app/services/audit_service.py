"""
F.A.R.O. Audit service helpers.
"""
from __future__ import annotations

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import AuditLog, User


async def log_audit_event(
    db: AsyncSession,
    *,
    actor: User | None,
    action: str,
    resource_type: str,
    resource_id,
    details: dict[str, Any] | None = None,
    justification: str | None = None,
) -> AuditLog:
    entry = AuditLog(
        user_id=actor.id if actor else None,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        details=details,
        justification=justification,
    )
    db.add(entry)
    await db.flush()
    return entry
