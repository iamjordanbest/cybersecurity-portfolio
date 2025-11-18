"""
Database connection pool manager for GRC Analytics Platform.

Provides efficient database connection management with:
- Connection pooling to reduce overhead
- Automatic connection recycling
- Health checks
- Thread-safe operation
"""

import sqlite3
import logging
from contextlib import contextmanager
from threading import Lock
from typing import Optional
from queue import Queue, Empty, Full
import time

logger = logging.getLogger(__name__)


class SQLiteConnectionPool:
    """
    Thread-safe connection pool for SQLite.
    
    SQLite has limitations with concurrent writes, but this pool helps
    manage connections efficiently for read-heavy workloads.
    """
    
    def __init__(self, database_path: str, pool_size: int = 5, 
                 timeout: int = 30, check_same_thread: bool = False):
        """
        Initialize connection pool.
        
        Args:
            database_path: Path to SQLite database file
            pool_size: Maximum number of connections in pool
            timeout: Connection timeout in seconds
            check_same_thread: SQLite thread safety check (False for pooling)
        """
        self.database_path = database_path
        self.pool_size = pool_size
        self.timeout = timeout
        self.check_same_thread = check_same_thread
        
        # Connection pool implemented as a queue
        self._pool = Queue(maxsize=pool_size)
        self._lock = Lock()
        self._created_connections = 0
        
        # Statistics
        self._total_requests = 0
        self._total_waits = 0
        self._total_wait_time = 0.0
        
        # Pre-create initial connections
        self._initialize_pool()
        
        logger.info(f"Connection pool initialized: {database_path} "
                   f"(pool_size={pool_size}, timeout={timeout}s)")
    
    def _initialize_pool(self):
        """Pre-create connections to fill the pool."""
        for _ in range(self.pool_size):
            try:
                conn = self._create_connection()
                self._pool.put(conn, block=False)
            except Full:
                break
            except Exception as e:
                logger.error(f"Error initializing connection: {e}")
    
    def _create_connection(self) -> sqlite3.Connection:
        """
        Create a new database connection.
        
        Returns:
            SQLite connection object
        """
        try:
            conn = sqlite3.connect(
                self.database_path,
                timeout=self.timeout,
                check_same_thread=self.check_same_thread,
                isolation_level=None  # Autocommit mode for better concurrency
            )
            
            # Enable some optimizations
            conn.execute("PRAGMA journal_mode=WAL")  # Write-Ahead Logging
            conn.execute("PRAGMA synchronous=NORMAL")  # Faster writes
            conn.execute("PRAGMA cache_size=-64000")  # 64MB cache
            conn.execute("PRAGMA temp_store=MEMORY")  # Use memory for temp tables
            
            # Use Row factory for dict-like access
            conn.row_factory = sqlite3.Row
            
            with self._lock:
                self._created_connections += 1
            
            logger.debug(f"Created new connection (total={self._created_connections})")
            return conn
            
        except sqlite3.Error as e:
            logger.error(f"Error creating connection: {e}")
            raise
    
    def get_connection(self, timeout: Optional[float] = None) -> sqlite3.Connection:
        """
        Get a connection from the pool.
        
        Args:
            timeout: Maximum time to wait for connection (uses pool timeout if None)
            
        Returns:
            Database connection
            
        Raises:
            TimeoutError: If no connection available within timeout
        """
        timeout = timeout or self.timeout
        start_time = time.time()
        
        self._total_requests += 1
        
        try:
            # Try to get existing connection from pool
            conn = self._pool.get(timeout=timeout)
            wait_time = time.time() - start_time
            
            if wait_time > 0.1:  # Log if waited more than 100ms
                self._total_waits += 1
                self._total_wait_time += wait_time
                logger.warning(f"Connection wait: {wait_time:.3f}s")
            
            # Verify connection is still alive
            try:
                conn.execute("SELECT 1")
                return conn
            except sqlite3.Error:
                # Connection dead, create new one
                logger.warning("Dead connection detected, creating new one")
                return self._create_connection()
                
        except Empty:
            # Pool empty and waited too long
            logger.error(f"Connection pool exhausted (timeout={timeout}s)")
            raise TimeoutError("No database connection available")
    
    def return_connection(self, conn: sqlite3.Connection):
        """
        Return a connection to the pool.
        
        Args:
            conn: Connection to return
        """
        try:
            # Rollback any pending transaction
            conn.rollback()
            
            # Return to pool
            self._pool.put(conn, block=False)
            
        except Full:
            # Pool is full, close this connection
            logger.debug("Pool full, closing excess connection")
            conn.close()
            
        except Exception as e:
            logger.error(f"Error returning connection: {e}")
            try:
                conn.close()
            except Exception:
                pass
    
    @contextmanager
    def get_cursor(self):
        """
        Context manager for getting a cursor.
        
        Usage:
            with pool.get_cursor() as cursor:
                cursor.execute("SELECT * FROM table")
                results = cursor.fetchall()
        """
        conn = self.get_connection()
        cursor = None
        
        try:
            cursor = conn.cursor()
            yield cursor
            conn.commit()
            
        except Exception as e:
            conn.rollback()
            logger.error(f"Database error: {e}")
            raise
            
        finally:
            if cursor:
                cursor.close()
            self.return_connection(conn)
    
    @contextmanager
    def get_connection_context(self):
        """
        Context manager for getting a connection.
        
        Usage:
            with pool.get_connection_context() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM table")
        """
        conn = self.get_connection()
        
        try:
            yield conn
            conn.commit()
            
        except Exception as e:
            conn.rollback()
            logger.error(f"Database error: {e}")
            raise
            
        finally:
            self.return_connection(conn)
    
    def close_all(self):
        """Close all connections in the pool."""
        logger.info("Closing all connections in pool")
        
        closed_count = 0
        while not self._pool.empty():
            try:
                conn = self._pool.get(block=False)
                conn.close()
                closed_count += 1
            except Empty:
                break
            except Exception as e:
                logger.error(f"Error closing connection: {e}")
        
        logger.info(f"Closed {closed_count} connections")
    
    def get_stats(self) -> dict:
        """
        Get pool statistics.
        
        Returns:
            Dictionary with pool statistics
        """
        avg_wait_time = (self._total_wait_time / self._total_waits 
                        if self._total_waits > 0 else 0)
        
        return {
            "pool_size": self.pool_size,
            "created_connections": self._created_connections,
            "available_connections": self._pool.qsize(),
            "total_requests": self._total_requests,
            "total_waits": self._total_waits,
            "avg_wait_time_ms": round(avg_wait_time * 1000, 2),
            "wait_percentage": round((self._total_waits / self._total_requests * 100) 
                                    if self._total_requests > 0 else 0, 2)
        }
    
    def health_check(self) -> bool:
        """
        Perform health check on the pool.
        
        Returns:
            True if pool is healthy
        """
        try:
            with self.get_cursor() as cursor:
                cursor.execute("SELECT 1")
                return True
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close_all()
    
    def __del__(self):
        """Cleanup on deletion."""
        try:
            self.close_all()
        except Exception:
            pass


# Global pool instance (singleton pattern)
_global_pool: Optional[SQLiteConnectionPool] = None
_pool_lock = Lock()


def initialize_pool(database_path: str, pool_size: int = 5, 
                   timeout: int = 30) -> SQLiteConnectionPool:
    """
    Initialize global connection pool.
    
    Args:
        database_path: Path to database
        pool_size: Size of connection pool
        timeout: Connection timeout
        
    Returns:
        Connection pool instance
    """
    global _global_pool
    
    with _pool_lock:
        if _global_pool is not None:
            logger.warning("Pool already initialized, closing existing pool")
            _global_pool.close_all()
        
        _global_pool = SQLiteConnectionPool(
            database_path=database_path,
            pool_size=pool_size,
            timeout=timeout
        )
        
        return _global_pool


def get_pool() -> Optional[SQLiteConnectionPool]:
    """
    Get global connection pool instance.
    
    Returns:
        Connection pool or None if not initialized
    """
    return _global_pool


def close_pool():
    """Close global connection pool."""
    global _global_pool
    
    with _pool_lock:
        if _global_pool is not None:
            _global_pool.close_all()
            _global_pool = None
            logger.info("Global pool closed")
