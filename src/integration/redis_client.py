"""Redis cache integration

Provides caching for sessions, embeddings, and search results.
"""

import asyncio
import logging
from typing import Any, Optional, List
import json
import redis.asyncio as redis
from redis.asyncio import Redis
from datetime import timedelta

logger = logging.getLogger(__name__)


class RedisCache:
    """Redis cache client for session and data caching"""
    
    def __init__(
        self,
        url: str = "redis://localhost:6379/0",
        default_ttl: int = 86400,  # 24 hours
    ):
        """
        Initialize Redis cache
        
        Args:
            url: Redis connection URL
            default_ttl: Default time-to-live in seconds
        """
        self.url = url
        self.default_ttl = default_ttl
        self.client: Optional[Redis] = None
    
    async def init(self) -> None:
        """
        Initialize connection to Redis
        
        Raises:
            Exception: If connection fails
        """
        try:
            self.client = await redis.from_url(self.url, decode_responses=True)
            
            # Test connection
            await self.client.ping()
            
            logger.info(f"✓ Redis cache initialized (url={self.url})")
        except Exception as e:
            logger.error(f"✗ Failed to initialize Redis: {e}")
            raise
    
    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
    ) -> bool:
        """
        Set cache value
        
        Args:
            key: Cache key
            value: Value to cache (will be JSON serialized)
            ttl: Time-to-live in seconds (uses default if None)
            
        Returns:
            Success flag
        """
        if not self.client:
            raise RuntimeError("Redis client not initialized")
        
        try:
            serialized = json.dumps(value) if not isinstance(value, str) else value
            ttl = ttl or self.default_ttl
            
            await self.client.setex(
                key,
                ttl,
                serialized,
            )
            logger.debug(f"✓ Cached key: {key} (ttl={ttl}s)")
            return True
        except Exception as e:
            logger.error(f"✗ Failed to set cache: {e}")
            raise
    
    async def get(self, key: str) -> Optional[Any]:
        """
        Get cached value
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found
        """
        if not self.client:
            raise RuntimeError("Redis client not initialized")
        
        try:
            value = await self.client.get(key)
            if value:
                try:
                    return json.loads(value)
                except json.JSONDecodeError:
                    return value
            logger.debug(f"✓ Retrieved cache key: {key}")
            return None
        except Exception as e:
            logger.error(f"✗ Failed to get cache: {e}")
            raise
    
    async def delete(self, key: str) -> bool:
        """
        Delete cached value
        
        Args:
            key: Cache key
            
        Returns:
            Success flag
        """
        if not self.client:
            raise RuntimeError("Redis client not initialized")
        
        try:
            result = await self.client.delete(key)
            logger.debug(f"✓ Deleted cache key: {key}")
            return result > 0
        except Exception as e:
            logger.error(f"✗ Failed to delete cache: {e}")
            raise
    
    async def exists(self, key: str) -> bool:
        """
        Check if key exists
        
        Args:
            key: Cache key
            
        Returns:
            True if exists, False otherwise
        """
        if not self.client:
            raise RuntimeError("Redis client not initialized")
        
        try:
            return await self.client.exists(key) > 0
        except Exception as e:
            logger.error(f"✗ Failed to check cache existence: {e}")
            raise
    
    async def get_or_set(
        self,
        key: str,
        factory,
        ttl: Optional[int] = None,
    ) -> Any:
        """
        Get value from cache or compute and set it
        
        Args:
            key: Cache key
            factory: Async callable to compute value if not cached
            ttl: Time-to-live in seconds
            
        Returns:
            Cached or computed value
        """
        # Try to get from cache
        cached = await self.get(key)
        if cached is not None:
            logger.debug(f"✓ Cache hit: {key}")
            return cached
        
        # Compute value
        logger.debug(f"✓ Cache miss: {key}, computing value")
        if asyncio.iscoroutinefunction(factory):
            value = await factory()
        else:
            value = factory()
        
        # Store in cache
        await self.set(key, value, ttl)
        return value
    
    async def set_multiple(
        self,
        data: dict,
        ttl: Optional[int] = None,
    ) -> bool:
        """
        Set multiple cache values
        
        Args:
            data: Dictionary of {key: value} pairs
            ttl: Time-to-live in seconds
            
        Returns:
            Success flag
        """
        if not self.client:
            raise RuntimeError("Redis client not initialized")
        
        try:
            ttl = ttl or self.default_ttl
            
            for key, value in data.items():
                serialized = json.dumps(value) if not isinstance(value, str) else value
                await self.client.setex(key, ttl, serialized)
            
            logger.debug(f"✓ Cached {len(data)} keys")
            return True
        except Exception as e:
            logger.error(f"✗ Failed to set multiple cache values: {e}")
            raise
    
    async def get_multiple(self, keys: List[str]) -> dict:
        """
        Get multiple cached values
        
        Args:
            keys: List of cache keys
            
        Returns:
            Dictionary of {key: value} for found keys
        """
        if not self.client:
            raise RuntimeError("Redis client not initialized")
        
        try:
            values = await self.client.mget(keys)
            result = {}
            
            for key, value in zip(keys, values):
                if value:
                    try:
                        result[key] = json.loads(value)
                    except json.JSONDecodeError:
                        result[key] = value
            
            logger.debug(f"✓ Retrieved {len(result)} out of {len(keys)} cache keys")
            return result
        except Exception as e:
            logger.error(f"✗ Failed to get multiple cache values: {e}")
            raise
    
    async def clear_pattern(self, pattern: str) -> int:
        """
        Delete all keys matching pattern
        
        Args:
            pattern: Key pattern (e.g., "session:*")
            
        Returns:
            Number of keys deleted
        """
        if not self.client:
            raise RuntimeError("Redis client not initialized")
        
        try:
            keys = await self.client.keys(pattern)
            if keys:
                count = await self.client.delete(*keys)
                logger.debug(f"✓ Cleared {count} cache keys matching pattern: {pattern}")
                return count
            return 0
        except Exception as e:
            logger.error(f"✗ Failed to clear cache pattern: {e}")
            raise
    
    async def increment(self, key: str, amount: int = 1) -> int:
        """
        Increment numeric cache value
        
        Args:
            key: Cache key
            amount: Amount to increment
            
        Returns:
            New value
        """
        if not self.client:
            raise RuntimeError("Redis client not initialized")
        
        try:
            value = await self.client.incrby(key, amount)
            logger.debug(f"✓ Incremented cache key: {key} (value={value})")
            return value
        except Exception as e:
            logger.error(f"✗ Failed to increment cache key: {e}")
            raise
    
    async def get_cache_stats(self) -> dict:
        """
        Get cache statistics
        
        Returns:
            Cache stats including memory usage, connected clients, etc.
        """
        if not self.client:
            raise RuntimeError("Redis client not initialized")
        
        try:
            info = await self.client.info()
            return {
                "connected_clients": info.get("connected_clients", 0),
                "used_memory": info.get("used_memory_human", "N/A"),
                "keys_count": await self.client.dbsize(),
                "uptime_seconds": info.get("uptime_in_seconds", 0),
            }
        except Exception as e:
            logger.error(f"✗ Failed to get cache stats: {e}")
            raise
    
    async def close(self) -> None:
        """Close Redis connection"""
        try:
            if self.client:
                await self.client.close()
                self.client = None
                logger.info("✓ Redis connection closed")
        except Exception as e:
            logger.error(f"✗ Failed to close Redis connection: {e}")
            raise


# Global Redis cache instance
_redis_cache: Optional[RedisCache] = None


async def init_redis_cache(
    url: str = "redis://localhost:6379/0",
    default_ttl: int = 86400,
) -> None:
    """
    Initialize global Redis cache
    
    Args:
        url: Redis connection URL
        default_ttl: Default time-to-live in seconds
    """
    global _redis_cache
    _redis_cache = RedisCache(url, default_ttl)
    await _redis_cache.init()


async def close_redis_cache() -> None:
    """Close global Redis cache"""
    global _redis_cache
    if _redis_cache:
        await _redis_cache.close()
        _redis_cache = None


def get_redis_cache() -> RedisCache:
    """Get global Redis cache"""
    if _redis_cache is None:
        raise RuntimeError("Redis cache not initialized. Call init_redis_cache() first.")
    return _redis_cache
