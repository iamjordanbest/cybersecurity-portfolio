"""
Redis Cache Manager for GRC Analytics Platform.

Provides caching capabilities for frequently accessed data including:
- Risk scores
- Compliance summaries
- Trend data
- Control information
"""

import redis
import pickle
import logging
from typing import Any, Optional, List, Dict
from datetime import timedelta
import json

logger = logging.getLogger(__name__)


class CacheManager:
    """
    Redis-based cache manager with automatic serialization and TTL support.
    
    Features:
    - Automatic pickle serialization for complex Python objects
    - Configurable TTL (time-to-live) for each key
    - Pattern-based cache invalidation
    - Connection health checking
    - Graceful fallback when Redis unavailable
    """
    
    # Default TTL values (in seconds)
    TTL_SHORT = 300      # 5 minutes
    TTL_MEDIUM = 3600    # 1 hour
    TTL_LONG = 86400     # 24 hours
    TTL_WEEK = 604800    # 7 days
    
    # Cache key prefixes
    PREFIX_RISK = "risk_scores"
    PREFIX_COMPLIANCE = "compliance"
    PREFIX_TREND = "trends"
    PREFIX_CONTROL = "controls"
    PREFIX_ROI = "roi"
    PREFIX_THREAT = "threats"
    
    def __init__(self, host='localhost', port=6379, db=0, enabled=True):
        """
        Initialize Redis cache manager.
        
        Args:
            host: Redis server hostname
            port: Redis server port
            db: Redis database number (0-15)
            enabled: Whether caching is enabled (useful for testing)
        """
        self.enabled = enabled
        self.redis_client = None
        
        if self.enabled:
            try:
                self.redis_client = redis.Redis(
                    host=host,
                    port=port,
                    db=db,
                    decode_responses=False,  # Handle binary data
                    socket_connect_timeout=5,
                    socket_timeout=5,
                    retry_on_timeout=True
                )
                # Test connection
                self.redis_client.ping()
                logger.info(f"Redis cache connected: {host}:{port} (db={db})")
            except (redis.ConnectionError, redis.TimeoutError) as e:
                logger.warning(f"Redis connection failed: {e}. Cache disabled.")
                self.enabled = False
                self.redis_client = None
    
    def is_available(self) -> bool:
        """Check if Redis cache is available."""
        if not self.enabled or not self.redis_client:
            return False
        try:
            self.redis_client.ping()
            return True
        except Exception:
            return False
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found or cache unavailable
        """
        if not self.is_available():
            return None
        
        try:
            data = self.redis_client.get(key)
            if data:
                logger.debug(f"Cache HIT: {key}")
                return pickle.loads(data)
            logger.debug(f"Cache MISS: {key}")
            return None
        except Exception as e:
            logger.error(f"Cache get error for key '{key}': {e}")
            return None
    
    def set(self, key: str, value: Any, ttl: int = TTL_MEDIUM) -> bool:
        """
        Set value in cache with TTL.
        
        Args:
            key: Cache key
            value: Value to cache (will be pickled)
            ttl: Time to live in seconds
            
        Returns:
            True if successful, False otherwise
        """
        if not self.is_available():
            return False
        
        try:
            serialized = pickle.dumps(value)
            self.redis_client.setex(key, ttl, serialized)
            logger.debug(f"Cache SET: {key} (TTL={ttl}s)")
            return True
        except Exception as e:
            logger.error(f"Cache set error for key '{key}': {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """
        Delete key from cache.
        
        Args:
            key: Cache key to delete
            
        Returns:
            True if key was deleted, False otherwise
        """
        if not self.is_available():
            return False
        
        try:
            deleted = self.redis_client.delete(key)
            logger.debug(f"Cache DELETE: {key} (deleted={deleted})")
            return deleted > 0
        except Exception as e:
            logger.error(f"Cache delete error for key '{key}': {e}")
            return False
    
    def invalidate_pattern(self, pattern: str) -> int:
        """
        Invalidate all keys matching pattern.
        
        Args:
            pattern: Redis pattern (e.g., "risk_scores:*")
            
        Returns:
            Number of keys deleted
        """
        if not self.is_available():
            return 0
        
        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                deleted = self.redis_client.delete(*keys)
                logger.info(f"Cache INVALIDATE: {pattern} ({deleted} keys)")
                return deleted
            return 0
        except Exception as e:
            logger.error(f"Cache invalidate error for pattern '{pattern}': {e}")
            return 0
    
    def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        if not self.is_available():
            return False
        
        try:
            return self.redis_client.exists(key) > 0
        except Exception as e:
            logger.error(f"Cache exists error for key '{key}': {e}")
            return False
    
    def get_ttl(self, key: str) -> Optional[int]:
        """
        Get remaining TTL for key.
        
        Args:
            key: Cache key
            
        Returns:
            Remaining TTL in seconds, -1 if no TTL, None if key doesn't exist
        """
        if not self.is_available():
            return None
        
        try:
            ttl = self.redis_client.ttl(key)
            if ttl == -2:  # Key doesn't exist
                return None
            return ttl
        except Exception as e:
            logger.error(f"Cache TTL error for key '{key}': {e}")
            return None
    
    def get_many(self, keys: List[str]) -> Dict[str, Any]:
        """
        Get multiple keys at once.
        
        Args:
            keys: List of cache keys
            
        Returns:
            Dictionary of {key: value} for found keys
        """
        if not self.is_available() or not keys:
            return {}
        
        try:
            pipe = self.redis_client.pipeline()
            for key in keys:
                pipe.get(key)
            results = pipe.execute()
            
            result_dict = {}
            for key, data in zip(keys, results):
                if data:
                    try:
                        result_dict[key] = pickle.loads(data)
                    except Exception as e:
                        logger.error(f"Error unpickling key '{key}': {e}")
            
            logger.debug(f"Cache GET_MANY: {len(result_dict)}/{len(keys)} hits")
            return result_dict
        except Exception as e:
            logger.error(f"Cache get_many error: {e}")
            return {}
    
    def set_many(self, items: Dict[str, Any], ttl: int = TTL_MEDIUM) -> int:
        """
        Set multiple keys at once.
        
        Args:
            items: Dictionary of {key: value}
            ttl: Time to live in seconds
            
        Returns:
            Number of keys successfully set
        """
        if not self.is_available() or not items:
            return 0
        
        try:
            pipe = self.redis_client.pipeline()
            for key, value in items.items():
                serialized = pickle.dumps(value)
                pipe.setex(key, ttl, serialized)
            pipe.execute()
            
            logger.debug(f"Cache SET_MANY: {len(items)} keys (TTL={ttl}s)")
            return len(items)
        except Exception as e:
            logger.error(f"Cache set_many error: {e}")
            return 0
    
    def increment(self, key: str, amount: int = 1) -> Optional[int]:
        """
        Increment a counter.
        
        Args:
            key: Cache key
            amount: Amount to increment by
            
        Returns:
            New value or None if error
        """
        if not self.is_available():
            return None
        
        try:
            return self.redis_client.incrby(key, amount)
        except Exception as e:
            logger.error(f"Cache increment error for key '{key}': {e}")
            return None
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dictionary with cache stats
        """
        if not self.is_available():
            return {"enabled": False, "available": False}
        
        try:
            info = self.redis_client.info()
            db_info = self.redis_client.info('keyspace')
            
            # Parse database info
            db_keys = 0
            if 'db0' in db_info:
                db_stats = db_info['db0']
                db_keys = db_stats.get('keys', 0)
            
            return {
                "enabled": True,
                "available": True,
                "total_keys": db_keys,
                "memory_used_mb": round(info.get('used_memory', 0) / 1024 / 1024, 2),
                "memory_peak_mb": round(info.get('used_memory_peak', 0) / 1024 / 1024, 2),
                "connected_clients": info.get('connected_clients', 0),
                "uptime_seconds": info.get('uptime_in_seconds', 0),
                "hit_rate": self._calculate_hit_rate(info)
            }
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return {"enabled": True, "available": False, "error": str(e)}
    
    def _calculate_hit_rate(self, info: Dict) -> Optional[float]:
        """Calculate cache hit rate from Redis info."""
        hits = info.get('keyspace_hits', 0)
        misses = info.get('keyspace_misses', 0)
        total = hits + misses
        
        if total == 0:
            return None
        
        return round((hits / total) * 100, 2)
    
    def clear_all(self) -> bool:
        """
        Clear all keys in current database.
        
        WARNING: This deletes ALL keys in the database!
        
        Returns:
            True if successful
        """
        if not self.is_available():
            return False
        
        try:
            self.redis_client.flushdb()
            logger.warning("Cache FLUSH: All keys deleted")
            return True
        except Exception as e:
            logger.error(f"Cache clear error: {e}")
            return False
    
    # Convenience methods for common cache patterns
    
    def cache_risk_scores(self, control_id: str, scores: Dict[str, Any], 
                         ttl: int = TTL_LONG) -> bool:
        """Cache risk scores for a control."""
        key = f"{self.PREFIX_RISK}:{control_id}"
        return self.set(key, scores, ttl)
    
    def get_risk_scores(self, control_id: str) -> Optional[Dict[str, Any]]:
        """Get cached risk scores for a control."""
        key = f"{self.PREFIX_RISK}:{control_id}"
        return self.get(key)
    
    def invalidate_risk_scores(self, control_id: Optional[str] = None) -> int:
        """Invalidate risk scores cache."""
        if control_id:
            pattern = f"{self.PREFIX_RISK}:{control_id}"
            return 1 if self.delete(pattern) else 0
        else:
            pattern = f"{self.PREFIX_RISK}:*"
            return self.invalidate_pattern(pattern)
    
    def cache_compliance_summary(self, summary: Dict[str, Any], 
                                ttl: int = TTL_MEDIUM) -> bool:
        """Cache compliance summary."""
        key = f"{self.PREFIX_COMPLIANCE}:summary"
        return self.set(key, summary, ttl)
    
    def get_compliance_summary(self) -> Optional[Dict[str, Any]]:
        """Get cached compliance summary."""
        key = f"{self.PREFIX_COMPLIANCE}:summary"
        return self.get(key)
    
    def cache_trend_data(self, trend_type: str, data: Any, 
                        ttl: int = TTL_LONG) -> bool:
        """Cache trend analysis data."""
        key = f"{self.PREFIX_TREND}:{trend_type}"
        return self.set(key, data, ttl)
    
    def get_trend_data(self, trend_type: str) -> Optional[Any]:
        """Get cached trend data."""
        key = f"{self.PREFIX_TREND}:{trend_type}"
        return self.get(key)
    
    def cache_control_info(self, control_id: str, info: Dict[str, Any],
                          ttl: int = TTL_WEEK) -> bool:
        """Cache control information (changes rarely)."""
        key = f"{self.PREFIX_CONTROL}:{control_id}"
        return self.set(key, info, ttl)
    
    def get_control_info(self, control_id: str) -> Optional[Dict[str, Any]]:
        """Get cached control information."""
        key = f"{self.PREFIX_CONTROL}:{control_id}"
        return self.get(key)
