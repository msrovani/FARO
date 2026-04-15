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

import structlog
from fastapi import FastAPI, Request, Response
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import settings


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


class PrometheusMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        path = request.url.path
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
