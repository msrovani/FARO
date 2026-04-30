"""
F.A.R.O. Database - Session Management
Async SQLAlchemy sessions with proper lifecycle management
"""
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.db.base import Base

# ============================================================================
# PgBouncer Auto-Detection (Hot-Swap)
# ============================================================================
import asyncpg
import time
import logging
import asyncio

logger = logging.getLogger(__name__)

# Global state for hot-swap
_pgbouncer_detected = False
_pgbouncer_available = None  # None = unknown, True/False = detected


async def detect_pgbouncer() -> bool:
    """
    Auto-detect if PgBouncer is available.
    Tries to connect to PgBouncer admin port.
    Returns True if available, False otherwise.
    """
    global _pgbouncer_available
    
    try:
        conn = await asyncio.wait_for(
            asyncpg.connect(
                host=settings.pgbouncer_host,
                port=settings.pgbouncer_port,
                user=settings.database_username,
                password=settings.database_password,
                database="pgbouncer",
                timeout=3,
            ),
            timeout=5,
        )
        await conn.close()
        _pgbouncer_available = True
        logger.info(f"PgBouncer detected at {settings.pgbouncer_host}:{settings.pgbouncer_port}")
        return True
    except asyncio.TimeoutError:
        logger.debug(f"PgBouncer connection timeout at {settings.pgbouncer_host}:{settings.pgbouncer_port}")
        _pgbouncer_available = False
        return False
    except asyncpg.CannotConnectNowError:
        logger.debug(f"PgBouncer cannot connect now (may be starting up)")
        _pgbouncer_available = False
        return False
    except asyncpg.PostgresError as e:
        logger.debug(f"PgBouncer PostgreSQL error: {e}")
        _pgbouncer_available = False
        return False
    except OSError as e:
        # Network/connection errors (host unreachable, connection refused)
        logger.debug(f"PgBouncer network error: {e}")
        _pgbouncer_available = False
        return False
    except Exception as e:
        # Catch-all for unexpected errors - log with warning
        logger.warning(f"Unexpected error detecting PgBouncer: {type(e).__name__}: {e}")
        _pgbouncer_available = False
        return False


def is_pgbouncer_available() -> bool:
    """Check if PgBouncer was detected (cached)."""
    if _pgbouncer_available is None:
        # Not yet detected - assume disabled by default
        return settings.pgbouncer_enabled
    return _pgbouncer_available and settings.pgbouncer_enabled


async def auto_detect_pgbouncer() -> None:
    """
    Auto-detect PgBouncer on startup.
    Run this once during app startup.
    
    Also records Prometheus metric for alerting:
    - faro_pgbouncer_recommended = 1 when available but NOT enabled
    """
    global _pgbouncer_detected, _pgbouncer_available
    
    if _pgbouncer_detected:
        return
    
    # If config says enabled, verify it's available
    if settings.pgbouncer_enabled:
        detected = await detect_pgbouncer()
        if detected:
            _pgbouncer_detected = True
            logger.info("PgBouncer enabled and detected - using connection pooling")
            
            # Record: PgBouncer available AND enabled = no alert
            try:
                from app.core.observability import record_pgbouncer_recommended
                record_pgbouncer_recommended(recommended=False)
            except ImportError:
                pass
        else:
            logger.warning("PgBouncer enabled but not detected - falling back to direct connection")
            _pgbouncer_detected = True
            _pgbouncer_available = False
    else:
        # Try to detect anyway for monitoring
        try:
            detected = await detect_pgbouncer()
            if detected:
                logger.info("PgBouncer detected (not configured) - pool available but NOT in use")
                # ALERTA: PgBouncer disponível mas NÃO está sendo usado!
                try:
                    from app.core.observability import record_pgbouncer_recommended
                    record_pgbouncer_recommended(recommended=True)
                except ImportError:
                    pass
            else:
                # Not detected - no alert needed
                try:
                    from app.core.observability import record_pgbouncer_recommended
                    record_pgbouncer_recommended(recommended=False)
                except ImportError:
                    pass
        except asyncio.TimeoutError:
            logger.debug("Timeout detecting PgBouncer for monitoring")
        except OSError as e:
            logger.debug(f"Network error during PgBouncer detection: {e}")
        except Exception as e:
            # Unexpected error - log with warning for investigation
            logger.warning(f"Unexpected error in PgBouncer auto-detection: {type(e).__name__}: {e}")
        _pgbouncer_detected = True


# ============================================================================
# PgBouncer Health Check
# ============================================================================


async def check_pgbouncer_health() -> dict:
    """
    Check PgBouncer connection and get pool statistics.
    Uses SHOW STATS command to get real-time metrics.
    
    Returns:
        Dict with health status and pool metrics
    """
    start_time = time.perf_counter()
    
    try:
        # Connect to PgBouncer admin database
        # Note: connection goes through PgBouncer to reach PostgreSQL
        conn = await asyncpg.connect(
            host=settings.pgbouncer_host,
            port=settings.pgbouncer_port,
            user=settings.database_username,
            password=settings.database_password,
            database="pgbouncer",  # PgBouncer admin database
            timeout=5,
        )
        
        # Get pool stats
        stats = await conn.fetch("SHOW STATS")
        await conn.close()
        
        # Calculate metrics from stats
        total_requests = sum(int(row.get('total_requests', 0) or 0) for row in stats)
        total_errors = sum(int(row.get('total_xerr', 0) or 0) for row in stats)
        
        duration = time.perf_counter() - start_time
        
        # Record Prometheus metrics if available
        try:
            from app.core.observability import record_pgbouncer_stats, record_pgbouncer_query_duration
            record_pgbouncer_stats(
                available=settings.pgbouncer_default_pool_size,
                used=min(total_requests, settings.pgbouncer_default_pool_size),
                waiting=0,
                in_use=True,
            )
            record_pgbouncer_query_duration(duration_seconds=duration)
        except ImportError:
            pass
        
        return {
            "status": "healthy",
            "pool_mode": settings.pgbouncer_pool_mode,
            "total_requests": total_requests,
            "total_errors": total_errors,
            "query_duration_ms": round(duration * 1000, 2),
        }
        
    except Exception as e:
        duration = time.perf_counter() - start_time
        return {
            "status": "unhealthy",
            "error": str(e),
            "query_duration_ms": round(duration * 1000, 2),
        }


# ============================================================================
# Database URL with PgBouncer support
# ============================================================================
def get_database_url() -> str:
    """
    Get database URL with auto-detection of PgBouncer.
    Uses hot-swap: if PgBouncer is available, use it.
    Otherwise, use direct PostgreSQL connection.
    """
    # Always use pool_size from config, regardless of PgBouncer
    # If PgBouncer is enabled AND detected, use it
    if is_pgbouncer_available():
        from urllib.parse import urlparse, urlunparse
        parsed = urlparse(settings.database_url)
        netloc = f"{parsed.hostname}:{settings.pgbouncer_port}"
        new_parsed = parsed._replace(netloc=netloc)
        return urlunparse(new_parsed)
    return settings.database_url


# Create async engine with production-ready pool settings
# Best practices: pool_pre_ping validates connections, pool_recycle prevents stale connections
engine = create_async_engine(
    get_database_url(),
    echo=settings.database_echo,
    pool_size=settings.database_pool_size,
    max_overflow=settings.database_max_overflow,
    pool_timeout=settings.database_pool_timeout,
    pool_pre_ping=settings.database_pool_pre_ping,  # Validate connections before use
    pool_recycle=settings.database_pool_recycle,  # Recycle connections hourly
    future=True,
)

# Session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for getting database sessions."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception as e:
            await session.rollback()
            raise
        finally:
            await session.close()


@asynccontextmanager
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Context manager for database sessions."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """Initialize database tables."""
    if not settings.auto_init_db:
        return
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db() -> None:
    """Close database connections."""
    await engine.dispose()


async def check_db_health() -> dict:
    """
    Check database connection pool health.
    
    Returns:
        Health status dict with pool metrics
    """
    try:
        # Force pool initialization by connecting
        from sqlalchemy import text
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        
        pool = engine.pool
        pool_size = pool.size()
        available = pool.checkedin()
        overflow = max(0, pool.overflow())
        
        # If pool is not initialized yet, return configured pool size
        if pool_size == 0:
            logger.warning(f"Pool size is 0, using configured pool size: {settings.database_pool_size}")
            pool_size = settings.database_pool_size
            available = pool_size
            overflow = 0
        
        # Record Prometheus metrics
        try:
            from app.core.observability import record_db_pool, record_db_action_needed
            record_db_pool(pool_size=pool_size, available=available, overflow=overflow)
            
            # Analyzer inteligente: DB precisa de PgBouncer?
            pgbouncer_available = False
            pgbouncer_in_use = False
            
            try:
                from app.db.session import is_pgbouncer_available
                pgbouncer_available = is_pgbouncer_available()
            except Exception as e:
                logger.debug(f"Error checking PgBouncer availability: {e}")
                pass
            
            # Analisar: DB sobrecarregado + PgBouncer necessário
            db_overloaded = overflow > 10
            if db_overloaded or pool_size - available < 5:  # menos de 5 disponiveis
                record_db_action_needed(
                    db_overloaded=True,
                    pgbouncer_available=pgbouncer_available,
                    pgbouncer_in_use=pgbouncer_available,  # usa se disponivel
                )
        except ImportError:
            pass
        
        logger.info(f"DB health check: pool_size={pool_size}, available={available}, overflow={overflow}")
        return {
            "status": "healthy",
            "pool_size": pool_size,
            "overflow": overflow,
            "checked_in": available,
            "checked_out": pool_size - available,
            "invalid": pool.invalidatedcount() if hasattr(pool, 'invalidatedcount') else 0,
        }
    except Exception as e:
        logger.error(f"DB health check failed: {e}", exc_info=True)
        return {
            "status": "unhealthy",
            "error": str(e),
        }
