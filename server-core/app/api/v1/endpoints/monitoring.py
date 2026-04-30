"""
Monitoring endpoints for Analytics Dashboard integration.

Provides endpoints for:
- Audit logs retrieval
- Alert history
- Alert statistics
"""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional, List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, desc, asc

from app.api.v1.deps import get_db
from app.db.base import (
    Alert, 
    AuditLog,
    User,
    VehicleObservation,
    SuspicionReport,
    IntelligenceReview,
    AlgorithmRun,
    AlgorithmType,
    UrgencyLevel
)

router = APIRouter()


@router.get("/audit/logs")
async def get_audit_logs(
    resource_type: Optional[str] = Query(None, description="Filter by resource type"),
    start_date: Optional[str] = Query(None, description="Start date (ISO format)"),
    end_date: Optional[str] = Query(None, description="End date (ISO format)"),
    ttl_days: str = Query("30", description="Days to look back (0 = no limit)"),
    page: str = Query("1", description="Page number"),
    page_size: str = Query("50", description="Items per page"),
    db: AsyncSession = Depends(get_db)
) -> dict:
    """
    Get audit logs from the database.
    
    Parameters:
    - resource_type: Filter by resource type (user, vehicle, alert, etc.)
    - start_date/end_date: Date range in ISO format
    - ttl_days: Number of days to look back (0 = no limit)
    - page/page_size: Pagination
    """
    try:
        # Parse pagination
        page_num = int(page)
        page_size_num = int(page_size)
        offset = (page_num - 1) * page_size_num
        
        # Calculate date range
        calculated_start = start_date
        days = int(ttl_days) if ttl_days.isdigit() else 30
        
        if days > 0:
            start_dt = datetime.utcnow() - timedelta(days=days)
            calculated_start = start_dt.isoformat()
        
        # Build query
        query = select(AuditLog)
        
        # Apply filters
        conditions = []
        
        if calculated_start:
            try:
                start_dt = datetime.fromisoformat(calculated_start.replace('Z', '+00:00'))
                conditions.append(AuditLog.created_at >= start_dt)
            except ValueError:
                pass  # Invalid date format, ignore
        
        if end_date:
            try:
                end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                conditions.append(AuditLog.created_at <= end_dt)
            except ValueError:
                pass  # Invalid date format, ignore
        
        if resource_type:
            conditions.append(AuditLog.resource_type == resource_type)
        
        if conditions:
            query = query.where(and_(*conditions))
        
        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_count = await db.scalar(count_query) or 0
        
        # Get paginated results
        query = query.order_by(desc(AuditLog.created_at))
        query = query.offset(offset).limit(page_size_num)
        
        result = await db.execute(query)
        logs = result.scalars().all()
        
        # Convert to dict
        logs_data = []
        for log in logs:
            logs_data.append({
                "id": str(log.id),
                "user_id": str(log.user_id) if log.user_id else None,
                "action": log.action,
                "resource_type": log.resource_type,
                "resource_id": str(log.resource_id) if log.resource_id else None,
                "details": log.details or {},
                "ip_address": log.ip_address,
                "user_agent": log.user_agent,
                "created_at": log.created_at.isoformat(),
                "ttl_days": int(ttl_days)
            })
        
        return {
            "data": logs_data,
            "total": total_count,
            "page": page_num,
            "page_size": page_size_num,
            "total_pages": (total_count + page_size_num - 1) // page_size_num,
            "server_available": True
        }
        
    except Exception as e:
        return {
            "error": "database_error",
            "message": f"Erro ao buscar logs: {str(e)}",
            "data": [],
            "server_available": False
        }


@router.get("/monitoring/history")
async def get_alert_history(
    alert_group: Optional[str] = Query(None, description="Filter by alert group"),
    severity: Optional[str] = Query(None, description="Filter by severity"),
    start_date: Optional[str] = Query(None, description="Start date (ISO format)"),
    end_date: Optional[str] = Query(None, description="End date (ISO format)"),
    acknowledged: Optional[bool] = Query(None, description="Filter by acknowledgment status"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    db: AsyncSession = Depends(get_db)
) -> dict:
    """
    Get alert history from the database.
    
    Parameters:
    - alert_group: Filter by alert group (watchlist, convoy, etc.)
    - severity: Filter by severity (critical, warning, info)
    - start_date/end_date: Date range in ISO format
    - acknowledged: Filter by acknowledgment status
    - limit/offset: Pagination
    """
    try:
        # Build query
        query = select(Alert)
        
        # Apply filters
        conditions = []
        
        if start_date:
            try:
                start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                conditions.append(Alert.created_at >= start_dt)
            except ValueError:
                pass
        
        if end_date:
            try:
                end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                conditions.append(Alert.created_at <= end_dt)
            except ValueError:
                pass
        
        if alert_group:
            conditions.append(Alert.alert_group == alert_group)
        
        if severity:
            conditions.append(Alert.severity == severity)
        
        if acknowledged is not None:
            conditions.append(Alert.acknowledged == acknowledged)
        
        if conditions:
            query = query.where(and_(*conditions))
        
        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_count = await db.scalar(count_query) or 0
        
        # Get paginated results
        query = query.order_by(desc(Alert.created_at))
        query = query.offset(offset).limit(limit)
        
        result = await db.execute(query)
        alerts = result.scalars().all()
        
        # Convert to dict
        alerts_data = []
        for alert in alerts:
            alerts_data.append({
                "id": str(alert.id),
                "alert_group": alert.alert_group,
                "title": alert.title,
                "message": alert.message,
                "severity": alert.severity,
                "urgency": alert.urgency,
                "status": alert.status,
                "acknowledged": alert.acknowledged,
                "acknowledged_by": str(alert.acknowledged_by) if alert.acknowledged_by else None,
                "acknowledged_at": alert.acknowledged_at.isoformat() if alert.acknowledged_at else None,
                "resolved_at": alert.resolved_at.isoformat() if alert.resolved_at else None,
                "created_at": alert.created_at.isoformat(),
                "updated_at": alert.updated_at.isoformat(),
                "metadata": alert.metadata or {}
            })
        
        return {
            "data": alerts_data,
            "total": total_count,
            "limit": limit,
            "offset": offset,
            "server_available": True
        }
        
    except Exception as e:
        return {
            "error": "database_error",
            "message": f"Erro ao buscar histórico: {str(e)}",
            "data": [],
            "server_available": False
        }


@router.get("/monitoring/history/stats")
async def get_alert_statistics(
    days: int = Query(30, ge=1, le=365, description="Number of days to look back"),
    db: AsyncSession = Depends(get_db)
) -> dict:
    """
    Get alert statistics for the specified period.
    
    Parameters:
    - days: Number of days to look back
    """
    try:
        # Calculate date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Get total alerts
        total_alerts = await db.scalar(
            select(func.count(Alert.id)).where(
                Alert.created_at >= start_date
            )
        ) or 0
        
        # Get alerts by severity
        severity_query = select(
            Alert.severity,
            func.count(Alert.id)
        ).where(
            Alert.created_at >= start_date
        ).group_by(Alert.severity)
        
        severity_result = await db.execute(severity_query)
        by_severity = dict(severity_result.all())
        
        # Get alerts by group
        group_query = select(
            Alert.alert_group,
            func.count(Alert.id)
        ).where(
            Alert.created_at >= start_date
        ).group_by(Alert.alert_group)
        
        group_result = await db.execute(group_query)
        by_group = dict(group_result.all())
        
        # Get unacknowledged alerts
        unacknowledged = await db.scalar(
            select(func.count(Alert.id)).where(
                and_(
                    Alert.created_at >= start_date,
                    Alert.acknowledged == False
                )
            )
        ) or 0
        
        # Get resolved alerts
        resolved = await db.scalar(
            select(func.count(Alert.id)).where(
                and_(
                    Alert.created_at >= start_date,
                    Alert.resolved_at.is_not(None)
                )
            )
        ) or 0
        
        return {
            "total_alerts": total_alerts,
            "by_severity": by_severity,
            "by_group": by_group,
            "unacknowledged": unacknowledged,
            "resolved": resolved,
            "period_days": days,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "server_available": True
        }
        
    except Exception as e:
        return {
            "error": "database_error",
            "message": f"Erro ao buscar estatísticas: {str(e)}",
            "total_alerts": 0,
            "by_severity": {"critical": 0, "warning": 0, "info": 0},
            "by_group": {},
            "unacknowledged": 0,
            "period_days": days,
            "server_available": False
        }
