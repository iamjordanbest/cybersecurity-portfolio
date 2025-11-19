"""
Unit tests for Redis CacheManager.

Tests caching functionality with graceful degradation when Redis unavailable.
"""

import pytest
import redis
from unittest.mock import Mock, patch
from src.cache.redis_manager import CacheManager


@pytest.mark.unit
class TestCacheManager:
    """Test suite for CacheManager class."""
    
    def test_cache_initialization(self):
        """Test cache manager initialization."""
        cache = CacheManager(enabled=False)
        assert cache.enabled is False
        assert cache.redis_client is None
    
    def test_cache_with_redis_unavailable(self):
        """Test cache gracefully handles Redis being unavailable."""
        with patch('src.cache.redis_manager.redis.Redis') as mock_redis:
            mock_instance = Mock()
            mock_instance.ping.side_effect = redis.ConnectionError("Connection failed")
            mock_redis.return_value = mock_instance
            
            cache = CacheManager(enabled=True)
            assert cache.enabled is False  # Should disable gracefully
    
    def test_is_available_when_disabled(self):
        """Test is_available returns False when disabled."""
        cache = CacheManager(enabled=False)
        assert cache.is_available() is False
    
    def test_get_returns_none_when_unavailable(self):
        """Test get returns None when cache unavailable."""
        cache = CacheManager(enabled=False)
        result = cache.get("test_key")
        assert result is None
    
    def test_set_returns_false_when_unavailable(self):
        """Test set returns False when cache unavailable."""
        cache = CacheManager(enabled=False)
        result = cache.set("test_key", "test_value")
        assert result is False
    
    def test_delete_returns_false_when_unavailable(self):
        """Test delete returns False when cache unavailable."""
        cache = CacheManager(enabled=False)
        result = cache.delete("test_key")
        assert result is False
    
    def test_cache_stats_when_disabled(self):
        """Test get_stats returns appropriate data when disabled."""
        cache = CacheManager(enabled=False)
        stats = cache.get_stats()
        
        assert stats['enabled'] is False
        assert stats['available'] is False
    
    def test_ttl_constants(self):
        """Test TTL constants are defined."""
        assert CacheManager.TTL_SHORT == 300
        assert CacheManager.TTL_MEDIUM == 3600
        assert CacheManager.TTL_LONG == 86400
        assert CacheManager.TTL_WEEK == 604800
    
    def test_prefix_constants(self):
        """Test cache key prefixes are defined."""
        assert CacheManager.PREFIX_RISK == "risk_scores"
        assert CacheManager.PREFIX_COMPLIANCE == "compliance"
        assert CacheManager.PREFIX_TREND == "trends"
        assert CacheManager.PREFIX_CONTROL == "controls"


@pytest.mark.unit
class TestCacheConvenienceMethods:
    """Test convenience methods for common cache patterns."""
    
    def test_cache_risk_scores(self):
        """Test caching risk scores convenience method."""
        cache = CacheManager(enabled=False)
        result = cache.cache_risk_scores('AC-1', {'score': 75})
        # Should fail gracefully when disabled
        assert result is False
    
    def test_get_risk_scores(self):
        """Test getting risk scores convenience method."""
        cache = CacheManager(enabled=False)
        result = cache.get_risk_scores('AC-1')
        # Should return None when disabled
        assert result is None
    
    def test_invalidate_risk_scores_all(self):
        """Test invalidating all risk scores."""
        cache = CacheManager(enabled=False)
        result = cache.invalidate_risk_scores()
        # Should return 0 when disabled
        assert result == 0
    
    def test_invalidate_risk_scores_specific(self):
        """Test invalidating specific control risk scores."""
        cache = CacheManager(enabled=False)
        result = cache.invalidate_risk_scores('AC-1')
        # Should return 0 when disabled
        assert result == 0


@pytest.mark.unit
class TestCacheWithMockRedis:
    """Test cache functionality with mocked Redis."""
    
    @patch('redis.Redis')
    def test_successful_redis_connection(self, mock_redis_class):
        """Test successful Redis connection."""
        mock_redis = Mock()
        mock_redis.ping.return_value = True
        mock_redis_class.return_value = mock_redis
        
        cache = CacheManager(enabled=True)
        assert cache.is_available() is True
    
    @patch('redis.Redis')
    def test_set_and_get_with_redis(self, mock_redis_class):
        """Test set and get operations with Redis."""
        import pickle
        
        mock_redis = Mock()
        mock_redis.ping.return_value = True
        test_data = {'test': 'data'}
        mock_redis.get.return_value = pickle.dumps(test_data)
        mock_redis.setex.return_value = True
        mock_redis_class.return_value = mock_redis
        
        cache = CacheManager(enabled=True)
        
        # Test set
        result = cache.set("test_key", test_data)
        assert result is True
        mock_redis.setex.assert_called_once()
        
        # Test get
        result = cache.get("test_key")
        assert result == test_data
    
    @patch('redis.Redis')
    def test_delete_with_redis(self, mock_redis_class):
        """Test delete operation with Redis."""
        mock_redis = Mock()
        mock_redis.ping.return_value = True
        mock_redis.delete.return_value = 1
        mock_redis_class.return_value = mock_redis
        
        cache = CacheManager(enabled=True)
        
        result = cache.delete("test_key")
        assert result is True
        mock_redis.delete.assert_called_once_with("test_key")
    
    @patch('redis.Redis')
    def test_exists_with_redis(self, mock_redis_class):
        """Test exists check with Redis."""
        mock_redis = Mock()
        mock_redis.ping.return_value = True
        mock_redis.exists.return_value = 1
        mock_redis_class.return_value = mock_redis
        
        cache = CacheManager(enabled=True)
        
        result = cache.exists("test_key")
        assert result is True
    
    @patch('redis.Redis')
    def test_get_ttl_with_redis(self, mock_redis_class):
        """Test TTL retrieval with Redis."""
        mock_redis = Mock()
        mock_redis.ping.return_value = True
        mock_redis.ttl.return_value = 3600
        mock_redis_class.return_value = mock_redis
        
        cache = CacheManager(enabled=True)
        
        ttl = cache.get_ttl("test_key")
        assert ttl == 3600
