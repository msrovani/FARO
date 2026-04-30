"""
F.A.R.O. Alert History API - Endpoint para histórico de alertas.
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_db
from app.services.alert_history_service import alert_history_service


router = APIRouter()


# ============================================================================
# Schemas
# ============================================================================


class AlertHistoryResponse(BaseModel):
    id: str
    alert_name: str
    alert_group: str
    fired_at: datetime
    resolved_at: Optional[datetime]
    severity: str
    urgency: str
    message: Optional[str]
    insight: Optional[str]
    possible_causes: Optional[str]
    solutions: Optional[str]
    labels: dict
    annotations: dict
    acknowledged: bool
    acknowledged_at: Optional[datetime]
    acknowledged_by: Optional[str]
    ttl_days: int
    
    class Config:
        from_attributes = True


class AlertStatsResponse(BaseModel):
    total_alerts: int
    by_severity: dict
    by_group: dict
    unacknowledged: int
    period_days: int


class AcknowledgeRequest(BaseModel):
    acknowledged_by: str


# ============================================================================
# Endpoints
# ============================================================================


@router.get("/history", response_model=list[AlertHistoryResponse])
async def get_alert_history(
    alert_group: Optional[str] = Query(None, description="Filter by alert group"),
    severity: Optional[str] = Query(None, description="Filter by severity"),
    start_date: Optional[str] = Query(None, description="Start date (ISO format)"),
    end_date: Optional[str] = Query(None, description="End date (ISO format)"),
    acknowledged: Optional[bool] = Query(None, description="Filter by acknowledged status"),
    limit: int = Query(100, le=500, description="Max results"),
    offset: int = Query(0, description="Offset for pagination"),
    db: AsyncSession = Depends(get_db),
):
    """Get alert history with filters."""
    # Parse dates
    start = None
    end = None
    if start_date:
        try:
            start = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
        except ValueError:
            pass
    if end_date:
        try:
            end = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
        except ValueError:
            pass
    
    alerts, total = await alert_history_service.get_alerts(
        db=db,
        alert_group=alert_group,
        severity=severity,
        start_date=start,
        end_date=end,
        acknowledged=acknowledged,
        limit=limit,
        offset=offset,
    )
    
    return alerts


@router.get("/history/stats", response_model=AlertStatsResponse)
async def get_alert_stats(
    days: int = Query(30, le=365, description="Period in days"),
    db: AsyncSession = Depends(get_db),
):
    """Get alert statistics."""
    stats = await alert_history_service.get_alert_stats(db=db, days=days)
    return stats


@router.get("/history/groups")
async def get_alert_groups(
    db: AsyncSession = Depends(get_db),
):
    """Get all unique alert groups."""
    groups = await alert_history_service.get_alert_groups(db=db)
    return {"groups": groups}


@router.post("/history/{alert_id}/acknowledge")
async def acknowledge_alert(
    alert_id: str,
    body: AcknowledgeRequest,
    db: AsyncSession = Depends(get_db),
):
    """Acknowledge an alert."""
    alert = await alert_history_service.acknowledge_alert(
        db=db,
        alert_id=alert_id,
        acknowledged_by=body.acknowledged_by,
    )
    
    if not alert:
        return {"success": False, "error": "Alert not found"}
    
    return {"success": True, "alert_id": alert_id}


@router.post("/history/cleanup")
async def cleanup_alerts(
    days: int = Query(90, le=365, description="Delete alerts older than X days"),
    db: AsyncSession = Depends(get_db),
):
    """Clean up old resolved alerts."""
    deleted = await alert_history_service.cleanup_old_alerts(db=db, days=days)
    return {"deleted": deleted, "days_older_than": days}


# Webhook endpoint for Prometheus AlertManager
@router.post("/webhook/prometheus")
async def prometheus_webhook(
    alerts: dict,
    db: AsyncSession = Depends(get_db),
):
    """Receive alerts from Prometheus AlertManager."""
    import logging
    logger = logging.getLogger(__name__)
    
    processed = 0
    errors = 0
    
    # Handle both firing and resolved alerts
    for alert in alerts.get("alerts", []):
        try:
            status = alert.get("status", {})
            labels = alert.get("labels", {})
            annotations = alert.get("annotations", {})
            
            alert_name = labels.get("alertname", "unknown")
            alert_group = labels.get("group", "default")
            severity = labels.get("severity", "warning")
            
            if status.get("state") == "firing":
                await alert_history_service.record_alert(
                    db=db,
                    alert_name=alert_name,
                    alert_group=alert_group,
                    severity=severity,
                    urgency=severity,  # Map severity to urgency
                    message=annotations.get("description", ""),
                    insight=annotations.get("insight", ""),
                    possible_causes=annotations.get("possible_causes", ""),
                    solutions=annotations.get("solutions", ""),
                    labels=labels,
                    annotations=annotations,
                )
                processed += 1
            elif status.get("state") == "resolved":
                # Find and resolve the alert
                fired_at = alert.get("fired_at")
                if fired_at:
                    await alert_history_service.resolve_alert(
                        db=db,
                        alert_name=alert_name,
                        fired_at=fired_at,
                    )
                    
        except Exception as e:
            logger.error(f"Error processing alert: {e}")
            errors += 1
    
    return {
        "success": True,
        "processed": processed,
        "errors": errors,
    }