"""
Performance monitoring utilities for GRC Analytics Platform.

Provides decorators and tools for monitoring:
- Function execution time
- Slow query detection
- Memory usage
- Performance metrics collection
"""

import time
import logging
import functools
from typing import Callable, Any, Optional
import tracemalloc
from collections import defaultdict
from datetime import datetime

logger = logging.getLogger(__name__)


class PerformanceMetrics:
    """Collects and stores performance metrics."""
    
    def __init__(self):
        self.metrics = defaultdict(list)
        self.slow_queries = []
        self.total_calls = defaultdict(int)
        self.total_time = defaultdict(float)
        
    def record_execution(self, func_name: str, elapsed_ms: float, 
                        is_slow: bool = False):
        """Record function execution time."""
        self.metrics[func_name].append({
            'timestamp': datetime.now(),
            'elapsed_ms': elapsed_ms,
            'is_slow': is_slow
        })
        self.total_calls[func_name] += 1
        self.total_time[func_name] += elapsed_ms
        
        if is_slow:
            self.slow_queries.append({
                'function': func_name,
                'timestamp': datetime.now(),
                'elapsed_ms': elapsed_ms
            })
    
    def get_summary(self, func_name: Optional[str] = None) -> dict:
        """Get performance summary."""
        if func_name:
            if func_name not in self.metrics:
                return {}
            
            times = [m['elapsed_ms'] for m in self.metrics[func_name]]
            return {
                'function': func_name,
                'total_calls': self.total_calls[func_name],
                'total_time_ms': round(self.total_time[func_name], 2),
                'avg_time_ms': round(sum(times) / len(times), 2) if times else 0,
                'min_time_ms': round(min(times), 2) if times else 0,
                'max_time_ms': round(max(times), 2) if times else 0,
                'slow_calls': sum(1 for m in self.metrics[func_name] if m['is_slow'])
            }
        else:
            # Summary for all functions
            return {
                func: self.get_summary(func) 
                for func in self.metrics.keys()
            }
    
    def get_slow_queries(self, limit: int = 10) -> list:
        """Get recent slow queries."""
        return sorted(
            self.slow_queries,
            key=lambda x: x['elapsed_ms'],
            reverse=True
        )[:limit]
    
    def clear(self):
        """Clear all metrics."""
        self.metrics.clear()
        self.slow_queries.clear()
        self.total_calls.clear()
        self.total_time.clear()


# Global metrics instance
_metrics = PerformanceMetrics()


def get_metrics() -> PerformanceMetrics:
    """Get global metrics instance."""
    return _metrics


def monitor_performance(threshold_ms: float = 100, log_level: str = 'WARNING'):
    """
    Decorator to monitor function performance.
    
    Args:
        threshold_ms: Threshold for slow query warning (default: 100ms)
        log_level: Logging level for slow queries
        
    Usage:
        @monitor_performance(threshold_ms=50)
        def my_slow_function():
            time.sleep(0.1)
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                return result
                
            finally:
                elapsed_ms = (time.time() - start_time) * 1000
                is_slow = elapsed_ms > threshold_ms
                
                # Record metrics
                _metrics.record_execution(func.__name__, elapsed_ms, is_slow)
                
                # Log if slow
                if is_slow:
                    log_func = getattr(logger, log_level.lower(), logger.warning)
                    log_func(
                        f"Slow function: {func.__name__} "
                        f"took {elapsed_ms:.2f}ms (threshold: {threshold_ms}ms)"
                    )
                else:
                    logger.debug(f"{func.__name__} executed in {elapsed_ms:.2f}ms")
        
        return wrapper
    return decorator


def monitor_query(threshold_ms: float = 100):
    """
    Decorator specifically for database queries.
    
    Similar to monitor_performance but with query-specific logging.
    
    Usage:
        @monitor_query(threshold_ms=50)
        def fetch_controls(self):
            cursor.execute("SELECT * FROM nist_controls")
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            start_time = time.time()
            query_name = func.__name__
            
            try:
                result = func(*args, **kwargs)
                return result
                
            finally:
                elapsed_ms = (time.time() - start_time) * 1000
                is_slow = elapsed_ms > threshold_ms
                
                # Record metrics
                _metrics.record_execution(f"query:{query_name}", elapsed_ms, is_slow)
                
                if is_slow:
                    logger.warning(
                        f"Slow query detected: {query_name} "
                        f"took {elapsed_ms:.2f}ms "
                        f"(threshold: {threshold_ms}ms)"
                    )
                else:
                    logger.debug(f"Query {query_name}: {elapsed_ms:.2f}ms")
        
        return wrapper
    return decorator


def measure_memory(func: Callable) -> Callable:
    """
    Decorator to measure memory usage.
    
    Tracks memory allocation during function execution.
    Note: Has performance overhead, use for profiling only.
    
    Usage:
        @measure_memory
        def memory_intensive_function():
            large_list = [i for i in range(1000000)]
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        tracemalloc.start()
        
        try:
            result = func(*args, **kwargs)
            
            current, peak = tracemalloc.get_traced_memory()
            tracemalloc.stop()
            
            logger.info(
                f"Memory usage for {func.__name__}: "
                f"current={current / 1024 / 1024:.2f}MB, "
                f"peak={peak / 1024 / 1024:.2f}MB"
            )
            
            return result
            
        except Exception:
            tracemalloc.stop()
            raise
    
    return wrapper


class PerformanceTimer:
    """
    Context manager for timing code blocks.
    
    Usage:
        with PerformanceTimer("my_operation") as timer:
            # do some work
            time.sleep(0.1)
        print(f"Took {timer.elapsed_ms}ms")
    """
    
    def __init__(self, name: str, threshold_ms: float = 100):
        self.name = name
        self.threshold_ms = threshold_ms
        self.start_time = None
        self.elapsed_ms = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.elapsed_ms = (time.time() - self.start_time) * 1000
        
        if self.elapsed_ms > self.threshold_ms:
            logger.warning(
                f"Slow operation: {self.name} "
                f"took {self.elapsed_ms:.2f}ms "
                f"(threshold: {self.threshold_ms}ms)"
            )
        else:
            logger.debug(f"{self.name}: {self.elapsed_ms:.2f}ms")
        
        # Record in metrics
        _metrics.record_execution(
            self.name, 
            self.elapsed_ms, 
            self.elapsed_ms > self.threshold_ms
        )


def benchmark(iterations: int = 100):
    """
    Decorator to benchmark function performance over multiple iterations.
    
    Args:
        iterations: Number of times to run the function
        
    Usage:
        @benchmark(iterations=1000)
        def function_to_benchmark():
            # code here
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            times = []
            result = None
            
            logger.info(f"Benchmarking {func.__name__} ({iterations} iterations)")
            
            for i in range(iterations):
                start = time.time()
                result = func(*args, **kwargs)
                elapsed = (time.time() - start) * 1000
                times.append(elapsed)
            
            avg_time = sum(times) / len(times)
            min_time = min(times)
            max_time = max(times)
            
            logger.info(
                f"Benchmark results for {func.__name__}:\n"
                f"  Iterations: {iterations}\n"
                f"  Average: {avg_time:.3f}ms\n"
                f"  Min: {min_time:.3f}ms\n"
                f"  Max: {max_time:.3f}ms\n"
                f"  Median: {sorted(times)[len(times)//2]:.3f}ms"
            )
            
            return result
        
        return wrapper
    return decorator


def profile_function(func: Callable) -> Callable:
    """
    Comprehensive profiling decorator.
    
    Combines timing and memory profiling.
    Use for detailed analysis of performance bottlenecks.
    
    Usage:
        @profile_function
        def complex_operation():
            # code here
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        # Start profiling
        tracemalloc.start()
        start_time = time.time()
        
        try:
            result = func(*args, **kwargs)
            
            # Get metrics
            elapsed_ms = (time.time() - start_time) * 1000
            current_mem, peak_mem = tracemalloc.get_traced_memory()
            tracemalloc.stop()
            
            logger.info(
                f"Profile for {func.__name__}:\n"
                f"  Execution time: {elapsed_ms:.2f}ms\n"
                f"  Current memory: {current_mem / 1024 / 1024:.2f}MB\n"
                f"  Peak memory: {peak_mem / 1024 / 1024:.2f}MB"
            )
            
            return result
            
        except Exception:
            tracemalloc.stop()
            raise
    
    return wrapper


class QueryProfiler:
    """
    Profile database queries with detailed statistics.
    
    Usage:
        profiler = QueryProfiler()
        
        with profiler.profile_query("fetch_controls"):
            cursor.execute("SELECT * FROM nist_controls")
            results = cursor.fetchall()
        
        print(profiler.get_summary())
    """
    
    def __init__(self):
        self.queries = []
    
    def profile_query(self, query_name: str):
        """Context manager for profiling a query."""
        return _QueryContext(self, query_name)
    
    def add_query(self, query_name: str, elapsed_ms: float, row_count: int = None):
        """Add query execution data."""
        self.queries.append({
            'name': query_name,
            'timestamp': datetime.now(),
            'elapsed_ms': elapsed_ms,
            'row_count': row_count
        })
    
    def get_summary(self) -> dict:
        """Get query profiling summary."""
        if not self.queries:
            return {}
        
        by_name = defaultdict(list)
        for q in self.queries:
            by_name[q['name']].append(q['elapsed_ms'])
        
        summary = {}
        for name, times in by_name.items():
            summary[name] = {
                'count': len(times),
                'total_ms': round(sum(times), 2),
                'avg_ms': round(sum(times) / len(times), 2),
                'min_ms': round(min(times), 2),
                'max_ms': round(max(times), 2)
            }
        
        return summary
    
    def get_slowest(self, limit: int = 10) -> list:
        """Get slowest queries."""
        return sorted(
            self.queries,
            key=lambda x: x['elapsed_ms'],
            reverse=True
        )[:limit]
    
    def clear(self):
        """Clear query history."""
        self.queries.clear()


class _QueryContext:
    """Internal context manager for QueryProfiler."""
    
    def __init__(self, profiler: QueryProfiler, query_name: str):
        self.profiler = profiler
        self.query_name = query_name
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        elapsed_ms = (time.time() - self.start_time) * 1000
        self.profiler.add_query(self.query_name, elapsed_ms)
