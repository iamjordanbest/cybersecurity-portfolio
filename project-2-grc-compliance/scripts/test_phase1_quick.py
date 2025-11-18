#!/usr/bin/env python3
"""
Quick test script for Phase 1 Performance Optimization.

This is a simplified version that can run without Redis for demonstration.
"""

import sys
from pathlib import Path
import time
import logging

sys.path.insert(0, str(Path(__file__).parent.parent))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_without_redis():
    """Test that the system works without Redis (graceful degradation)."""
    logger.info("Testing graceful degradation without Redis...")
    
    from src.cache.redis_manager import CacheManager
    
    # Try to create cache manager (should handle Redis not available)
    cache = CacheManager(enabled=True)
    
    if not cache.is_available():
        logger.info("✓ Cache gracefully handles Redis unavailable")
        logger.info("  System will work without caching")
    else:
        logger.info("✓ Redis is available")
    
    # Test that operations don't fail
    result = cache.get("test_key")
    logger.info(f"✓ Cache get operation completed: {result}")
    
    return True


def test_connection_pool():
    """Test connection pool without Redis."""
    logger.info("\nTesting connection pool...")
    
    db_path = Path(__file__).parent.parent / 'data' / 'processed' / 'grc_analytics.db'
    
    if not db_path.exists():
        logger.warning(f"Database not found: {db_path}")
        return False
    
    from src.database.pool import SQLiteConnectionPool
    
    try:
        pool = SQLiteConnectionPool(str(db_path), pool_size=3)
        logger.info("✓ Connection pool created")
        
        # Test getting connection
        with pool.get_cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM nist_controls")
            count = cursor.fetchone()[0]
            logger.info(f"✓ Query executed: {count} controls found")
        
        # Get stats
        stats = pool.get_stats()
        logger.info(f"✓ Pool stats: {stats['available_connections']}/{stats['pool_size']} available")
        
        pool.close_all()
        logger.info("✓ Pool closed successfully")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Connection pool test failed: {e}")
        return False


def test_performance_monitoring():
    """Test performance monitoring utilities."""
    logger.info("\nTesting performance monitoring...")
    
    from src.utils.performance_monitor import (
        monitor_performance,
        PerformanceTimer,
        get_metrics
    )
    
    try:
        # Test decorator
        @monitor_performance(threshold_ms=100)
        def test_func():
            time.sleep(0.01)
            return "success"
        
        result = test_func()
        logger.info(f"✓ Performance decorator works: {result}")
        
        # Test timer
        with PerformanceTimer("test_operation", threshold_ms=100):
            time.sleep(0.01)
        logger.info("✓ Performance timer works")
        
        # Get metrics
        metrics = get_metrics()
        summary = metrics.get_summary()
        logger.info(f"✓ Metrics collected: {len(summary)} functions tracked")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Performance monitoring test failed: {e}")
        return False


def test_original_engine():
    """Test that original engine still works."""
    logger.info("\nTesting original risk scoring engine (backwards compatibility)...")
    
    db_path = Path(__file__).parent.parent / 'data' / 'processed' / 'grc_analytics.db'
    
    if not db_path.exists():
        logger.warning(f"Database not found: {db_path}")
        return False
    
    try:
        from src.analytics.risk_scoring import RiskScoringEngine
        
        with RiskScoringEngine(str(db_path)) as engine:
            # Get a sample control
            cursor = engine.conn.cursor()
            cursor.execute("SELECT control_id FROM nist_controls LIMIT 1")
            control_id = cursor.fetchone()[0]
            
            # Calculate score
            start = time.time()
            score = engine.calculate_control_risk_score(control_id)
            elapsed_ms = (time.time() - start) * 1000
            
            logger.info(f"✓ Original engine works: {control_id} score = {score['priority_score']:.2f}")
            logger.info(f"  Execution time: {elapsed_ms:.2f}ms")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Original engine test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_cached_engine_without_redis():
    """Test cached engine works even without Redis."""
    logger.info("\nTesting cached engine without Redis...")
    
    db_path = Path(__file__).parent.parent / 'data' / 'processed' / 'grc_analytics.db'
    
    if not db_path.exists():
        logger.warning(f"Database not found: {db_path}")
        return False
    
    try:
        from src.analytics.risk_scoring_cached import RiskScoringEngine
        from src.cache.redis_manager import CacheManager
        from src.database.pool import SQLiteConnectionPool
        
        # Create cache (may not be available)
        cache = CacheManager(enabled=True)
        
        # Create pool
        pool = SQLiteConnectionPool(str(db_path), pool_size=3)
        
        # Create engine
        engine = RiskScoringEngine(
            db_path=str(db_path),
            cache_manager=cache,
            connection_pool=pool
        )
        
        # Get a sample control
        with engine._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT control_id FROM nist_controls LIMIT 1")
            control_id = cursor.fetchone()[0]
        
        # Calculate score
        start = time.time()
        score = engine.calculate_control_risk_score(control_id, use_cache=True)
        elapsed_ms = (time.time() - start) * 1000
        
        logger.info(f"✓ Cached engine works: {control_id} score = {score['priority_score']:.2f}")
        logger.info(f"  Execution time: {elapsed_ms:.2f}ms")
        
        if cache.is_available():
            logger.info("  Cache is available and being used")
        else:
            logger.info("  Cache not available, using fallback (no Redis)")
        
        pool.close_all()
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Cached engine test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run quick tests."""
    logger.info("=" * 70)
    logger.info("PHASE 1: QUICK TEST SUITE")
    logger.info("=" * 70)
    logger.info("Testing core functionality (Redis optional)...\n")
    
    results = {
        'Cache Manager (no Redis)': test_without_redis(),
        'Connection Pool': test_connection_pool(),
        'Performance Monitoring': test_performance_monitoring(),
        'Original Engine': test_original_engine(),
        'Cached Engine': test_cached_engine_without_redis()
    }
    
    # Summary
    logger.info("\n" + "=" * 70)
    logger.info("TEST SUMMARY")
    logger.info("=" * 70)
    
    for test_name, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        logger.info(f"{test_name}: {status}")
    
    total = len(results)
    passed = sum(results.values())
    
    logger.info(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("\n✅ All tests passed!")
        logger.info("\nPhase 1 core functionality is working correctly.")
        logger.info("\nFor full performance testing with Redis:")
        logger.info("  1. Install and start Redis")
        logger.info("  2. Run: python scripts/setup_phase1.py")
        logger.info("  3. Run: python scripts/performance_benchmark.py")
    else:
        logger.info("\n⚠ Some tests failed. Please review the errors above.")
    
    return 0 if passed == total else 1


if __name__ == '__main__':
    sys.exit(main())
