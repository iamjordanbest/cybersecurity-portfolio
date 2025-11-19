"""
API Dependencies

Provides dependency injection for database connections,
authentication, and other shared resources.
"""

from fastapi import Depends, HTTPException, status
from pathlib import Path
import sqlite3
from typing import Generator

from src.database.pool import SQLiteConnectionPool, get_pool, initialize_pool
from src.cache.redis_manager import CacheManager
from src.analytics.framework_mapper import FrameworkMapper
from src.analytics.multi_framework_analytics import MultiFrameworkAnalytics


# Database path
DB_PATH = Path(__file__).parent.parent.parent / 'data' / 'processed' / 'grc_analytics.db'

# Global instances
_db_pool: SQLiteConnectionPool = None
_cache_manager: CacheManager = None


def get_database_connection() -> Generator:
    """
    Dependency to get database connection from pool.
    
    Usage:
        @app.get("/endpoint")
        def endpoint(db = Depends(get_database_connection)):
            cursor = db.cursor()
            ...
    """
    pool = get_pool()
    if pool is None:
        # Initialize pool if not already done
        pool = initialize_pool(str(DB_PATH), pool_size=10)
    
    conn = pool.get_connection()
    try:
        yield conn
    finally:
        pool.return_connection(conn)


def get_cache_manager() -> CacheManager:
    """
    Dependency to get cache manager instance.
    
    Usage:
        @app.get("/endpoint")
        def endpoint(cache = Depends(get_cache_manager)):
            cached_data = cache.get("key")
            ...
    """
    global _cache_manager
    
    if _cache_manager is None:
        _cache_manager = CacheManager()
    
    return _cache_manager


def get_framework_mapper() -> FrameworkMapper:
    """
    Dependency to get framework mapper instance.
    
    Usage:
        @app.get("/endpoint")
        def endpoint(mapper = Depends(get_framework_mapper)):
            coverage = mapper.get_framework_coverage(...)
            ...
    """
    return FrameworkMapper(str(DB_PATH))


def get_analytics_engine() -> MultiFrameworkAnalytics:
    """
    Dependency to get multi-framework analytics engine.
    
    Usage:
        @app.get("/endpoint")
        def endpoint(analytics = Depends(get_analytics_engine)):
            compliance = analytics.get_unified_compliance_status()
            ...
    """
    return MultiFrameworkAnalytics(str(DB_PATH))


def verify_framework_exists(framework_code: str, db = Depends(get_database_connection)) -> str:
    """
    Verify framework exists in database.
    
    Args:
        framework_code: Framework code to verify
        db: Database connection
        
    Returns:
        framework_code if exists
        
    Raises:
        HTTPException: If framework not found
    """
    cursor = db.cursor()
    cursor.execute(
        "SELECT framework_code FROM frameworks WHERE framework_code = ? AND is_active = 1",
        (framework_code,)
    )
    
    result = cursor.fetchone()
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Framework '{framework_code}' not found"
        )
    
    return framework_code


def verify_control_exists(framework_code: str, control_id: str,
                         db = Depends(get_database_connection)) -> tuple:
    """
    Verify control exists in framework.
    
    Args:
        framework_code: Framework code
        control_id: Control identifier
        db: Database connection
        
    Returns:
        (framework_code, control_id) if exists
        
    Raises:
        HTTPException: If control not found
    """
    cursor = db.cursor()
    cursor.execute("""
        SELECT fc.control_identifier
        FROM framework_controls fc
        JOIN frameworks f ON fc.framework_id = f.framework_id
        WHERE f.framework_code = ? AND fc.control_identifier = ?
    """, (framework_code, control_id))
    
    result = cursor.fetchone()
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Control '{control_id}' not found in framework '{framework_code}'"
        )
    
    return (framework_code, control_id)
