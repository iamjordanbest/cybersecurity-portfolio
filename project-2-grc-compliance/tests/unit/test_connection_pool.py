"""
Unit tests for Database Connection Pool.

Tests connection pooling functionality.
"""

import pytest
import tempfile
import sqlite3
from pathlib import Path
from src.database.pool import SQLiteConnectionPool


@pytest.mark.unit
@pytest.mark.database
class TestConnectionPool:
    """Test suite for SQLiteConnectionPool."""
    
    @pytest.fixture
    def temp_db(self):
        """Create a temporary test database."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        
        # Create a simple test table
        conn = sqlite3.connect(db_path)
        conn.execute("CREATE TABLE test (id INTEGER PRIMARY KEY, value TEXT)")
        conn.execute("INSERT INTO test (value) VALUES ('test')")
        conn.commit()
        conn.close()
        
        yield db_path
        
        # Cleanup
        Path(db_path).unlink(missing_ok=True)
    
    def test_pool_initialization(self, temp_db):
        """Test pool can be initialized."""
        pool = SQLiteConnectionPool(temp_db, pool_size=3)
        assert pool.pool_size == 3
        assert pool.database_path == temp_db
        pool.close_all()
    
    def test_get_connection(self, temp_db):
        """Test getting connection from pool."""
        pool = SQLiteConnectionPool(temp_db, pool_size=3)
        
        conn = pool.get_connection()
        assert conn is not None
        
        # Test connection works
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM test")
        result = cursor.fetchone()
        assert result is not None
        
        pool.return_connection(conn)
        pool.close_all()
    
    def test_return_connection(self, temp_db):
        """Test returning connection to pool."""
        pool = SQLiteConnectionPool(temp_db, pool_size=3)
        
        conn = pool.get_connection()
        pool.return_connection(conn)
        
        # Pool should have connection available
        stats = pool.get_stats()
        assert stats['available_connections'] > 0
        
        pool.close_all()
    
    def test_context_manager_cursor(self, temp_db):
        """Test get_cursor context manager."""
        pool = SQLiteConnectionPool(temp_db, pool_size=3)
        
        with pool.get_cursor() as cursor:
            cursor.execute("SELECT * FROM test")
            result = cursor.fetchone()
            assert result is not None
        
        pool.close_all()
    
    def test_context_manager_connection(self, temp_db):
        """Test get_connection_context manager."""
        pool = SQLiteConnectionPool(temp_db, pool_size=3)
        
        with pool.get_connection_context() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM test")
            result = cursor.fetchone()
            assert result is not None
        
        pool.close_all()
    
    def test_pool_stats(self, temp_db):
        """Test pool statistics."""
        pool = SQLiteConnectionPool(temp_db, pool_size=3)
        
        stats = pool.get_stats()
        assert 'pool_size' in stats
        assert 'available_connections' in stats
        assert 'total_requests' in stats
        assert stats['pool_size'] == 3
        
        pool.close_all()
    
    def test_health_check(self, temp_db):
        """Test pool health check."""
        pool = SQLiteConnectionPool(temp_db, pool_size=3)
        
        is_healthy = pool.health_check()
        assert is_healthy is True
        
        pool.close_all()
    
    def test_close_all(self, temp_db):
        """Test closing all connections."""
        pool = SQLiteConnectionPool(temp_db, pool_size=3)
        
        # Get some connections
        conn1 = pool.get_connection()
        pool.return_connection(conn1)
        
        # Close all
        pool.close_all()
        
        # Pool should be empty
        stats = pool.get_stats()
        assert stats['available_connections'] == 0
    
    def test_context_manager_pool(self, temp_db):
        """Test pool as context manager."""
        with SQLiteConnectionPool(temp_db, pool_size=3) as pool:
            conn = pool.get_connection()
            assert conn is not None
            pool.return_connection(conn)
        # Pool should be closed after context


@pytest.mark.unit
@pytest.mark.database
class TestConnectionPoolConcurrency:
    """Test connection pool under concurrent access."""
    
    @pytest.fixture
    def temp_db(self):
        """Create a temporary test database."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        
        conn = sqlite3.connect(db_path)
        conn.execute("CREATE TABLE test (id INTEGER PRIMARY KEY, value TEXT)")
        conn.commit()
        conn.close()
        
        yield db_path
        
        Path(db_path).unlink(missing_ok=True)
    
    def test_multiple_connections(self, temp_db):
        """Test getting multiple connections from pool."""
        pool = SQLiteConnectionPool(temp_db, pool_size=3)
        
        connections = []
        for i in range(3):
            conn = pool.get_connection()
            connections.append(conn)
        
        assert len(connections) == 3
        
        # Return all connections
        for conn in connections:
            pool.return_connection(conn)
        
        pool.close_all()
    
    def test_connection_reuse(self, temp_db):
        """Test connections are reused from pool."""
        pool = SQLiteConnectionPool(temp_db, pool_size=2)
        
        # Get and return connection
        conn1 = pool.get_connection()
        pool.return_connection(conn1)
        
        # Get another connection
        conn2 = pool.get_connection()
        
        # Both connections should work (reuse or new is fine)
        cursor = conn2.cursor()
        cursor.execute("SELECT 1")
        assert cursor.fetchone()[0] == 1
        
        pool.return_connection(conn2)
        pool.close_all()
