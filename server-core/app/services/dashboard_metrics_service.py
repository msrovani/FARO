"""
Dashboard Metrics Service.
Service for storing and querying dashboard metrics in database.
"""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional
from uuid import uuid4

from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import DashboardMetric


class DashboardMetricsService:
    """Service for managing dashboard metrics stored in DB."""
    
    # Metric groups
    GROUP_SYSTEM = "system"      # HTTP, alerts
    GROUP_DATABASE = "database"    # Pool, queries
    GROUP_CACHE = "cache"          # Redis hit/miss
    GROUP_USER = "user"            # Connectivity, online
    GROUP_ALGORITHM = "algorithm"  # Execution time, accuracy
    GROUP_SYNC = "sync"            # Sync operations
    GROUP_SUSPICION = "suspicion"  # Suspect analytics
    
    # Value types
    TYPE_GAUGE = "gauge"
    TYPE_COUNTER = "counter"
    TYPE_HISTOGRAM_P50 = "histogram_p50"
    TYPE_HISTOGRAM_P95 = "histogram_p95"
    TYPE_HISTOGRAM_P99 = "histogram_p99"
    
    @staticmethod
    async def record_metric(
        db: AsyncSession,
        metric_name: str,
        metric_group: str,
        value: float,
        value_type: str = "gauge",
        labels: Optional[dict] = None,
        ttl_days: int = 90,
    ) -> DashboardMetric:
        """Record a single metric value."""
        metric = DashboardMetric(
            id=uuid4(),
            metric_name=metric_name,
            metric_group=metric_group,
            value=value,
            value_type=value_type,
            labels=labels or {},
            recorded_at=datetime.utcnow(),
            ttl_days=ttl_days,
        )
        db.add(metric)
        await db.commit()
        return metric
    
    @staticmethod
    async def record_batch(
        db: AsyncSession,
        metrics: list[dict],
    ) -> int:
        """Record multiple metrics at once (more efficient)."""
        now = datetime.utcnow()
        records = [
            DashboardMetric(
                id=uuid4(),
                metric_name=m["metric_name"],
                metric_group=m["metric_group"],
                value=m["value"],
                value_type=m.get("value_type", "gauge"),
                labels=m.get("labels", {}),
                recorded_at=now,
                ttl_days=m.get("ttl_days", 90),
            )
            for m in metrics
        ]
        db.add_all(records)
        await db.commit()
        return len(records)
    
    @staticmethod
    async def get_latest(
        db: AsyncSession,
        metric_name: str,
        metric_group: Optional[str] = None,
    ) -> Optional[DashboardMetric]:
        """Get the most recent value for a metric."""
        query = select(DashboardMetric).where(
            DashboardMetric.metric_name == metric_name
        )
        if metric_group:
            query = query.where(DashboardMetric.metric_group == metric_group)
        query = query.order_by(DashboardMetric.recorded_at.desc()).limit(1)
        
        result = await db.execute(query)
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_range(
        db: AsyncSession,
        metric_name: str,
        metric_group: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        interval_minutes: int = 5,
    ) -> list[DashboardMetric]:
        """Get metrics in a time range, optionally aggregated by interval."""
        if not start_time:
            start_time = datetime.utcnow() - timedelta(hours=1)
        if not end_time:
            end_time = datetime.utcnow()
        
        query = select(DashboardMetric).where(
            and_(
                DashboardMetric.metric_name == metric_name,
                DashboardMetric.recorded_at >= start_time,
                DashboardMetric.recorded_at <= end_time,
            )
        )
        if metric_group:
            query = query.where(DashboardMetric.metric_group == metric_group)
        
        query = query.order_by(DashboardMetric.recorded_at.asc())
        
        result = await db.execute(query)
        return list(result.scalars().all())
    
    @staticmethod
    async def get_aggregated(
        db: AsyncSession,
        metric_group: str,
        start_time: datetime,
        end_time: datetime,
        aggregation: str = "avg",  # avg, min, max, sum, count
    ) -> list[dict]:
        """Get aggregated metrics for a group in time range."""
        # For now, return raw data - aggregation can be done in query
        query = select(DashboardMetric).where(
            and_(
                DashboardMetric.metric_group == metric_group,
                DashboardMetric.recorded_at >= start_time,
                DashboardMetric.recorded_at <= end_time,
            )
        ).order_by(DashboardMetric.recorded_at.asc())
        
        result = await db.execute(query)
        metrics = list(result.scalars().all())
        
        # Group by metric_name
        aggregated = {}
        for m in metrics:
            key = m.metric_name
            if key not in aggregated:
                aggregated[key] = []
            aggregated[key].append({
                "recorded_at": m.recorded_at.isoformat(),
                "value": m.value,
                "labels": m.labels,
            })
        
        return aggregated
    
    @staticmethod
    async def cleanup_old_metrics(db: AsyncSession, days: int = 90) -> int:
        """Delete metrics older than specified days."""
        cutoff = datetime.utcnow() - timedelta(days=days)
        
        query = select(DashboardMetric).where(
            DashboardMetric.recorded_at < cutoff
        )
        result = await db.execute(query)
        metrics_to_delete = list(result.scalars().all())
        
        for metric in metrics_to_delete:
            await db.delete(metric)
        
        await db.commit()
        return len(metrics_to_delete)
    
    @staticmethod
    async def get_current_values(db: AsyncSession) -> dict:
        """Get current/latest values for all metric groups (for dashboard)."""
        groups = [
            DashboardMetricsService.GROUP_SYSTEM,
            DashboardMetricsService.GROUP_DATABASE,
            DashboardMetricsService.GROUP_CACHE,
            DashboardMetricsService.GROUP_USER,
            DashboardMetricsService.GROUP_ALGORITHM,
            DashboardMetricsService.GROUP_SYNC,
            DashboardMetricsService.GROUP_SUSPICION,
        ]
        
        result = {}
        for group in groups:
            query = (
                select(DashboardMetric)
                .where(DashboardMetric.metric_group == group)
                .order_by(DashboardMetric.recorded_at.desc())
            )
            exec_result = await db.execute(query)
            metrics = list(exec_result.scalars().all())
            
            # Get latest value for each unique metric name
            latest = {}
            for m in metrics:
                if m.metric_name not in latest:
                    latest[m.metric_name] = {
                        "value": m.value,
                        "recorded_at": m.recorded_at.isoformat(),
                        "type": m.value_type,
                    }
            
            result[group] = latest
        
        return result


# Singleton
dashboard_metrics_service = DashboardMetricsService()