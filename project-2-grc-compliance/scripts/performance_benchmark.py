#!/usr/bin/env python3
"""
Performance Benchmark Suite for GRC Analytics Platform

Compares performance between:
- Original implementation vs. cached implementation
- With/without connection pooling
- Different cache configurations
"""

import sys
import time
from pathlib import Path
import logging

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.analytics.risk_scoring import RiskScoringEngine as OriginalEngine
from src.analytics.risk_scoring_cached import RiskScoringEngine as CachedEngine
from src.cache.redis_manager import CacheManager
from src.database.pool import initialize_pool, close_pool
from src.utils.performance_monitor import get_metrics, PerformanceTimer

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def benchmark_original_engine(db_path: str, num_controls: int = 50):
    """Benchmark original risk scoring engine."""
    logger.info("=" * 70)
    logger.info("BENCHMARKING ORIGINAL ENGINE (No Cache, No Pool)")
    logger.info("=" * 70)
    
    with OriginalEngine(db_path) as engine:
        # Get sample control IDs
        cursor = engine.conn.cursor()
        cursor.execute(f"SELECT control_id FROM nist_controls LIMIT {num_controls}")
        control_ids = [row[0] for row in cursor.fetchall()]
        
        # Benchmark individual score calculations
        times = []
        with PerformanceTimer("original_engine_individual_scores"):
            for control_id in control_ids:
                start = time.time()
                engine.calculate_control_risk_score(control_id)
                elapsed_ms = (time.time() - start) * 1000
                times.append(elapsed_ms)
        
        # Calculate statistics
        avg_time = sum(times) / len(times)
        min_time = min(times)
        max_time = max(times)
        
        logger.info(f"Individual Score Calculations ({len(control_ids)} controls):")
        logger.info(f"  Average: {avg_time:.2f}ms")
        logger.info(f"  Min: {min_time:.2f}ms")
        logger.info(f"  Max: {max_time:.2f}ms")
        logger.info(f"  Total: {sum(times):.2f}ms")
        
        # Benchmark high-risk controls query
        with PerformanceTimer("original_engine_high_risk"):
            high_risk = engine.get_high_risk_controls(threshold=50.0, limit=20)
        
        logger.info(f"High-Risk Controls Query: Found {len(high_risk)} controls")
        
        # Benchmark summary
        with PerformanceTimer("original_engine_summary"):
            summary = engine.get_risk_score_summary()
        
        logger.info(f"Risk Score Summary: {summary['total_controls']} total controls")
        
        return {
            'engine': 'original',
            'num_controls': len(control_ids),
            'avg_individual_ms': avg_time,
            'min_individual_ms': min_time,
            'max_individual_ms': max_time,
            'total_individual_ms': sum(times),
            'high_risk_count': len(high_risk),
            'summary': summary
        }


def benchmark_cached_engine_cold(db_path: str, num_controls: int = 50):
    """Benchmark cached engine with cold cache."""
    logger.info("=" * 70)
    logger.info("BENCHMARKING CACHED ENGINE (Cold Cache)")
    logger.info("=" * 70)
    
    # Initialize cache and clear it
    cache = CacheManager()
    cache.clear_all()
    
    # Initialize connection pool
    pool = initialize_pool(db_path, pool_size=5)
    
    try:
        engine = CachedEngine(
            db_path=db_path,
            cache_manager=cache,
            connection_pool=pool
        )
        
        with engine._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"SELECT control_id FROM nist_controls LIMIT {num_controls}")
            control_ids = [row['control_id'] for row in cursor.fetchall()]
        
        # Benchmark individual score calculations (cold cache)
        times = []
        with PerformanceTimer("cached_engine_cold_individual_scores"):
            for control_id in control_ids:
                start = time.time()
                engine.calculate_control_risk_score(control_id, use_cache=True)
                elapsed_ms = (time.time() - start) * 1000
                times.append(elapsed_ms)
        
        avg_time = sum(times) / len(times)
        min_time = min(times)
        max_time = max(times)
        
        logger.info(f"Individual Score Calculations - Cold Cache ({len(control_ids)} controls):")
        logger.info(f"  Average: {avg_time:.2f}ms")
        logger.info(f"  Min: {min_time:.2f}ms")
        logger.info(f"  Max: {max_time:.2f}ms")
        logger.info(f"  Total: {sum(times):.2f}ms")
        
        # Check cache stats
        cache_stats = cache.get_stats()
        logger.info(f"Cache Stats: {cache_stats}")
        
        return {
            'engine': 'cached_cold',
            'num_controls': len(control_ids),
            'avg_individual_ms': avg_time,
            'min_individual_ms': min_time,
            'max_individual_ms': max_time,
            'total_individual_ms': sum(times),
            'cache_stats': cache_stats
        }
        
    finally:
        close_pool()


def benchmark_cached_engine_warm(db_path: str, num_controls: int = 50):
    """Benchmark cached engine with warm cache."""
    logger.info("=" * 70)
    logger.info("BENCHMARKING CACHED ENGINE (Warm Cache)")
    logger.info("=" * 70)
    
    # Initialize cache (should have data from previous benchmark)
    cache = CacheManager()
    
    # Initialize connection pool
    pool = initialize_pool(db_path, pool_size=5)
    
    try:
        engine = CachedEngine(
            db_path=db_path,
            cache_manager=cache,
            connection_pool=pool
        )
        
        with engine._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"SELECT control_id FROM nist_controls LIMIT {num_controls}")
            control_ids = [row['control_id'] for row in cursor.fetchall()]
        
        # Benchmark individual score calculations (warm cache)
        times = []
        cache_hits = 0
        with PerformanceTimer("cached_engine_warm_individual_scores"):
            for control_id in control_ids:
                start = time.time()
                result = engine.calculate_control_risk_score(control_id, use_cache=True)
                elapsed_ms = (time.time() - start) * 1000
                times.append(elapsed_ms)
                if 'cached_at' in result:
                    cache_hits += 1
        
        avg_time = sum(times) / len(times)
        min_time = min(times)
        max_time = max(times)
        cache_hit_rate = (cache_hits / len(control_ids)) * 100
        
        logger.info(f"Individual Score Calculations - Warm Cache ({len(control_ids)} controls):")
        logger.info(f"  Average: {avg_time:.2f}ms")
        logger.info(f"  Min: {min_time:.2f}ms")
        logger.info(f"  Max: {max_time:.2f}ms")
        logger.info(f"  Total: {sum(times):.2f}ms")
        logger.info(f"  Cache Hit Rate: {cache_hit_rate:.1f}%")
        
        # Benchmark high-risk controls query (should use cache)
        with PerformanceTimer("cached_engine_warm_high_risk"):
            high_risk = engine.get_high_risk_controls(threshold=50.0, limit=20, use_cache=True)
        
        logger.info(f"High-Risk Controls Query (cached): Found {len(high_risk)} controls")
        
        # Benchmark summary (should use cache)
        with PerformanceTimer("cached_engine_warm_summary"):
            summary = engine.get_risk_score_summary(use_cache=True)
        
        logger.info(f"Risk Score Summary (cached): {summary['total_controls']} total controls")
        
        # Check cache stats
        cache_stats = cache.get_stats()
        logger.info(f"Cache Stats: {cache_stats}")
        
        # Check pool stats
        pool_stats = pool.get_stats()
        logger.info(f"Connection Pool Stats: {pool_stats}")
        
        return {
            'engine': 'cached_warm',
            'num_controls': len(control_ids),
            'avg_individual_ms': avg_time,
            'min_individual_ms': min_time,
            'max_individual_ms': max_time,
            'total_individual_ms': sum(times),
            'cache_hit_rate': cache_hit_rate,
            'high_risk_count': len(high_risk),
            'summary': summary,
            'cache_stats': cache_stats,
            'pool_stats': pool_stats
        }
        
    finally:
        close_pool()


def benchmark_concurrent_access(db_path: str, num_threads: int = 5, 
                                requests_per_thread: int = 10):
    """Benchmark concurrent access with connection pooling."""
    logger.info("=" * 70)
    logger.info(f"BENCHMARKING CONCURRENT ACCESS ({num_threads} threads)")
    logger.info("=" * 70)
    
    import threading
    import queue
    
    cache = CacheManager()
    pool = initialize_pool(db_path, pool_size=num_threads)
    
    results_queue = queue.Queue()
    errors_queue = queue.Queue()
    
    def worker(thread_id: int):
        """Worker thread function."""
        try:
            engine = CachedEngine(
                db_path=db_path,
                cache_manager=cache,
                connection_pool=pool
            )
            
            # Get control IDs
            with engine._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(f"SELECT control_id FROM nist_controls LIMIT {requests_per_thread}")
                control_ids = [row['control_id'] for row in cursor.fetchall()]
            
            thread_times = []
            for control_id in control_ids:
                start = time.time()
                engine.calculate_control_risk_score(control_id, use_cache=True)
                elapsed_ms = (time.time() - start) * 1000
                thread_times.append(elapsed_ms)
            
            results_queue.put({
                'thread_id': thread_id,
                'times': thread_times,
                'avg_ms': sum(thread_times) / len(thread_times)
            })
            
        except Exception as e:
            errors_queue.put({
                'thread_id': thread_id,
                'error': str(e)
            })
    
    # Create and start threads
    threads = []
    start_time = time.time()
    
    for i in range(num_threads):
        t = threading.Thread(target=worker, args=(i,))
        t.start()
        threads.append(t)
    
    # Wait for all threads to complete
    for t in threads:
        t.join()
    
    total_time = time.time() - start_time
    
    # Collect results
    all_results = []
    while not results_queue.empty():
        all_results.append(results_queue.get())
    
    all_errors = []
    while not errors_queue.empty():
        all_errors.append(errors_queue.get())
    
    if all_errors:
        logger.error(f"Errors occurred: {all_errors}")
    
    # Calculate statistics
    all_times = []
    for result in all_results:
        all_times.extend(result['times'])
    
    total_requests = len(all_times)
    avg_time = sum(all_times) / len(all_times) if all_times else 0
    throughput = total_requests / total_time if total_time > 0 else 0
    
    logger.info(f"Concurrent Access Results:")
    logger.info(f"  Total Threads: {num_threads}")
    logger.info(f"  Requests per Thread: {requests_per_thread}")
    logger.info(f"  Total Requests: {total_requests}")
    logger.info(f"  Total Time: {total_time:.2f}s")
    logger.info(f"  Average Request Time: {avg_time:.2f}ms")
    logger.info(f"  Throughput: {throughput:.2f} requests/sec")
    logger.info(f"  Errors: {len(all_errors)}")
    
    # Pool stats
    pool_stats = pool.get_stats()
    logger.info(f"Connection Pool Stats: {pool_stats}")
    
    close_pool()
    
    return {
        'num_threads': num_threads,
        'requests_per_thread': requests_per_thread,
        'total_requests': total_requests,
        'total_time_sec': total_time,
        'avg_request_ms': avg_time,
        'throughput_rps': throughput,
        'errors': len(all_errors),
        'pool_stats': pool_stats
    }


def print_comparison_summary(original_results: dict, cached_cold: dict, 
                            cached_warm: dict, concurrent: dict):
    """Print comprehensive comparison summary."""
    logger.info("\n" + "=" * 70)
    logger.info("PERFORMANCE COMPARISON SUMMARY")
    logger.info("=" * 70)
    
    logger.info("\n--- Individual Score Calculation Times ---")
    logger.info(f"Original (no cache):     {original_results['avg_individual_ms']:.2f}ms avg")
    logger.info(f"Cached (cold cache):     {cached_cold['avg_individual_ms']:.2f}ms avg")
    logger.info(f"Cached (warm cache):     {cached_warm['avg_individual_ms']:.2f}ms avg")
    
    # Calculate improvements
    cold_improvement = ((original_results['avg_individual_ms'] - 
                        cached_cold['avg_individual_ms']) / 
                       original_results['avg_individual_ms'] * 100)
    warm_improvement = ((original_results['avg_individual_ms'] - 
                        cached_warm['avg_individual_ms']) / 
                       original_results['avg_individual_ms'] * 100)
    
    logger.info(f"\nImprovements:")
    logger.info(f"  Cold cache vs Original: {cold_improvement:+.1f}%")
    logger.info(f"  Warm cache vs Original: {warm_improvement:+.1f}%")
    logger.info(f"  Warm cache vs Cold:     "
               f"{((cached_cold['avg_individual_ms'] - cached_warm['avg_individual_ms']) / cached_cold['avg_individual_ms'] * 100):+.1f}%")
    
    logger.info("\n--- Cache Statistics ---")
    if 'cache_stats' in cached_warm:
        stats = cached_warm['cache_stats']
        logger.info(f"  Total Keys: {stats.get('total_keys', 'N/A')}")
        logger.info(f"  Memory Used: {stats.get('memory_used_mb', 'N/A')} MB")
        logger.info(f"  Hit Rate: {cached_warm.get('cache_hit_rate', 'N/A'):.1f}%")
    
    logger.info("\n--- Connection Pool Statistics ---")
    if 'pool_stats' in cached_warm:
        stats = cached_warm['pool_stats']
        logger.info(f"  Pool Size: {stats.get('pool_size', 'N/A')}")
        logger.info(f"  Total Requests: {stats.get('total_requests', 'N/A')}")
        logger.info(f"  Wait Percentage: {stats.get('wait_percentage', 'N/A')}%")
        logger.info(f"  Avg Wait Time: {stats.get('avg_wait_time_ms', 'N/A')}ms")
    
    logger.info("\n--- Concurrent Access Performance ---")
    logger.info(f"  Throughput: {concurrent['throughput_rps']:.2f} requests/sec")
    logger.info(f"  Avg Request Time: {concurrent['avg_request_ms']:.2f}ms")
    logger.info(f"  Total Time ({concurrent['total_requests']} requests): "
               f"{concurrent['total_time_sec']:.2f}s")
    
    logger.info("\n" + "=" * 70)


def main():
    """Run comprehensive benchmark suite."""
    # Database path
    db_path = Path(__file__).parent.parent / 'data' / 'processed' / 'grc_analytics.db'
    
    if not db_path.exists():
        logger.error(f"Database not found: {db_path}")
        return
    
    logger.info(f"Using database: {db_path}")
    logger.info(f"Starting comprehensive benchmark suite...\n")
    
    # Run benchmarks
    num_controls = 50
    
    # 1. Original engine
    original_results = benchmark_original_engine(str(db_path), num_controls)
    
    # 2. Cached engine (cold cache)
    cached_cold_results = benchmark_cached_engine_cold(str(db_path), num_controls)
    
    # 3. Cached engine (warm cache)
    cached_warm_results = benchmark_cached_engine_warm(str(db_path), num_controls)
    
    # 4. Concurrent access
    concurrent_results = benchmark_concurrent_access(str(db_path), 
                                                     num_threads=5, 
                                                     requests_per_thread=10)
    
    # Print comparison summary
    print_comparison_summary(original_results, cached_cold_results, 
                           cached_warm_results, concurrent_results)
    
    # Print performance monitor metrics
    logger.info("\n--- Performance Monitor Metrics ---")
    metrics = get_metrics()
    summary = metrics.get_summary()
    for func_name, stats in summary.items():
        if stats.get('total_calls', 0) > 0:
            logger.info(f"{func_name}:")
            logger.info(f"  Calls: {stats['total_calls']}")
            logger.info(f"  Avg: {stats['avg_time_ms']:.2f}ms")
            logger.info(f"  Total: {stats['total_time_ms']:.2f}ms")
    
    logger.info("\n✅ Benchmark suite completed!")


if __name__ == '__main__':
    main()
