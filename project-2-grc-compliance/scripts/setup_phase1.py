#!/usr/bin/env python3
"""
Setup script for Phase 1: Performance Optimization

This script:
1. Checks Redis installation and connectivity
2. Verifies database optimizations
3. Tests cache functionality
4. Initializes connection pool
5. Runs basic performance tests
"""

import sys
import subprocess
from pathlib import Path
import logging

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def check_redis_installation():
    """Check if Redis is installed and running."""
    logger.info("Checking Redis installation...")
    
    try:
        import redis
        logger.info("✓ Redis Python package installed")
    except ImportError:
        logger.error("✗ Redis Python package not found")
        logger.info("  Install with: pip install redis")
        return False
    
    # Try to connect to Redis
    try:
        r = redis.Redis(host='localhost', port=6379, socket_connect_timeout=5)
        r.ping()
        logger.info("✓ Redis server is running")
        
        # Get Redis info
        info = r.info()
        logger.info(f"  Redis version: {info.get('redis_version', 'unknown')}")
        logger.info(f"  Memory used: {info.get('used_memory_human', 'unknown')}")
        
        return True
        
    except redis.ConnectionError:
        logger.error("✗ Cannot connect to Redis server")
        logger.info("  Redis server may not be running")
        logger.info("  Start Redis with:")
        logger.info("    - Windows: redis-server.exe")
        logger.info("    - Linux/Mac: redis-server")
        return False
    except Exception as e:
        logger.error(f"✗ Error connecting to Redis: {e}")
        return False


def check_database_optimizations():
    """Check database optimizations are applied."""
    logger.info("\nChecking database optimizations...")
    
    db_path = Path(__file__).parent.parent / 'data' / 'processed' / 'grc_analytics.db'
    
    if not db_path.exists():
        logger.error(f"✗ Database not found: {db_path}")
        return False
    
    logger.info(f"✓ Database found: {db_path}")
    
    import sqlite3
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Check journal mode
        cursor.execute("PRAGMA journal_mode")
        journal_mode = cursor.fetchone()[0]
        logger.info(f"  Journal mode: {journal_mode}")
        
        if journal_mode != 'wal':
            logger.warning("  ⚠ WAL mode not enabled (recommended for better concurrency)")
            logger.info("    Enable with: PRAGMA journal_mode=WAL")
        else:
            logger.info("  ✓ WAL mode enabled")
        
        # Check synchronous setting
        cursor.execute("PRAGMA synchronous")
        sync = cursor.fetchone()[0]
        logger.info(f"  Synchronous: {sync}")
        
        # Check indexes
        cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='index' AND sql IS NOT NULL")
        index_count = cursor.fetchone()[0]
        logger.info(f"  ✓ {index_count} custom indexes found")
        
        # Check database size
        cursor.execute("SELECT page_count * page_size as size FROM pragma_page_count(), pragma_page_size()")
        db_size = cursor.fetchone()[0]
        logger.info(f"  Database size: {db_size / 1024 / 1024:.2f} MB")
        
        conn.close()
        return True
        
    except Exception as e:
        logger.error(f"✗ Error checking database: {e}")
        return False


def test_cache_functionality():
    """Test cache functionality."""
    logger.info("\nTesting cache functionality...")
    
    try:
        from src.cache.redis_manager import CacheManager
        
        cache = CacheManager()
        
        if not cache.is_available():
            logger.error("✗ Cache not available")
            return False
        
        logger.info("✓ Cache manager initialized")
        
        # Test basic operations
        test_key = "test:setup"
        test_value = {"test": "data", "timestamp": "2024-01-01"}
        
        # Set
        success = cache.set(test_key, test_value, ttl=60)
        if not success:
            logger.error("✗ Cache set failed")
            return False
        logger.info("✓ Cache set operation successful")
        
        # Get
        retrieved = cache.get(test_key)
        if retrieved != test_value:
            logger.error("✗ Cache get failed - data mismatch")
            return False
        logger.info("✓ Cache get operation successful")
        
        # Delete
        deleted = cache.delete(test_key)
        if not deleted:
            logger.error("✗ Cache delete failed")
            return False
        logger.info("✓ Cache delete operation successful")
        
        # Get cache stats
        stats = cache.get_stats()
        logger.info(f"✓ Cache stats retrieved: {stats.get('total_keys', 0)} keys")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Error testing cache: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_connection_pool():
    """Test connection pool functionality."""
    logger.info("\nTesting connection pool...")
    
    db_path = Path(__file__).parent.parent / 'data' / 'processed' / 'grc_analytics.db'
    
    try:
        from src.database.pool import SQLiteConnectionPool
        
        pool = SQLiteConnectionPool(str(db_path), pool_size=3)
        logger.info("✓ Connection pool initialized")
        
        # Test getting connection
        conn = pool.get_connection()
        logger.info("✓ Got connection from pool")
        
        # Test query
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM nist_controls")
        count = cursor.fetchone()[0]
        logger.info(f"✓ Query executed: {count} controls found")
        
        # Return connection
        pool.return_connection(conn)
        logger.info("✓ Connection returned to pool")
        
        # Check pool stats
        stats = pool.get_stats()
        logger.info(f"  Pool size: {stats['pool_size']}")
        logger.info(f"  Available connections: {stats['available_connections']}")
        logger.info(f"  Total requests: {stats['total_requests']}")
        
        # Test context manager
        with pool.get_cursor() as cursor:
            cursor.execute("SELECT control_id FROM nist_controls LIMIT 1")
            result = cursor.fetchone()
            logger.info(f"✓ Context manager works: {result[0]}")
        
        # Health check
        if pool.health_check():
            logger.info("✓ Pool health check passed")
        else:
            logger.error("✗ Pool health check failed")
            return False
        
        # Cleanup
        pool.close_all()
        logger.info("✓ Pool closed successfully")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Error testing connection pool: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_performance_monitoring():
    """Test performance monitoring."""
    logger.info("\nTesting performance monitoring...")
    
    try:
        from src.utils.performance_monitor import (
            monitor_performance, 
            PerformanceTimer,
            get_metrics
        )
        import time
        
        # Test decorator
        @monitor_performance(threshold_ms=50)
        def test_function():
            time.sleep(0.01)  # 10ms
            return "test"
        
        result = test_function()
        logger.info("✓ Performance decorator works")
        
        # Test timer
        with PerformanceTimer("test_operation", threshold_ms=100):
            time.sleep(0.02)  # 20ms
        logger.info("✓ Performance timer works")
        
        # Get metrics
        metrics = get_metrics()
        summary = metrics.get_summary()
        
        if 'test_function' in summary:
            logger.info(f"✓ Metrics collected: {summary['test_function']}")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Error testing performance monitoring: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_quick_benchmark():
    """Run a quick performance benchmark."""
    logger.info("\nRunning quick performance benchmark...")
    
    db_path = Path(__file__).parent.parent / 'data' / 'processed' / 'grc_analytics.db'
    
    try:
        from src.analytics.risk_scoring_cached import RiskScoringEngine
        from src.cache.redis_manager import CacheManager
        from src.database.pool import initialize_pool, close_pool
        import time
        
        # Initialize
        cache = CacheManager()
        cache.clear_all()  # Start fresh
        pool = initialize_pool(str(db_path), pool_size=3)
        
        engine = RiskScoringEngine(
            db_path=str(db_path),
            cache_manager=cache,
            connection_pool=pool
        )
        
        # Get sample controls
        with engine._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT control_id FROM nist_controls LIMIT 10")
            control_ids = [row['control_id'] for row in cursor.fetchall()]
        
        # Benchmark cold cache
        cold_times = []
        logger.info("  Testing cold cache...")
        for control_id in control_ids:
            start = time.time()
            engine.calculate_control_risk_score(control_id, use_cache=True)
            elapsed_ms = (time.time() - start) * 1000
            cold_times.append(elapsed_ms)
        
        cold_avg = sum(cold_times) / len(cold_times)
        logger.info(f"  Cold cache average: {cold_avg:.2f}ms")
        
        # Benchmark warm cache
        warm_times = []
        logger.info("  Testing warm cache...")
        for control_id in control_ids:
            start = time.time()
            engine.calculate_control_risk_score(control_id, use_cache=True)
            elapsed_ms = (time.time() - start) * 1000
            warm_times.append(elapsed_ms)
        
        warm_avg = sum(warm_times) / len(warm_times)
        logger.info(f"  Warm cache average: {warm_avg:.2f}ms")
        
        improvement = ((cold_avg - warm_avg) / cold_avg * 100)
        logger.info(f"  ✓ Cache improvement: {improvement:.1f}%")
        
        # Cache stats
        stats = cache.get_stats()
        logger.info(f"  Cache keys: {stats.get('total_keys', 0)}")
        
        close_pool()
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Error running benchmark: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all setup checks."""
    logger.info("=" * 70)
    logger.info("PHASE 1 SETUP: Performance Optimization")
    logger.info("=" * 70)
    
    results = {
        'redis': check_redis_installation(),
        'database': check_database_optimizations(),
        'cache': False,
        'pool': False,
        'monitoring': False,
        'benchmark': False
    }
    
    # Only proceed with advanced tests if Redis is available
    if results['redis']:
        results['cache'] = test_cache_functionality()
        results['pool'] = test_connection_pool()
        results['monitoring'] = test_performance_monitoring()
        
        # Only run benchmark if everything else passed
        if all([results['cache'], results['pool'], results['monitoring']]):
            results['benchmark'] = run_quick_benchmark()
    
    # Summary
    logger.info("\n" + "=" * 70)
    logger.info("SETUP SUMMARY")
    logger.info("=" * 70)
    
    for component, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        logger.info(f"{component.upper()}: {status}")
    
    all_passed = all(results.values())
    
    if all_passed:
        logger.info("\n✅ Phase 1 setup completed successfully!")
        logger.info("You can now run the full benchmark with:")
        logger.info("  python scripts/performance_benchmark.py")
    else:
        logger.info("\n⚠ Some components failed. Please fix the issues above.")
        if not results['redis']:
            logger.info("\n📝 To install Redis:")
            logger.info("  - Windows: https://github.com/microsoftarchive/redis/releases")
            logger.info("  - Linux: sudo apt-get install redis-server")
            logger.info("  - macOS: brew install redis")
    
    return 0 if all_passed else 1


if __name__ == '__main__':
    sys.exit(main())
