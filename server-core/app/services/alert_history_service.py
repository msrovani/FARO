"""
Alert History Service.
Service to record and query alert history from Prometheus monitoring.
"""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional
from uuid import uuid4

from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import AlertHistory


class AlertHistoryService:
    """Service for managing alert history."""
    
    @staticmethod
    async def record_alert(
        db: AsyncSession,
        alert_name: str,
        alert_group: str,
        severity: str,
        urgency: str,
        message: Optional[str] = None,
        insight: Optional[str] = None,
        possible_causes: Optional[str] = None,
        solutions: Optional[str] = None,
        labels: Optional[dict] = None,
        annotations: Optional[dict] = None,
        ttl_days: int = 90,
    ) -> AlertHistory:
        """Record a new alert firing."""
        alert = AlertHistory(
            id=uuid4(),
            alert_name=alert_name,
            alert_group=alert_group,
            fired_at=datetime.utcnow(),
            severity=severity,
            urgency=urgency,
            message=message,
            insight=insight,
            possible_causes=possible_causes,
            solutions=solutions,
            labels=labels or {},
            annotations=annotations or {},
            acknowledged=False,
            ttl_days=ttl_days,
        )
        db.add(alert)
        await db.commit()
        return alert
    
    @staticmethod
    async def resolve_alert(
        db: AsyncSession,
        alert_name: str,
        fired_at: datetime,
    ) -> Optional[AlertHistory]:
        """Mark an alert as resolved."""
        query = select(AlertHistory).where(
            and_(
                AlertHistory.alert_name == alert_name,
                AlertHistory.fired_at == fired_at,
                AlertHistory.resolved_at.is_(None),
            )
        )
        result = await db.execute(query)
        alert = result.scalar_one_or_none()
        
        if alert:
            alert.resolved_at = datetime.utcnow()
            await db.commit()
        
        return alert
    
    @staticmethod
    async def acknowledge_alert(
        db: AsyncSession,
        alert_id: str,
        acknowledged_by: str,
    ) -> Optional[AlertHistory]:
        """Acknowledge an alert."""
        query = select(AlertHistory).where(AlertHistory.id == alert_id)
        result = await db.execute(query)
        alert = result.scalar_one_or_none()
        
        if alert:
            alert.acknowledged = True
            alert.acknowledged_at = datetime.utcnow()
            alert.acknowledged_by = acknowledged_by
            await db.commit()
        
        return alert
    
    @staticmethod
    async def get_alerts(
        db: AsyncSession,
        alert_group: Optional[str] = None,
        severity: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        acknowledged: Optional[bool] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[list[AlertHistory], int]:
        """Get alerts with filters."""
        conditions = []
        
        if alert_group:
            conditions.append(AlertHistory.alert_group == alert_group)
        if severity:
            conditions.append(AlertHistory.severity == severity)
        if start_date:
            conditions.append(AlertHistory.fired_at >= start_date)
        if end_date:
            conditions.append(AlertHistory.fired_at <= end_date)
        if acknowledged is not None:
            conditions.append(AlertHistory.acknowledged == acknowledged)
        
        where_clause = and_(*conditions) if conditions else True
        
        # Count query
        count_query = select(AlertHistory).where(where_clause)
        count_result = await db.execute(count_query)
        total = len(count_result.all())
        
        # Data query
        query = (
            select(AlertHistory)
            .where(where_clause)
            .order_by(AlertHistory.fired_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await db.execute(query)
        alerts = list(result.scalars().all())
        
        return alerts, total
    
    @staticmethod
    async def cleanup_old_alerts(db: AsyncSession, days: int = 90) -> int:
        """Delete alerts older than specified days."""
        cutoff = datetime.utcnow() - timedelta(days=days)
        
        # Only delete resolved alerts older than TTL
        query = (
            select(AlertHistory)
            .where(
                and_(
                    AlertHistory.fired_at < cutoff,
                    AlertHistory.resolved_at.isnot(None),
                )
            )
        )
        result = await db.execute(query)
        alerts_to_delete = list(result.scalars().all())
        
        for alert in alerts_to_delete:
            await db.delete(alert)
        
        await db.commit()
        return len(alerts_to_delete)
    
    @staticmethod
    async def get_alert_groups(db: AsyncSession) -> list[str]:
        """Get all unique alert groups."""
        query = select(AlertHistory.alert_group).distinct()
        result = await db.execute(query)
        return [row[0] for row in result.all()]
    
    @staticmethod
    async def get_alert_stats(db: AsyncSession, days: int = 30) -> dict:
        """Get alert statistics."""
        since = datetime.utcnow() - timedelta(days=days)
        
        # Total alerts
        total_query = select(AlertHistory).where(AlertHistory.fired_at >= since)
        total_result = await db.execute(total_query)
        total = len(total_result.all())
        
        # By severity
        severity_query = (
            select(AlertHistory.severity)
            .where(AlertHistory.fired_at >= since)
        )
        severity_result = await db.execute(severity_query)
        severity_counts = {}
        for row in severity_result.all():
            sev = row[0]
            severity_counts[sev] = severity_counts.get(sev, 0) + 1
        
        # By group
        group_query = (
            select(AlertHistory.alert_group)
            .where(AlertHistory.fired_at >= since)
        )
        group_result = await db.execute(group_query)
        group_counts = {}
        for row in group_result.all():
            group = row[0]
            group_counts[group] = group_counts.get(group, 0) + 1
        
        # Unacknowledged
        unack_query = select(AlertHistory).where(
            and_(
                AlertHistory.fired_at >= since,
                AlertHistory.acknowledged == False,
            )
        )
        unack_result = await db.execute(unack_query)
        unacknowledged = len(unack_result.all())
        
        return {
            "total_alerts": total,
            "by_severity": severity_counts,
            "by_group": group_counts,
            "unacknowledged": unacknowledged,
            "period_days": days,
        }


# Singleton instance
alert_history_service = AlertHistoryService()