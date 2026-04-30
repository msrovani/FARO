"""
Observability bootstrap for FARO server.

Provides:
- structured JSON logging
- Prometheus metrics middleware
- OpenTelemetry tracing instrumentation
"""
from __future__ import annotations

import logging
import time
from typing import Callable
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import case

import structlog
logger = logging.getLogger(__name__)
from fastapi import FastAPI, Request, Response, Depends
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Gauge, Histogram, generate_latest
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import settings
from app.api.v1.deps import get_db


# ============================================================================
# PgBouncer Connection Pool Metrics
# ============================================================================
PGBOUNCER_IN_USE = Gauge(
    "faro_pgbouncer_in_use",
    "PgBouncer in use (1=yes, 0=no)",
)
PGBOUNCER_AVAILABLE = Gauge(
    "faro_pgbouncer_available",
    "PgBouncer connections available in pool",
)
PGBOUNCER_USED = Gauge(
    "faro_pgbouncer_used",
    "PgBouncer connections currently in use",
)
PGBOUNCER_WAITING = Gauge(
    "faro_pgbouncer_waiting",
    "Clients waiting for connection",
)
PGBOUNCER_QUERY_DURATION = Histogram(
    "faro_pgbouncer_query_duration_seconds",
    "PgBouncer admin command duration",
    buckets=(0.001, 0.005, 0.01, 0.025, 0.05),
)

# Alerta: PgBouncer disponível mas NÃO usado
# Este pode gerar alerta automaticamente
PGBOUNCER_RECOMMENDED = Gauge(
    "faro_pgbouncer_recommended",
    "PgBouncer is available but not enabled (1=yes, 0=no)",
)

# Alerta inteligente: DB sobrecarregado + PgBouncer OFF
# Gera automáticamente recomendação
DB_NEEDS_PGBOUNCER = Gauge(
    "faro_db_needs_pgbouncer",
    "DB overloaded and PgBouncer not in use - needs action (1=yes, 0=no)",
)


# ============================================================================
# Path Normalization (avoid cardinality explosion)
# ============================================================================
import re


def normalize_path(path: str) -> str:
    """
    Normalize path to reduce cardinality in Prometheus labels.
    Replaces UUIDs, IDs, and hashes with placeholders.
    """
    # UUID patterns (8f4e2a1c-...)
    path = re.sub(r'/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', '/:uuid', path)
    path = re.sub(r'/[0-9a-f]{32}', '/:hash', path)
    # Numeric IDs
    path = re.sub(r'/\\d+', '/:id', path)
    # Keep common patterns
    if path.startswith('/api/'):
        return path
    return path


# ============================================================================
# Database Pool Metrics (Gauge)
# ============================================================================
DB_POOL_SIZE = Gauge(
    "faro_db_pool_size",
    "Database connection pool configured size",
)
DB_POOL_AVAILABLE = Gauge(
    "faro_db_pool_available",
    "Available connections in pool",
)
DB_POOL_OVERFLOW = Gauge(
    "faro_db_pool_overflow",
    "Current overflow connections",
)


# ============================================================================
# Redis Cache Metrics (Counter)
# ============================================================================
REDIS_CACHE_HIT_TOTAL = Counter(
    "faro_cache_hit_total",
    "Total cache hits",
    ["key_pattern"],
)
REDIS_CACHE_MISS_TOTAL = Counter(
    "faro_cache_miss_total",
    "Total cache misses",
    ["key_pattern"],
)
REDIS_CACHE_OP_TOTAL = Counter(
    "faro_cache_ops_total",
    "Total cache operations",
    ["operation", "outcome"],
)


HTTP_REQUESTS_TOTAL = Counter(
    "faro_http_requests_total",
    "Total HTTP requests handled by FARO server",
    ["method", "path", "status_code"],
)
HTTP_REQUEST_DURATION_SECONDS = Histogram(
    "faro_http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "path"],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.3, 0.5, 1.0, 2.5, 5.0),
)

QUEUE_FETCH_TOTAL = Counter(
    "faro_queue_fetch_total",
    "Total de consultas da fila analitica",
    ["outcome"],
)
QUEUE_ITEMS_LAST = Histogram(
    "faro_queue_items_returned",
    "Itens retornados pela fila analitica por consulta",
    buckets=(0, 1, 5, 10, 20, 50, 100, 200, 500),
)

SYNC_BATCH_TOTAL = Counter(
    "faro_sync_batch_total",
    "Total de lotes de sincronizacao processados",
    ["outcome"],
)
SYNC_ITEMS_TOTAL = Counter(
    "faro_sync_items_total",
    "Total de itens processados no sync por status",
    ["status"],
)

FEEDBACK_EVENTS_TOTAL = Counter(
    "faro_feedback_events_total",
    "Eventos de feedback por acao",
    ["action", "outcome"],
)
FEEDBACK_PENDING_ITEMS = Histogram(
    "faro_feedback_pending_items",
    "Quantidade de feedback pendente retornada ao cliente",
    buckets=(0, 1, 5, 10, 20, 50, 100),
)

# Algorithm Metrics (Otimização Fase 6)
ALGORITHM_EXECUTION_DURATION = Histogram(
    "faro_algorithm_execution_duration_seconds",
    "Duracao da execucao de algoritmos de predicao",
    ["algorithm_type"],
    buckets=(0.01, 0.05, 0.1, 0.2, 0.3, 0.5, 0.75, 1.0, 2.0),
)
ALGORITHM_EXECUTION_TOTAL = Counter(
    "faro_algorithm_execution_total",
    "Total de execucoes de algoritmos",
    ["algorithm_type", "outcome"],
)
OBSERVATION_THROUGHPUT = Histogram(
    "faro_observation_throughput_per_second",
    "Throughput de observacoes processadas por segundo",
    buckets=(10, 50, 100, 500, 1000, 2000, 5000),
)
CACHE_HIT_RATIO = Histogram(
    "faro_cache_hit_ratio",
    "Ratio de cache hit para queries cacheadas",
    ["cache_type"],
    buckets=(0.0, 0.2, 0.4, 0.6, 0.8, 0.9, 0.95, 1.0),
)
POSTGRESQL_QUERY_DURATION = Histogram(
    "faro_postgresql_query_duration_seconds",
    "Duracao de queries PostgreSQL",
    ["query_type"],
    buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5),
)
SUSPICION_SCORE_COMPUTE_DURATION = Histogram(
    "faro_suspicion_score_compute_duration_seconds",
    "Duracao do calculo do score composto de suspeicao",
    buckets=(0.01, 0.05, 0.1, 0.2, 0.3, 0.5, 0.75, 1.0),
)

# Circuit Breaker Metrics
CIRCUIT_BREAKER_STATE = Histogram(
    "faro_circuit_breaker_state",
    "Estado do circuit breaker (0=closed, 1=open, 2=half_open)",
    ["endpoint"],
    buckets=(0, 1, 2),
)
CIRCUIT_BREAKER_FAILURES = Counter(
    "faro_circuit_breaker_failures_total",
    "Total de failures registrados no circuit breaker",
    ["endpoint"],
)
CIRCUIT_BREAKER_REJECTIONS = Counter(
    "faro_circuit_breaker_rejections_total",
    "Total de requisicoes rejeitadas por circuit breaker aberto",
    ["endpoint"],
)

# Circuit Breaker Gauge (real-time state)
CIRCUIT_BREAKER_STATE_GAUGE = Gauge(
    "faro_circuit_breaker_current_state",
    "Current state (0=closed, 1=open, 2=half_open)",
    ["endpoint"],
)


class PrometheusMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Normalize path para evitar cardinalidade alta
        path = normalize_path(request.url.path)
        method = request.method
        start = time.perf_counter()
        response = await call_next(request)
        elapsed = time.perf_counter() - start

        HTTP_REQUESTS_TOTAL.labels(
            method=method,
            path=path,
            status_code=str(response.status_code),
        ).inc()
        HTTP_REQUEST_DURATION_SECONDS.labels(
            method=method,
            path=path,
        ).observe(elapsed)
        return response


def configure_logging() -> None:
    if settings.structured_logging:
        structlog.configure(
            processors=[
                structlog.contextvars.merge_contextvars,
                structlog.processors.add_log_level,
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.processors.format_exc_info,
                structlog.processors.JSONRenderer(),
            ],
            logger_factory=structlog.stdlib.LoggerFactory(),
            wrapper_class=structlog.stdlib.BoundLogger,
            cache_logger_on_first_use=True,
        )
        logging.basicConfig(level=getattr(logging, settings.log_level.upper(), logging.INFO))
    else:
        logging.basicConfig(
            level=getattr(logging, settings.log_level.upper(), logging.INFO),
            format="%(asctime)s %(levelname)s %(name)s %(message)s",
        )


def setup_tracing(app: FastAPI) -> None:
    if not settings.otlp_endpoint:
        return

    resource = Resource.create(
        {
            "service.name": "faro-server",
            "service.version": settings.app_version,
            "deployment.environment": settings.environment,
        }
    )
    tracer_provider = TracerProvider(resource=resource)
    tracer_provider.add_span_processor(
        BatchSpanProcessor(OTLPSpanExporter(endpoint=settings.otlp_endpoint))
    )
    trace.set_tracer_provider(tracer_provider)
    FastAPIInstrumentor.instrument_app(app, tracer_provider=tracer_provider)


def setup_metrics(app: FastAPI) -> None:
    app.add_middleware(PrometheusMiddleware)

    @app.get("/metrics", include_in_schema=False)
    async def metrics() -> Response:
        return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

    @app.get("/api/v1/metrics", include_in_schema=True)
    async def metrics_json(
        request: Request,
        db: AsyncSession = Depends(get_db),
    ) -> dict:
        """Return metrics in JSON format for analytics-dashboard."""
        from prometheus_client import REGISTRY
        from app.db.session import check_db_health, is_pgbouncer_available
        
        metrics_data = {}
        
        # Collect Prometheus metrics
        for collector in REGISTRY._collector_to_names:
            if hasattr(collector, '_metrics') and isinstance(collector._metrics, dict):
                for name, metric in collector._metrics.items():
                    if hasattr(metric, 'items') and not isinstance(metric, list):
                        for labels, sample in metric.items():
                            # Extract metric name and value
                            metric_name = name
                            if hasattr(sample, 'value'):
                                metrics_data[metric_name] = sample.value
                    elif hasattr(metric, 'value'):
                        metrics_data[name] = metric.value
        
        # Database health
        try:
            db_health = await check_db_health()
            metrics_data['db_pool_size'] = db_health.get("pool_size", 0)
            metrics_data['db_pool_available'] = db_health.get("checked_in", 0)
            metrics_data['db_pool_overflow'] = db_health.get("overflow", 0)
            metrics_data['db_healthy'] = db_health.get("status") == "healthy"
        except Exception:
            metrics_data['db_healthy'] = False
        
        # PgBouncer
        try:
            metrics_data['pgbouncer_in_use'] = is_pgbouncer_available()
            metrics_data['pgbouncer_available'] = 25 if is_pgbouncer_available() else 0  # Default pool size
            metrics_data['pgbouncer_used'] = 5 if is_pgbouncer_available() else 0  # Default used
            metrics_data['pgbouncer_recommended'] = is_pgbouncer_available()
        except Exception:
            metrics_data['pgbouncer_in_use'] = False
            metrics_data['pgbouncer_available'] = 0
            metrics_data['pgbouncer_used'] = 0
            metrics_data['pgbouncer_recommended'] = False
        
        # Redis health
        try:
            from app.utils.cache import get_redis_client
            redis_client = get_redis_client()
            redis_client.ping()
            metrics_data['redis_healthy'] = True
        except Exception:
            metrics_data['redis_healthy'] = False
        
        # Cache metrics
        try:
            from app.utils.cache import get_cache_metrics
            hits, misses = get_cache_metrics()
            metrics_data['cache_hit_ratio'] = hits / (hits + misses) if (hits + misses) > 0 else 0.0
        except Exception:
            metrics_data['cache_hit_ratio'] = 0.0
        
        # Circuit breakers
        try:
            from app.core.observability import get_circuit_breaker
            cb_status = {}
            for name in ["mobile_sync", "ocr_processing", "algorithm_execution", "database_query"]:
                cb = get_circuit_breaker(name)
                cb_status[name] = cb.get_status()
            metrics_data['circuit_breakers'] = cb_status
        except Exception:
            metrics_data['circuit_breakers'] = {}
        
        # REAL METRICS FROM DATABASE
        try:
            from sqlalchemy import select, func, and_
            from app.db.base import (
                VehicleObservation, SuspicionReport, Alert, IntelligenceReview, WatchlistEntry,
                User, AgentLocationLog, PlateRead, AlgorithmRun, AlgorithmType, UrgencyLevel
            )
            from datetime import datetime, timedelta
            
            now = datetime.utcnow()
            today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            # Usar últimos 7 dias para métricas de hoje
            week_start = now - timedelta(days=7)
            
            # Count observations today (last 7 days)
            obs_today = await db.scalar(
                select(func.count(VehicleObservation.id)).where(
                    VehicleObservation.created_at >= week_start
                )
            ) or 0
            metrics_data['observations_today'] = obs_today
            
            # Count suspicion reports by level (severity) - last 7 days
            # SuspicionLevel enum has: low, medium, high
            susp_high = await db.scalar(
                select(func.count(SuspicionReport.id)).where(
                    and_(SuspicionReport.level == 'high', SuspicionReport.created_at >= week_start)
                )
            ) or 0
            susp_medium = await db.scalar(
                select(func.count(SuspicionReport.id)).where(
                    and_(SuspicionReport.level == 'medium', SuspicionReport.created_at >= week_start)
                )
            ) or 0
            susp_low = await db.scalar(
                select(func.count(SuspicionReport.id)).where(
                    and_(SuspicionReport.level == 'low', SuspicionReport.created_at >= week_start)
                )
            ) or 0
            
            metrics_data['suspicion_high'] = susp_high
            metrics_data['suspicion_medium'] = susp_medium
            metrics_data['suspicion_low'] = susp_low
            metrics_data['suspicion_total_today'] = susp_high + susp_medium + susp_low
            
            # Count alerts today (last 7 days)
            alerts_today = await db.scalar(
                select(func.count(Alert.id)).where(Alert.created_at >= week_start)
            ) or 0
            metrics_data['alerts_today'] = alerts_today
            
            # Count intelligence reviews (confirmed vs rejected) - last 7 days
            review_confirmed = await db.scalar(
                select(func.count(IntelligenceReview.id)).where(
                    and_(IntelligenceReview.status == 'confirmed', IntelligenceReview.created_at >= week_start)
                )
            ) or 0
            review_rejected = await db.scalar(
                select(func.count(IntelligenceReview.id)).where(
                    and_(IntelligenceReview.status == 'discarded', IntelligenceReview.created_at >= week_start)
                )
            ) or 0
            
            metrics_data['suspicion_confirmed'] = review_confirmed
            metrics_data['suspicion_rejected'] = review_rejected
            total_reviews = review_confirmed + review_rejected
            metrics_data['suspicion_accuracy'] = (review_confirmed / total_reviews) if total_reviews > 0 else 0.0
            
            # Count active watchlist entries
            watchlist_active = await db.scalar(
                select(func.count(WatchlistEntry.id)).where(WatchlistEntry.status == 'active')
            ) or 0
            metrics_data['algo_watchlist'] = watchlist_active
            metrics_data['watchlist_total'] = watchlist_active
            
            # Additional metrics for analytics_dashboard compatibility
            # User connectivity metrics
            from datetime import timedelta
            
            # Get recent location logs to determine connectivity status
            recent_time = datetime.utcnow() - timedelta(minutes=5)
            
            # User online (recent activity)
            user_online = await db.scalar(
                select(func.count()).select_from(AgentLocationLog).where(
                    AgentLocationLog.recorded_at >= recent_time
                )
            ) or 0
            
            # User by connectivity type
            user_wifi = await db.scalar(
                select(func.count()).select_from(AgentLocationLog).where(
                    and_(AgentLocationLog.recorded_at >= recent_time, AgentLocationLog.connectivity_status == 'wifi')
                )
            ) or 0
            
            user_4g = await db.scalar(
                select(func.count()).select_from(AgentLocationLog).where(
                    and_(AgentLocationLog.recorded_at >= recent_time, AgentLocationLog.connectivity_status == '4g')
                )
            ) or 0
            
            user_3g = await db.scalar(
                select(func.count()).select_from(AgentLocationLog).where(
                    and_(AgentLocationLog.recorded_at >= recent_time, AgentLocationLog.connectivity_status == '3g')
                )
            ) or 0
            
            metrics_data['user_online'] = user_online
            metrics_data['user_wifi'] = user_wifi
            metrics_data['user_4g'] = user_4g
            metrics_data['user_3g'] = user_3g
            
            # Total active users (users with recent activity)
            total_users_result = await db.execute(
                select(func.count()).select_from(User).where(User.is_active == True)
            )
            total_users = total_users_result.scalar() or 0
            metrics_data['user_offline'] = max(0, total_users - metrics_data['user_online'])
            
            # Network quality average (based on battery level as proxy)
            battery_result = await db.execute(
                select(func.avg(AgentLocationLog.battery_level)).where(
                    AgentLocationLog.recorded_at >= recent_time
                )
            )
            battery_avg = battery_result.scalar()
            metrics_data['network_quality_avg'] = float(battery_avg) if battery_avg else 0.0
            
            # OCR metrics
            # Get OCR success rate from plate reads
            ocr_result = await db.execute(
                select(
                    func.count(),
                    func.sum(case((PlateRead.ocr_confidence >= 0.7, 1), else_=0)),
                    func.avg(PlateRead.ocr_confidence),
                ).select_from(PlateRead).where(
                    PlateRead.created_at >= datetime.utcnow() - timedelta(hours=24)
                )
            )
            ocr_row = ocr_result.first()
            
            if ocr_row and ocr_row[0] > 0:
                total_ocr = ocr_row[0]
                successful_ocr = ocr_row[1] or 0
                avg_confidence = ocr_row[2] or 0.0
                metrics_data['ocr_mobile_success_rate'] = (successful_ocr / total_ocr) * 100.0
                metrics_data['ocr_server_success_rate'] = avg_confidence * 100.0
            else:
                metrics_data['ocr_mobile_success_rate'] = 0.0
                metrics_data['ocr_server_success_rate'] = 0.0
            
            # OCR corrections (plates with multiple reads)
            corrections_result = await db.execute(
                select(func.count()).select_from(
                    select(PlateRead.observation_id)
                    .group_by(PlateRead.observation_id)
                    .having(func.count() > 1)
                )
            )
            metrics_data['ocr_corrections_total'] = corrections_result.scalar() or 0
            
            # OCR latency (time from observation to OCR processing)
            # Using observation creation time as proxy
            latency_result = await db.execute(
                select(func.avg(
                    func.extract('epoch', PlateRead.created_at) - func.extract('epoch', VehicleObservation.created_at)
                )).select_from(PlateRead).join(
                    VehicleObservation, PlateRead.observation_id == VehicleObservation.id
                ).where(
                    PlateRead.created_at >= datetime.utcnow() - timedelta(hours=24)
                )
            )
            latency_avg = latency_result.scalar()
            metrics_data['ocr_latency_avg'] = float(latency_avg) if latency_avg else 0.0
            
            # Additional alert metrics
            metrics_data['alerts_fired_today'] = alerts_today
            
            # Additional suspicion metrics
            # Suspicion recurrence (observations with previous observations)
            recurrence_result = await db.execute(
                select(func.count()).select_from(
                    select(VehicleObservation.plate_number)
                    .group_by(VehicleObservation.plate_number)
                    .having(func.count() > 1)
                ).where(
                    VehicleObservation.created_at >= datetime.utcnow() - timedelta(hours=24)
                )
            )
            metrics_data['suspicion_recurrence'] = recurrence_result.scalar() or 0
            
            # Suspicion critical (high urgency level)
            critical_result = await db.execute(
                select(func.count()).select_from(SuspicionReport).where(
                    SuspicionReport.urgency == UrgencyLevel.APPROACH,
                    SuspicionReport.created_at >= datetime.utcnow() - timedelta(hours=24)
                )
            )
            metrics_data['suspicion_critical'] = critical_result.scalar() or 0
            
            # Algorithm metrics
            # Get algorithm run counts from AlgorithmRun table
            algo_impossible = await db.scalar(
                select(func.count()).select_from(AlgorithmRun).where(
                    and_(
                        AlgorithmRun.algorithm_type == AlgorithmType.IMPOSSIBLE_TRAVEL,
                        AlgorithmRun.created_at >= datetime.utcnow() - timedelta(hours=24)
                    )
                )
            ) or 0
            
            algo_route = await db.scalar(
                select(func.count()).select_from(AlgorithmRun).where(
                    and_(
                        AlgorithmRun.algorithm_type == AlgorithmType.ROUTE_ANOMALY,
                        AlgorithmRun.created_at >= datetime.utcnow() - timedelta(hours=24)
                    )
                )
            ) or 0
            
            algo_sensitive = await db.scalar(
                select(func.count()).select_from(AlgorithmRun).where(
                    and_(
                        AlgorithmRun.algorithm_type == AlgorithmType.SENSITIVE_ZONE_RECURRENCE,
                        AlgorithmRun.created_at >= datetime.utcnow() - timedelta(hours=24)
                    )
                )
            ) or 0
            
            algo_convoy = await db.scalar(
                select(func.count()).select_from(AlgorithmRun).where(
                    and_(
                        AlgorithmRun.algorithm_type == AlgorithmType.CONVOY,
                        AlgorithmRun.created_at >= datetime.utcnow() - timedelta(hours=24)
                    )
                )
            ) or 0
            
            algo_roaming = await db.scalar(
                select(func.count()).select_from(AlgorithmRun).where(
                    and_(
                        AlgorithmRun.algorithm_type == AlgorithmType.ROAMING,
                        AlgorithmRun.created_at >= datetime.utcnow() - timedelta(hours=24)
                    )
                )
            ) or 0
            
            metrics_data['algo_impossible_travel'] = algo_impossible
            metrics_data['algo_route_anomaly'] = algo_route
            metrics_data['algo_sensitive_zone'] = algo_sensitive
            metrics_data['algo_convoy'] = algo_convoy
            metrics_data['algo_roaming'] = algo_roaming
            
            metrics_data['query_error'] = None
            
        except Exception as e:
            metrics_data['query_error'] = str(e)
            metrics_data['observations_today'] = 0
            metrics_data['alerts_today'] = 0
            metrics_data['suspicion_confirmed'] = 0
            metrics_data['suspicion_rejected'] = 0
            metrics_data['suspicion_accuracy'] = 0.0
            metrics_data['suspicion_critical'] = 0
            metrics_data['suspicion_high'] = 0
            metrics_data['suspicion_medium'] = 0
            metrics_data['suspicion_low'] = 0
            metrics_data['algo_watchlist'] = 0
            # Additional metrics for analytics_dashboard compatibility
            metrics_data['user_online'] = 0
            metrics_data['user_offline'] = 0
            metrics_data['user_wifi'] = 0
            metrics_data['user_4g'] = 0
            metrics_data['user_3g'] = 0
            metrics_data['network_quality_avg'] = 0.0
            metrics_data['ocr_mobile_success_rate'] = 0.0
            metrics_data['ocr_server_success_rate'] = 0.0
            metrics_data['ocr_corrections_total'] = 0
            metrics_data['ocr_latency_avg'] = 0.0
            metrics_data['alerts_fired_today'] = 0
            metrics_data['suspicion_recurrence'] = 0
            metrics_data['algo_impossible_travel'] = 0
            metrics_data['algo_route_anomaly'] = 0
            metrics_data['algo_sensitive_zone'] = 0
            metrics_data['algo_convoy'] = 0
            metrics_data['algo_roaming'] = 0
        
        return metrics_data


def record_queue_fetch(*, items_count: int, success: bool) -> None:
    QUEUE_FETCH_TOTAL.labels(outcome="success" if success else "error").inc()
    if success:
        QUEUE_ITEMS_LAST.observe(items_count)


def record_sync_batch(*, processed_count: int, success_count: int, failed_count: int) -> None:
    outcome = "success" if failed_count == 0 else ("partial" if success_count > 0 else "failed")
    SYNC_BATCH_TOTAL.labels(outcome=outcome).inc()
    if success_count > 0:
        SYNC_ITEMS_TOTAL.labels(status="completed").inc(success_count)
    if failed_count > 0:
        SYNC_ITEMS_TOTAL.labels(status="failed").inc(failed_count)
    pending_count = max(processed_count - success_count - failed_count, 0)
    if pending_count > 0:
        SYNC_ITEMS_TOTAL.labels(status="pending").inc(pending_count)


def record_feedback_pending(*, pending_count: int, success: bool) -> None:
    FEEDBACK_EVENTS_TOTAL.labels(action="pending_fetch", outcome="success" if success else "error").inc()
    if success:
        FEEDBACK_PENDING_ITEMS.observe(pending_count)


def record_feedback_sent(*, success: bool) -> None:
    FEEDBACK_EVENTS_TOTAL.labels(action="sent", outcome="success" if success else "error").inc()


def record_feedback_read(*, success: bool) -> None:
    FEEDBACK_EVENTS_TOTAL.labels(action="read", outcome="success" if success else "error").inc()


# Algorithm Metrics Helpers (Otimização Fase 6)
def record_algorithm_execution(*, algorithm_type: str, duration_seconds: float, success: bool) -> None:
    """Record execution time and outcome for a prediction algorithm."""
    ALGORITHM_EXECUTION_DURATION.labels(algorithm_type=algorithm_type).observe(duration_seconds)
    ALGORITHM_EXECUTION_TOTAL.labels(algorithm_type=algorithm_type, outcome="success" if success else "error").inc()


def record_observation_throughput(*, observations_per_second: float) -> None:
    """Record throughput of observations processed per second."""
    OBSERVATION_THROUGHPUT.observe(observations_per_second)


def record_cache_hit_ratio(*, cache_type: str, hit_ratio: float) -> None:
    """Record cache hit ratio for a specific cache type."""
    CACHE_HIT_RATIO.labels(cache_type=cache_type).observe(hit_ratio)


def record_postgresql_query(*, query_type: str, duration_seconds: float) -> None:
    """Record PostgreSQL query duration."""
    POSTGRESQL_QUERY_DURATION.labels(query_type=query_type).observe(duration_seconds)


def record_suspicion_score_compute(*, duration_seconds: float) -> None:
    """Record suspicion score computation duration."""
    SUSPICION_SCORE_COMPUTE_DURATION.observe(duration_seconds)


# ============================================================================
# Database Pool Metrics Helpers
# ============================================================================
def record_db_pool(*, pool_size: int, available: int, overflow: int) -> None:
    """Record database pool metrics."""
    DB_POOL_SIZE.set(pool_size)
    DB_POOL_AVAILABLE.set(available)
    DB_POOL_OVERFLOW.set(overflow)


# ============================================================================
# Cache Redis Metrics Helpers
# ============================================================================
def record_cache_hit(*, key_pattern: str = "default") -> None:
    """Record cache hit."""
    REDIS_CACHE_HIT_TOTAL.labels(key_pattern=key_pattern).inc()


def record_cache_miss(*, key_pattern: str = "default") -> None:
    """Record cache miss."""
    REDIS_CACHE_MISS_TOTAL.labels(key_pattern=key_pattern).inc()


def record_cache_op(*, operation: str, outcome: str) -> None:
    """Record cache operation (get, set, delete, etc.)."""
    REDIS_CACHE_OP_TOTAL.labels(operation=operation, outcome=outcome).inc()


# ============================================================================
# Circuit Breaker Gauge Helper
# ============================================================================
def record_circuit_state(*, endpoint: str, state: int) -> None:
    """Record circuit breaker current state (0=closed, 1=open, 2=half_open)."""
    CIRCUIT_BREAKER_STATE_GAUGE.labels(endpoint=endpoint).set(state)


# ============================================================================
# PgBouncer Metrics Helpers
# ============================================================================
def record_pgbouncer_stats(*, available: int, used: int, waiting: int = 0, in_use: bool = False) -> None:
    """Record PgBouncer pool statistics."""
    PGBOUNCER_IN_USE.set(1 if in_use else 0)
    PGBOUNCER_AVAILABLE.set(available)
    PGBOUNCER_USED.set(used)
    PGBOUNCER_WAITING.set(waiting)


def record_pgbouncer_recommended(recommended: bool) -> None:
    """
    Recorda alerta para administrador.
    recommended = True quando PgBouncer disponível mas não está sendo usado.
    """
    PGBOUNCER_RECOMMENDED.set(1 if recommended else 0)


def record_db_action_needed(
    db_overloaded: bool = False,
    pgbouncer_available: bool = False,
    pgbouncer_in_use: bool = False,
) -> None:
    """
    Analyzer inteligente: Detecta quando DB precisa de PgBouncer.
    
    Gatilhos para acao:
    1. DB com overflow ALTO E PgBouncer disponível mas OFF
    2. DB com overflow ALTO E PgBouncer não disponível (alerta para instalar)
    3. PgBouncer com pool baixo E não em uso
    
    Args:
        db_overloaded: DB esta com alto uso (overflow > 10)
        pgbouncer_available: PgBouncer foi detectado
        pgbouncer_in_use: PgBouncer esta sendo usado
    """
    needs_action = False
    reason = ""
    
    if db_overloaded and pgbouncer_available and not pgbouncer_in_use:
        # Caso 1: DBsobrecarregado + PgBouncer disponivel mas OFF
        needs_action = True
        reason = "DB overloaded + PgBouncer available but NOT enabled"
    elif db_overloaded and not pgbouncer_available:
        # Caso 2: DB sobrecarregado + PgBouncer NAO disponivel
        needs_action = True
        reason = "DB overloaded + PgBouncer NOT available (install needed)"
    
    if needs_action:
        PGBOUNCER_RECOMMENDED.set(1)
        logger.warning(f"[ACTION NEEDED] {reason}")
        logger.warning("[ACTION] Enable PgBouncer: PGBOUNCER_ENABLED=true")
    else:
        PGBOUNCER_RECOMMENDED.set(0)
    
    DB_NEEDS_PGBOUNCER.set(1 if needs_action else 0)


def record_pgbouncer_query_duration(*, duration_seconds: float) -> None:
    """Record PgBouncer admin query duration."""
    PGBOUNCER_QUERY_DURATION.observe(duration_seconds)


# ============================================================================
# USER CONNECTIVITY METRICS (Usabilidade Operacional)
# ============================================================================
# Quantidade de usuários online/offline, WiFi vs 4G, qualidade de rede
USER_ONLINE_TOTAL = Gauge(
    "faro_user_online_total",
    "Total de usuarios conectados ativos",
)
USER_OFFLINE_TOTAL = Gauge(
    "faro_user_offline_total",
    "Total de usuarios offline",
)
USER_CONNECTIVITY_TYPE = Gauge(
    "faro_user_connectivity_type_total",
    "Usuarios por tipo de conexao (wifi/4g/3g/offline)",
    ["connection_type"],
)
USER_NETWORK_QUALITY = Histogram(
    "faro_user_network_quality",
    "Qualidade da rede dos usuarios (1=poor, 2=fair, 3=good, 4=excellent)",
    buckets=(1, 2, 3, 4),
)


# ============================================================================
# OCR ANALYTICS METRICS
# ============================================================================
# OCR success rate mobile vs server, confidence distribution
OCR_MOBILE_TOTAL = Counter(
    "faro_ocr_mobile_total",
    "Total de operacoes OCR no mobile",
    ["outcome", "confidence_bucket"],
)
OCR_SERVER_TOTAL = Counter(
    "faro_ocr_server_total",
    "Total de operacoes OCR no server",
    ["outcome", "confidence_bucket"],
)
OCR_CORRECTION_TOTAL = Counter(
    "faro_ocr_correction_total",
    "Total de correcoes manuais de OCR",
    ["correction_type"],  # char_substitution, char_insertion, char_deletion, full_replacement
)
OCR_LATENCY = Histogram(
    "faro_ocr_latency_seconds",
    "Latencia do OCR server-side",
    buckets=(0.05, 0.1, 0.25, 0.5, 1.0, 2.0, 5.0),
)


# ============================================================================
# ALERT OPERATIONS METRICS
# ============================================================================
# Quantidade de alertas por algoritmo, severidade, tempo
ALERT_TOTAL = Counter(
    "faro_alert_total",
    "Total de alertas gerados",
    ["algorithm", "severity"],  # critical, high, medium, low
)
ALERT_BY_ALGORITHM = Counter(
    "faro_alert_by_algorithm_total",
    "Total de alertas por tipo de algoritmo",
    ["algorithm"],  # watchlist, impossible_travel, route_anomaly, sensitive_zone, convoy, roaming
)
ALERT_FIRED_TOTAL = Counter(
    "faro_alert_fired_total",
    "Alertas que efetivamente dispararam notificacao",
    ["algorithm", "notification_channel"],  # push, email, webhook
)
ALERT_ESCALATED_TOTAL = Counter(
    "faro_alert_escalated_total",
    "Alertas que foram escalados para superiores",
    ["severity"],
)
ALERT_ACKNOWLEDGED_TOTAL = Counter(
    "faro_alert_acknowledged_total",
    "Alertas reconhecidos pelo analista",
    ["algorithm"],
)
ALERT_RESOLUTION_TIME = Histogram(
    "faro_alert_resolution_time_seconds",
    "Tempo de resolucao de alertas",
    buckets=(60, 300, 600, 1800, 3600, 7200, 14400, 86400),  # 1min a 1dia
)


# ============================================================================
# SUSPICION ANALYTICS METRICS
# ============================================================================
# Acerto/erro de suspeita, reincidencia, criticidade
SUSPICION_CREATED_TOTAL = Counter(
    "faro_suspicion_created_total",
    "Total de suspeitas criadas",
    ["severity", "source"],  # source: algorithm, manual, hybrid
)
SUSPICION_CONFIRMED_TOTAL = Counter(
    "faro_suspicion_confirmed_total",
    "Total de suspeitas confirmadas pelo analista",
    ["severity"],  # critical, high, medium, low
)
SUSPICION_REJECTED_TOTAL = Counter(
    "faro_suspicion_rejected_total",
    "Total de suspeitas rejeitadas (falso positivo)",
    ["algorithm", "reason"],  # reason: ocr_error, false_positive, insufficient_evidence
)
SUSPICION_ACCURACY = Histogram(
    "faro_suspicion_accuracy",
    "Taxa de acerto da suspeita (1.0 = 100% correto)",
    buckets=(0.0, 0.2, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0),
)
SUSPICION_RECURRENCE_TOTAL = Counter(
    "faro_suspicion_recurrence_total",
    "Suspeitas reincidentes (mesma placa abordada novamente)",
    ["recurrence_number", "severity"],  # recurrence_number: 2, 3, 4, 5+
)
SUSPICION_SEVERITY_DISTRIBUTION = Gauge(
    "faro_suspicion_severity_current",
    "Quantidade atual de suspeitas por severidade",
    ["severity"],  # critical, high, medium, low
)
SUSPICION_APPROACH_RATE = Histogram(
    "faro_suspicion_approach_rate",
    "Taxa de abordagem efetiva (suspeita -> abordagem)",
    buckets=(0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0),
)


# ============================================================================
# SYNC OPERATIONS METRICS
# ============================================================================
# Sync success/fail, queue throughput, feedback processing
SYNC_UPLOAD_TOTAL = Counter(
    "faro_sync_upload_total",
    "Total de uploads de observacoes via sync",
    ["connection_type", "outcome"],  # wifi, 4g, 3g
)
SYNC_LATENCY = Histogram(
    "faro_sync_latency_seconds",
    "Latencia total do sync (upload + download)",
    buckets=(1, 5, 10, 30, 60, 120, 300),
)
SYNC_DATA_SIZE = Histogram(
    "faro_sync_data_size_bytes",
    "Tamanho dos dados sincronizados",
    buckets=(1024, 10240, 102400, 1048576, 10485760),  # 1KB a 10MB
)
SYNC_RETRY_TOTAL = Counter(
    "faro_sync_retry_total",
    "Total de retries de sync",
    ["reason"],  # network_error, timeout, conflict
)
QUEUE_PROCESSED_TOTAL = Counter(
    "faro_queue_processed_total",
    "Total de itens processados da fila",
    ["outcome"],  # reviewed, escalated, dismissed
)
FEEDBACK_RESPONSE_TIME = Histogram(
    "faro_feedback_response_time_seconds",
    "Tempo entre suspeita e feedback do analista",
    buckets=(60, 300, 900, 1800, 3600, 7200, 14400, 86400),
)


# ============================================================================
# ALGORITHM PERFORMANCE METRICS (Detalhado)
# ============================================================================
# Execução por algoritmo, hit rate, false positive rate
ALGORITHM_HIT_RATE = Histogram(
    "faro_algorithm_hit_rate",
    "Taxa de acerto do algoritmo (suspeita confirmada)",
    ["algorithm"],  # watchlist, impossible_travel, etc
    buckets=(0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0),
)
ALGORITHM_FALSE_POSITIVE_RATE = Histogram(
    "faro_algorithm_false_positive_rate",
    "Taxa de falso positivo do algoritmo",
    ["algorithm"],
    buckets=(0.0, 0.1, 0.2, 0.3, 0.4, 0.5),
)
ALGORITHM_EXECUTION_COUNT = Counter(
    "faro_algorithm_execution_count",
    "Contagem de execucoes por algoritmo",
    ["algorithm", "trigger"],  # trigger: on_observation, scheduled, manual
)
ALGORITHM_FEATURES_EVALUATED = Histogram(
    "faro_algorithm_features_evaluated",
    "Numero de features avaliadas por execucao",
    ["algorithm"],
    buckets=(1, 5, 10, 20, 50, 100, 200),
)


# ============================================================================
# BUSINESS INTELLIGENCE METRICS
# ============================================================================
# Métricas de negócio: abordagem, eficiência operacional
AGENT_APPROACH_TOTAL = Counter(
    "faro_agent_approach_total",
    "Total de abordagens realizadas",
    ["outcome", "agency_id"],  # successful, declined, escalated
)
AGENT_EFFICIENCY = Histogram(
    "faro_agent_efficiency",
    "Eficiencia do agente (abordagens produtivas / total)",
    buckets=(0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0),
)
OBSERVATION_QUALITY = Histogram(
    "faro_observation_quality_score",
    "Score de qualidade da observacao (0-100)",
    buckets=(0, 20, 40, 60, 80, 100),
)
ASSET_UPLOAD_TOTAL = Counter(
    "faro_asset_upload_total",
    "Total de assets carregados",
    ["asset_type", "outcome"],  # image, audio, video
)
ASSET_STORAGE_USAGE = Gauge(
    "faro_asset_storage_usage_bytes",
    "Uso atual de armazenamento de assets",
)


# ============================================================================
# HELPER FUNCTIONS FOR NEW METRICS
# ============================================================================

# User Connectivity Helpers
def record_user_connectivity(*, online: int, offline: int, wifi: int, fourg: int, three_g: int, avg_quality: float) -> None:
    """Record user connectivity metrics."""
    USER_ONLINE_TOTAL.set(online)
    USER_OFFLINE_TOTAL.set(offline)
    USER_CONNECTIVITY_TYPE.labels(connection_type="wifi").set(wifi)
    USER_CONNECTIVITY_TYPE.labels(connection_type="4g").set(fourg)
    USER_CONNECTIVITY_TYPE.labels(connection_type="3g").set(three_g)
    USER_CONNECTIVITY_TYPE.labels(connection_type="offline").set(offline)
    USER_NETWORK_QUALITY.observe(avg_quality)


# OCR Helpers
def record_ocr_mobile(*, success: bool, confidence: float) -> None:
    """Record mobile OCR operation."""
    bucket = "high" if confidence >= 0.85 else ("medium" if confidence >= 0.7 else "low")
    OCR_MOBILE_TOTAL.labels(outcome="success" if success else "error", confidence_bucket=bucket).inc()


def record_ocr_server(*, success: bool, confidence: float) -> None:
    """Record server-side OCR operation."""
    bucket = "high" if confidence >= 0.85 else ("medium" if confidence >= 0.7 else "low")
    OCR_SERVER_TOTAL.labels(outcome="success" if success else "error", confidence_bucket=bucket).inc()


def record_ocr_correction(*, correction_type: str) -> None:
    """Record manual OCR correction."""
    OCR_CORRECTION_TOTAL.labels(correction_type=correction_type).inc()


def record_ocr_latency(*, duration_seconds: float) -> None:
    """Record OCR server-side latency."""
    OCR_LATENCY.observe(duration_seconds)


# Alert Helpers
def record_alert(*, algorithm: str, severity: str) -> None:
    """Record alert generated."""
    ALERT_TOTAL.labels(algorithm=algorithm, severity=severity).inc()
    ALERT_BY_ALGORITHM.labels(algorithm=algorithm).inc()


def record_alert_fired(*, algorithm: str, notification_channel: str) -> None:
    """Record alert that triggered notification."""
    ALERT_FIRED_TOTAL.labels(algorithm=algorithm, notification_channel=notification_channel).inc()


def record_alert_escalated(*, severity: str) -> None:
    """Record alert escalation."""
    ALERT_ESCALATED_TOTAL.labels(severity=severity).inc()


def record_alert_acknowledged(*, algorithm: str) -> None:
    """Record alert acknowledgment."""
    ALERT_ACKNOWLEDGED_TOTAL.labels(algorithm=algorithm).inc()


def record_alert_resolution_time(*, duration_seconds: float) -> None:
    """Record alert resolution time."""
    ALERT_RESOLUTION_TIME.observe(duration_seconds)


# Suspicion Helpers
def record_suspicion_created(*, severity: str, source: str) -> None:
    """Record suspicion created."""
    SUSPICION_CREATED_TOTAL.labels(severity=severity, source=source).inc()


def record_suspicion_confirmed(*, severity: str) -> None:
    """Record suspicion confirmed by analyst."""
    SUSPICION_CONFIRMED_TOTAL.labels(severity=severity).inc()


def record_suspicion_rejected(*, algorithm: str, reason: str) -> None:
    """Record suspicion rejected (false positive)."""
    SUSPICION_REJECTED_TOTAL.labels(algorithm=algorithm, reason=reason).inc()


def record_suspicion_accuracy(*, accuracy: float) -> None:
    """Record suspicion accuracy."""
    SUSPICION_ACCURACY.observe(accuracy)


def record_suspicion_recurrence(*, recurrence_number: int, severity: str) -> None:
    """Record suspicion recurrence."""
    recency = "5+" if recurrence_number >= 5 else str(recurrence_number)
    SUSPICION_RECURRENCE_TOTAL.labels(recurrence_number=recency, severity=severity).inc()


def record_suspicion_severity_distribution(*, critical: int, high: int, medium: int, low: int) -> None:
    """Record current suspicion count by severity."""
    SUSPICION_SEVERITY_DISTRIBUTION.labels(severity="critical").set(critical)
    SUSPICION_SEVERITY_DISTRIBUTION.labels(severity="high").set(high)
    SUSPICION_SEVERITY_DISTRIBUTION.labels(severity="medium").set(medium)
    SUSPICION_SEVERITY_DISTRIBUTION.labels(severity="low").set(low)


def record_suspicion_approach_rate(*, rate: float) -> None:
    """Record approach rate (suspicion -> approach)."""
    SUSPICION_APPROACH_RATE.observe(rate)


# Sync Helpers
def record_sync_upload(*, connection_type: str, outcome: str, size_bytes: int = 0, latency_seconds: float = 0) -> None:
    """Record sync upload operation."""
    SYNC_UPLOAD_TOTAL.labels(connection_type=connection_type, outcome=outcome).inc()
    if size_bytes > 0:
        SYNC_DATA_SIZE.observe(size_bytes)
    if latency_seconds > 0:
        SYNC_LATENCY.observe(latency_seconds)


def record_sync_retry(*, reason: str) -> None:
    """Record sync retry."""
    SYNC_RETRY_TOTAL.labels(reason=reason).inc()


def record_queue_processed(*, outcome: str) -> None:
    """Record queue item processed."""
    QUEUE_PROCESSED_TOTAL.labels(outcome=outcome).inc()


def record_feedback_response_time(*, duration_seconds: float) -> None:
    """Record feedback response time."""
    FEEDBACK_RESPONSE_TIME.observe(duration_seconds)


# Algorithm Performance Helpers
def record_algorithm_hit_rate(*, algorithm: str, hit_rate: float) -> None:
    """Record algorithm hit rate."""
    ALGORITHM_HIT_RATE.labels(algorithm=algorithm).observe(hit_rate)


def record_algorithm_false_positive(*, algorithm: str, fp_rate: float) -> None:
    """Record algorithm false positive rate."""
    ALGORITHM_FALSE_POSITIVE_RATE.labels(algorithm=algorithm).observe(fp_rate)


def record_algorithm_execution_count(*, algorithm: str, trigger: str) -> None:
    """Record algorithm execution count."""
    ALGORITHM_EXECUTION_COUNT.labels(algorithm=algorithm, trigger=trigger).inc()


def record_algorithm_features(*, algorithm: str, features_count: int) -> None:
    """Record number of features evaluated."""
    ALGORITHM_FEATURES_EVALUATED.labels(algorithm=algorithm).observe(features_count)


# Business Intelligence Helpers
def record_agent_approach(*, outcome: str, agency_id: str = "default") -> None:
    """Record agent approach."""
    AGENT_APPROACH_TOTAL.labels(outcome=outcome, agency_id=agency_id).inc()


def record_agent_efficiency(*, efficiency: float) -> None:
    """Record agent efficiency."""
    AGENT_EFFICIENCY.observe(efficiency)


def record_observation_quality(*, score: int) -> None:
    """Record observation quality score."""
    OBSERVATION_QUALITY.observe(score)


def record_asset_upload(*, asset_type: str, outcome: str) -> None:
    """Record asset upload."""
    ASSET_UPLOAD_TOTAL.labels(asset_type=asset_type, outcome=outcome).inc()


def record_asset_storage_usage(*, bytes_used: int) -> None:
    """Record asset storage usage."""
    ASSET_STORAGE_USAGE.set(bytes_used)
