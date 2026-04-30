"""
Cache Service - Server-side caching with Redis for performance optimization.

Features:
- Cache of frequently accessed data (queue, watchlist, etc.)
- Intelligent cache invalidation
- TTL-based expiration
- Cache hit/miss metrics
- Distributed caching with Redis
"""
import json
import logging
from datetime import timedelta
from typing import Any, Optional, List, Dict
from uuid import uuid4

import redis.asyncio as redis
from redis.asyncio import Redis

from app.core.config import settings
from app.db.session import get_db
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class CacheService:
    """
    Server-side cache service using Redis.
    """
    
    def __init__(self):
        self.redis: Optional[Redis] = None
        self.enabled = settings.redis_enabled
        self.default_ttl = timedelta(minutes=5)
        
    async def initialize(self):
        """Initialize Redis connection."""
        if not self.enabled:
            logger.info("Redis caching disabled")
            return
            
        try:
            self.redis = await redis.from_url(
                settings.redis_url,
                encoding="utf-8",
                decode_responses=True
            )
            # Test connection
            await self.redis.ping()
            logger.info("Redis cache initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Redis: {e}")
            self.enabled = False
    
    async def close(self):
        """Close Redis connection."""
        if self.redis:
            await self.redis.close()
            logger.info("Redis cache closed")
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        if not self.enabled or not self.redis:
            return None
            
        try:
            value = await self.redis.get(key)
            if value:
                logger.debug(f"Cache hit: {key}")
                return json.loads(value)
            else:
                logger.debug(f"Cache miss: {key}")
                return None
        except Exception as e:
            logger.error(f"Cache get error for key {key}: {e}")
            return None
    
    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[timedelta] = None
    ) -> bool:
        """Set value in cache with optional TTL."""
        if not self.enabled or not self.redis:
            return False
            
        try:
            ttl = ttl or self.default_ttl
            serialized = json.dumps(value, default=str)
            await self.redis.setex(key, int(ttl.total_seconds()), serialized)
            logger.debug(f"Cache set: {key} (TTL: {ttl.total_seconds()}s)")
            return True
        except Exception as e:
            logger.error(f"Cache set error for key {key}: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete value from cache."""
        if not self.enabled or not self.redis:
            return False
            
        try:
            await self.redis.delete(key)
            logger.debug(f"Cache deleted: {key}")
            return True
        except Exception as e:
            logger.error(f"Cache delete error for key {key}: {e}")
            return False
    
    async def invalidate_pattern(self, pattern: str) -> int:
        """Invalidate all keys matching pattern."""
        if not self.enabled or not self.redis:
            return 0
            
        try:
            keys = []
            async for key in self.redis.scan_iter(match=pattern):
                keys.append(key)
            
            if keys:
                await self.redis.delete(*keys)
                logger.info(f"Invalidated {len(keys)} keys matching pattern: {pattern}")
            
            return len(keys)
        except Exception as e:
            logger.error(f"Cache invalidate pattern error for {pattern}: {e}")
            return 0
    
    async def get_cached_queue(
        self,
        user_id: str,
        filters: Optional[Dict] = None
    ) -> Optional[List]:
        """Get cached intelligence queue for user."""
        cache_key = f"queue:user:{user_id}"
        if filters:
            # Include filters in cache key for different filter combinations
            filter_str = json.dumps(filters, sort_keys=True)
            cache_key = f"{cache_key}:filters:{hash(filter_str)}"
        
        return await self.get(cache_key)
    
    async def cache_queue(
        self,
        user_id: str,
        queue: List,
        filters: Optional[Dict] = None
    ) -> bool:
        """Cache intelligence queue for user."""
        cache_key = f"queue:user:{user_id}"
        if filters:
            filter_str = json.dumps(filters, sort_keys=True)
            cache_key = f"{cache_key}:filters:{hash(filter_str)}"
        
        return await self.set(cache_key, queue, timedelta(minutes=10))
    
    async def get_cached_watchlist(self) -> Optional[List]:
        """Get cached active watchlist entries."""
        return await self.get("watchlist:active")
    
    async def cache_watchlist(self, entries: List) -> bool:
        """Cache active watchlist entries."""
        return await self.set("watchlist:active", entries, timedelta(minutes=30))
    
    async def get_cached_route_regions(self) -> Optional[List]:
        """Get cached active route regions."""
        return await self.get("route_regions:active")
    
    async def cache_route_regions(self, regions: List) -> bool:
        """Cache active route regions."""
        return await self.set("route_regions:active", regions, timedelta(hours=2))
    
    async def get_cached_sensitive_zones(self) -> Optional[List]:
        """Get cached active sensitive zones."""
        return await self.get("sensitive_zones:active")
    
    async def cache_sensitive_zones(self, zones: List) -> bool:
        """Cache active sensitive zones."""
        return await self.set("sensitive_zones:active", zones, timedelta(hours=2))
    
    async def get_cached_algorithm_result(
        self,
        algorithm_type: str,
        observation_id: str,
        parameters_hash: str
    ) -> Optional[Dict]:
        """Get cached algorithm result."""
        cache_key = f"algorithm:{algorithm_type}:{observation_id}:{parameters_hash}"
        return await self.get(cache_key)
    
    async def cache_algorithm_result(
        self,
        algorithm_type: str,
        observation_id: str,
        parameters_hash: str,
        result: Dict,
        ttl: timedelta = timedelta(minutes=15)
    ) -> bool:
        """Cache algorithm result."""
        cache_key = f"algorithm:{algorithm_type}:{observation_id}:{parameters_hash}"
        return await self.set(cache_key, result, ttl)
    
    async def get_cached_plate_lookup(self, plate: str) -> Optional[Dict]:
        """Get cached plate lookup result."""
        return await self.get(f"plate_lookup:{plate}")
    
    async def cache_plate_lookup(self, plate: str, result: Dict) -> bool:
        """Cache plate lookup result."""
        return await self.set(f"plate_lookup:{plate}", result, timedelta(hours=6))
    
    async def get_cached_intercept_score(self, observation_id: str) -> Optional[float]:
        """Get cached INTERCEPT score."""
        return await self.get(f"intercept_score:{observation_id}")
    
    async def cache_intercept_score(self, observation_id: str, score: float) -> bool:
        """Cache INTERCEPT score."""
        return await self.set(f"intercept_score:{observation_id}", score, timedelta(hours=1))
    
    async def invalidate_algorithm_cache(self, algorithm_type: str) -> int:
        """Invalidate all cache entries for specific algorithm."""
        pattern = f"algorithm:{algorithm_type}:*"
        return await self.invalidate_pattern(pattern)
    
    async def invalidate_watchlist_cache(self) -> int:
        """Invalidate watchlist cache."""
        return await self.invalidate_pattern("watchlist:*")
    
    async def get_cache_stats(self) -> Dict:
        """Get cache performance statistics."""
        if not self.enabled or not self.redis:
            return {"enabled": False}
        
        try:
            info = await self.redis.info()
            return {
                "enabled": True,
                "connected_clients": info.get("connected_clients", 0),
                "used_memory": info.get("used_memory_human", "0B"),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0),
                "hit_rate": (
                    info.get("keyspace_hits", 0) / 
                    max(info.get("keyspace_hits", 0) + info.get("keyspace_misses", 0), 1)
                ) * 100
            }
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return {"enabled": True, "error": str(e)}


# Global cache service instance
cache_service = CacheService()
