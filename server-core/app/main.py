"""
F.A.R.O. Server Core - FastAPI Application Entry Point
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.observability import configure_logging, setup_metrics, setup_tracing
from app.core.rate_limit import InMemoryRateLimitMiddleware
from app.db.session import init_db, close_db
from app.api.routes import api_router
from app.core.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerConfig,
    get_circuit_breaker,
    get_endpoint_circuit_breaker,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler for startup/shutdown events."""
    # Startup
    await init_db()
    
    # Auto-detect PgBouncer (hot-swap)
    from app.db.session import auto_detect_pgbouncer, is_pgbouncer_available
    await auto_detect_pgbouncer()
    print(f"PgBouncer auto-detection complete - pool: {is_pgbouncer_available()}")

    # Pré-carregar modelos OCR para eliminar cold start
    # DESABILITADO TEMPORARIAMENTE - modelos não encontrados
    # try:
    #     from app.services.ocr_service import get_ocr_service
    #     ocr_service = get_ocr_service()
    #     ocr_service._load_models()
    #     print("OCR models loaded successfully on startup")
    # except Exception as e:
    #     print(f"Failed to preload OCR models: {e}")
    print("OCR model preload disabled - models will be loaded on demand")

    # Initialize performance monitoring configurations
    from app.utils.performance_monitor import get_performance_monitor
    from app.core.config import settings

    monitor = get_performance_monitor()

    # Register configurations for different task types
    monitor.register_config(
        task_type="ocr_processing",
        current_workers=settings.process_pool_max_workers
        if isinstance(settings.process_pool_max_workers, int)
        else 4,
        current_batch_size=8,
        min_workers=1,
        max_workers=32,
        min_batch_size=1,
        max_batch_size=32,
        target_p95_ms=1000,
        target_p99_ms=2000,
    )

    monitor.register_config(
        task_type="ocr_batch",
        current_workers=settings.process_pool_max_workers
        if isinstance(settings.process_pool_max_workers, int)
        else 4,
        current_batch_size=16,
        min_workers=2,
        max_workers=16,
        min_batch_size=4,
        max_batch_size=64,
        target_p95_ms=5000,
        target_p99_ms=10000,
    )

    monitor.register_config(
        task_type="route_recurrence",
        current_workers=settings.process_pool_cpu_bound_workers
        if isinstance(settings.process_pool_cpu_bound_workers, int)
        else 4,
        current_batch_size=1,
        min_workers=1,
        max_workers=8,
        min_batch_size=1,
        max_batch_size=4,
        target_p95_ms=500,
        target_p99_ms=1000,
    )

    monitor.register_config(
        task_type="route_direction",
        current_workers=settings.process_pool_cpu_bound_workers
        if isinstance(settings.process_pool_cpu_bound_workers, int)
        else 4,
        current_batch_size=1,
        min_workers=1,
        max_workers=8,
        min_batch_size=1,
        max_batch_size=4,
        target_p95_ms=200,
        target_p99_ms=500,
    )

    monitor.register_config(
        task_type="hotspot_clustering",
        current_workers=settings.process_pool_cpu_bound_workers
        if isinstance(settings.process_pool_cpu_bound_workers, int)
        else 4,
        current_batch_size=1,
        min_workers=1,
        max_workers=8,
        min_batch_size=1,
        max_batch_size=4,
        target_p95_ms=2000,
        target_p99_ms=5000,
    )

    yield
    # Shutdown
    from app.utils.process_pool import shutdown_process_pool

    shutdown_process_pool()
    await close_db()


def create_application() -> FastAPI:
    """Create and configure FastAPI application."""
    configure_logging()
    app = FastAPI(
        title=settings.app_name,
        description=settings.app_description,
        version=settings.app_version,
        docs_url="/docs" if not settings.is_production else None,
        redoc_url="/redoc" if not settings.is_production else None,
        openapi_url="/openapi.json" if not settings.is_production else None,
        lifespan=lifespan,
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=settings.cors_allow_credentials,
        allow_methods=settings.cors_allow_methods,
        allow_headers=settings.cors_allow_headers,
    )

    # Gzip compression
    app.add_middleware(GZipMiddleware, minimum_size=1000)
    setup_metrics(app)
    setup_tracing(app)

    # Baseline API abuse protection
    app.add_middleware(
        InMemoryRateLimitMiddleware,
        requests=settings.rate_limit_requests,
        window_seconds=settings.rate_limit_window,
        exempt_paths={"/health", "/"},
    )

    # Include API router
    app.include_router(
        api_router,
        prefix="/api/v1",
    )

    # Exception handler
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        return JSONResponse(
            status_code=500,
            content={
                "error": "Erro Interno do Servidor",
                "message": str(exc)
                if settings.debug
                else "An unexpected error occurred",
            },
        )

    # Health check endpoint
    @app.get("/health", tags=["Health"])
    async def health_check():
        # Get circuit breaker statuses
        circuit_breaker_status = {}
        from app.core.circuit_breaker import get_circuit_breaker
        for name in ["mobile_sync", "ocr_processing", "algorithm_execution", "database_query"]:
            try:
                cb = get_circuit_breaker(name)
                circuit_breaker_status[name] = cb.get_status()
            except Exception:
                pass
        
        # Get DB pool status and record Prometheus metrics
        db_pool_status = {}
        try:
            from app.db.session import check_db_health
            db_pool_status = await check_db_health()
        except Exception:
            pass
        
        # Get PgBouncer status (auto-detected)
        pgbouncer_status = {}
        try:
            from app.db.session import check_pgbouncer_health, is_pgbouncer_available
            if is_pgbouncer_available():
                pgbouncer_status = await check_pgbouncer_health()
            else:
                pgbouncer_status = {"status": "disabled"}
        except Exception as e:
            pgbouncer_status = {"status": "error", "error": str(e)}
        
        return {
            "status": "healthy",
            "service": settings.app_name,
            "version": settings.app_version,
            "circuit_breakers": circuit_breaker_status,
            "database_pool": db_pool_status,
            "pgbouncer": pgbouncer_status,
        }

    # Root endpoint
    @app.get("/", tags=["Root"])
    async def root():
        return {
            "name": settings.app_name,
            "version": settings.app_version,
            "description": settings.app_description,
            "docs": "/docs" if not settings.is_production else None,
        }

    return app


# Create application instance
app = create_application()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.reload,
        workers=settings.workers if not settings.reload else 1,
    )
