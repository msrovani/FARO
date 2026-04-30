"""
Redis cache layer for query results caching.
"""
import json
import hashlib
import logging
from functools import wraps
from typing import Optional, Any, Callable
from dataclasses import asdict

import redis

logger = logging.getLogger(__name__)

# Cache metrics (Otimização Fase 6)
_cache_hits = 0
_cache_misses = 0

# Import Prometheus metrics
try:
    from app.core.observability import (
        record_cache_hit,
        record_cache_miss,
        record_cache_op,
    )
    PROMETHEUS_METRICS = True
except ImportError:
    PROMETHEUS_METRICS = False


def get_cache_metrics() -> tuple[int, int]:
    """Get cache hit/miss metrics."""
    return _cache_hits, _cache_misses


def reset_cache_metrics() -> None:
    """Reset cache metrics."""
    global _cache_hits, _cache_misses
    _cache_hits = 0
    _cache_misses = 0

# Redis client singleton
_redis_client: Optional[redis.Redis] = None


def get_redis_client() -> redis.Redis:
    """
    Get or create Redis client singleton.
    With retry and resilience settings.
    
    Returns:
        Redis client instance
    """
    global _redis_client
    if _redis_client is None:
        from app.core.config import settings
        from urllib.parse import urlparse
        
        # Parse redis_url to extract host and port
        parsed = urlparse(settings.redis_url)
        host = parsed.hostname or 'localhost'
        port = parsed.port or 6379
        db = int(parsed.path[1:]) if parsed.path else 0
        
        _redis_client = redis.Redis(
            host=host,
            port=port,
            db=db,
            decode_responses=True,
            # Retry settings for resilience
            retry_on_timeout=True,
            socket_connect_timeout=5,
            socket_timeout=5,
            # Retry configuration
            retry=redis.exceptions.Retry(
                maximum=3,
                interval_start=0.1,
                interval_max=1.0,
            ),
            # Health check
            health_check_interval=30,
        )
    return _redis_client


CacheTTL = CacheTTLConfig = Optional[str]  # "short", "medium", "long"

# Cache TTL presets
CACHE_TTL_PRESETS = {
    "short": 60,    # 1 min (dados mutáveis, e.g.,-watchlist ativa)
    "medium": 300,  # 5 min (dados normais, e.g., analytics)
    "long": 3600,   # 1 hour (dados estáticos, e.g., regiões)
}


def cached_query(ttl: Optional[int] = None, preset: Optional[str] = None):
    """
    Decorator for caching query results in Redis.
    
    Args:
        ttl: Time to live in seconds (custom)
        preset: TTL preset ("short", "medium", "long")
    
    Example:
        @cached_query(ttl=60)
        async def get_active_watchlist(db: AsyncSession):
            return await db.execute(select(WatchlistEntry).where(...))
    
    Example with preset:
        @cached_query(preset="short")  # 60s
        @cached_query(preset="medium")  # 300s
        @cached_query(preset="long")  # 3600s
    """
    # Resolve TTL from preset or custom value
    if preset and preset in CACHE_TTL_PRESETS:
        _ttl = CACHE_TTL_PRESETS[preset]
    else:
        from app.core.config import settings
        _ttl = ttl or settings.cache_ttl_medium

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                redis_client = get_redis_client()
                
                # Generate cache key from function name and arguments
                key_parts = [func.__name__]
                if args:
                    key_parts.extend(str(arg) for arg in args[1:])  # Skip db session
                if kwargs:
                    key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
                cache_key = f"query_cache:{':'.join(key_parts)}"
                
                # Try to get from cache
                cached = redis_client.get(cache_key)
                if cached:
                    global _cache_hits
                    _cache_hits += 1
                    if PROMETHEUS_METRICS:
                        record_cache_hit(key_pattern=func.__name__)
                        record_cache_op(operation="get", outcome="hit")
                    return json.loads(cached)
                
                # Execute query
                result = await func(*args, **kwargs)
                
                # Record cache miss
                global _cache_misses
                _cache_misses += 1
                if PROMETHEUS_METRICS:
                    record_cache_miss(key_pattern=func.__name__)
                    record_cache_op(operation="get", outcome="miss")
                
                # Serialize and cache result
                if result is not None:
                    # Handle different result types
                    if hasattr(result, '__dict__'):
                        # Dataclass or ORM object
                        serialized = json.dumps(asdict(result), default=str)
                    elif isinstance(result, (list, tuple)):
                        # List of objects
                        serialized = json.dumps([asdict(item) if hasattr(item, '__dict__') else item for item in result], default=str)
                    else:
                        # Simple type
                        serialized = json.dumps(result, default=str)
                    
                    redis_client.setex(cache_key, ttl, serialized)
                if PROMETHEUS_METRICS:
                    record_cache_op(operation="set", outcome="success")
                
                return result
                
            except Exception as e:
                # If Redis fails, fallback to executing query without cache
                # This ensures the application continues to work even if Redis is down
                logger.warning(f"Cache error: {e} - falling back to direct query")
                return await func(*args, **kwargs)
        
        return wrapper
    return decorator


def cache_invalidate_pattern(pattern: str) -> int:
    """
    Invalidate all cache keys matching a pattern.
    
    Args:
        pattern: Redis key pattern (e.g., "query_cache:get_active_watchlist*")
    
    Returns:
        Number of keys deleted
    """
    try:
        redis_client = get_redis_client()
        keys = redis_client.keys(f"query_cache:{pattern}*")
        if keys:
            return redis_client.delete(*keys)
        return 0
    except Exception as e:
        logger.error(f"Cache invalidation error: {e}")
        return 0


def cache_clear_all() -> int:
    """
    Clear all query cache entries.
    
    Returns:
        Number of keys deleted
    """
    try:
        redis_client = get_redis_client()
        keys = redis_client.keys("query_cache:*")
        if keys:
            return redis_client.delete(*keys)
        return 0
    except Exception as e:
        logger.error(f"Cache clear error: {e}")
        return 0
