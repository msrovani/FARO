"""
F.A.R.O. Cache Manager - Optimized Redis Caching
Implements cache-aside pattern with intelligent TTL strategies
Based on Redis best practices for production workloads
"""
import json
import logging
from typing import Any, Optional, Callable, TypeVar
from functools import wraps

import redis.asyncio as redis
from redis.asyncio import Redis

from app.core.config import settings

logger = logging.getLogger(__name__)

T = TypeVar('T')


class CacheManager:
    """
    Production-ready cache manager with cache-aside pattern.
    
    Best practices implemented:
    - Cache-aside (lazy loading) for read-heavy workloads
    - Configurable TTLs per data type
    - Automatic serialization/deserialization
    - Graceful degradation on Redis failures
    - Connection pooling
    """
    
    def __init__(self):
        self._redis: Optional[Redis] = None
        self._enabled = True
    
    async def connect(self) -> None:
        """Initialize Redis connection with connection pooling."""
        try:
            self._redis = await redis.from_url(
                settings.redis_cache_url,
                encoding="utf-8",
                decode_responses=True,
                socket_timeout=settings.redis_socket_timeout,
                socket_connect_timeout=settings.redis_socket_connect_timeout,
                max_connections=50,  # Connection pool size
                health_check_interval=30,
            )
            # Test connection
            await self._redis.ping()
            logger.info("Cache manager connected to Redis")
        except Exception as e:
            logger.warning(f"Failed to connect to Redis cache: {e}. Cache disabled.")
            self._enabled = False
            self._redis = None
    
    async def close(self) -> None:
        """Close Redis connection."""
        if self._redis:
            await self._redis.close()
            logger.info("Cache manager disconnected from Redis")
    
    def _get_key(self, prefix: str, identifier: str) -> str:
        """Generate cache key with prefix."""
        return f"{prefix}:{identifier}"
    
    async def get(
        self,
        prefix: str,
        identifier: str,
        ttl_type: str = "medium"
    ) -> Optional[Any]:
        """
        Get value from cache (cache-aside pattern).
        
        Args:
            prefix: Cache key prefix (e.g., "user", "observation")
            identifier: Unique identifier for the data
            ttl_type: TTL category ("short", "medium", "long")
        
        Returns:
            Cached value or None if not found
        """
        if not self._enabled or not self._redis:
            return None
        
        try:
            key = self._get_key(prefix, identifier)
            value = await self._redis.get(key)
            
            if value:
                logger.debug(f"Cache hit: {key}")
                return json.loads(value)
            
            logger.debug(f"Cache miss: {key}")
            return None
        except Exception as e:
            logger.error(f"Cache get error: {e}")
            return None
    
    async def set(
        self,
        prefix: str,
        identifier: str,
        value: Any,
        ttl_type: str = "medium"
    ) -> bool:
        """
        Set value in cache with appropriate TTL.
        
        Args:
            prefix: Cache key prefix
            identifier: Unique identifier
            value: Value to cache (must be JSON serializable)
            ttl_type: TTL category
        
        Returns:
            True if successful, False otherwise
        """
        if not self._enabled or not self._redis:
            return False
        
        try:
            key = self._get_key(prefix, identifier)
            
            # Get TTL based on type
            ttl = self._get_ttl(ttl_type)
            
            # Serialize value
            serialized = json.dumps(value)
            
            # Set with TTL
            await self._redis.setex(key, ttl, serialized)
            logger.debug(f"Cache set: {key} (TTL: {ttl}s)")
            return True
        except Exception as e:
            logger.error(f"Cache set error: {e}")
            return False
    
    async def delete(self, prefix: str, identifier: str) -> bool:
        """
        Delete value from cache.
        
        Args:
            prefix: Cache key prefix
            identifier: Unique identifier
        
        Returns:
            True if successful, False otherwise
        """
        if not self._enabled or not self._redis:
            return False
        
        try:
            key = self._get_key(prefix, identifier)
            await self._redis.delete(key)
            logger.debug(f"Cache delete: {key}")
            return True
        except Exception as e:
            logger.error(f"Cache delete error: {e}")
            return False
    
    async def invalidate_pattern(self, pattern: str) -> int:
        """
        Invalidate all keys matching a pattern.
        
        WARNING: Use with caution - SCAN is preferred over KEYS in production.
        
        Args:
            pattern: Redis key pattern (e.g., "user:*")
        
        Returns:
            Number of keys deleted
        """
        if not self._enabled or not self._redis:
            return 0
        
        try:
            # Use SCAN instead of KEYS for production safety
            count = 0
            async for key in self._redis.scan_iter(match=pattern):
                await self._redis.delete(key)
                count += 1
            
            logger.info(f"Cache pattern invalidation: {pattern} ({count} keys)")
            return count
        except Exception as e:
            logger.error(f"Cache pattern invalidation error: {e}")
            return 0
    
    def _get_ttl(self, ttl_type: str) -> int:
        """Get TTL based on type."""
        ttl_map = {
            "short": settings.cache_ttl_short,
            "medium": settings.cache_ttl_medium,
            "long": settings.cache_ttl_long,
        }
        return ttl_map.get(ttl_type, settings.cache_ttl_medium)
    
    async def get_or_set(
        self,
        prefix: str,
        identifier: str,
        fetch_func: Callable[[], Any],
        ttl_type: str = "medium"
    ) -> Any:
        """
        Get from cache or fetch and set (cache-aside pattern).
        
        This is the primary method for cache-aside pattern.
        
        Args:
            prefix: Cache key prefix
            identifier: Unique identifier
            fetch_func: Async function to fetch data if cache miss
            ttl_type: TTL category
        
        Returns:
            Cached or fetched value
        """
        # Try to get from cache
        cached = await self.get(prefix, identifier, ttl_type)
        if cached is not None:
            return cached
        
        # Cache miss - fetch from source
        value = await fetch_func()
        
        # Set in cache for future requests
        if value is not None:
            await self.set(prefix, identifier, value, ttl_type)
        
        return value


# Global cache manager instance
cache_manager = CacheManager()


def cached(
    prefix: str,
    ttl_type: str = "medium",
    identifier_func: Optional[Callable] = None
):
    """
    Decorator for caching function results.
    
    Args:
        prefix: Cache key prefix
        ttl_type: TTL category
        identifier_func: Function to generate identifier from args
    
    Example:
        @cached(prefix="user", ttl_type="medium")
        async def get_user(user_id: str):
            return await db.get_user(user_id)
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            # Generate identifier
            if identifier_func:
                identifier = identifier_func(*args, **kwargs)
            else:
                identifier = str(args) + str(kwargs)
            
            # Try cache
            cached = await cache_manager.get(prefix, identifier, ttl_type)
            if cached is not None:
                return cached
            
            # Cache miss - execute function
            result = await func(*args, **kwargs)
            
            # Set cache
            if result is not None:
                await cache_manager.set(prefix, identifier, result, ttl_type)
            
            return result
        return wrapper
    return decorator
