"""
Database connection management for GRC Analytics Platform

Provides SQLite connection with abstraction for easy PostgreSQL migration.
"""

import sqlite3
import logging
from pathlib import Path
from contextlib import contextmanager
from typing import Optional, Any, List, Dict
import os

logger = logging.getLogger(__name__)


class DatabaseConnection:
    """
    Database connection manager with context support.
    
    Provides a clean interface for database operations with automatic
    connection management and error handling.
    """
    
    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize database connection.
        
        Args:
            db_path: Path to SQLite database file. If None, uses default path.
        """
        if db_path is None:
            from src.config import settings
            # Remove sqlite:/// prefix if present as sqlite3.connect expects a file path
            db_url = settings.DATABASE_URL
            if db_url.startswith("sqlite:///"):
                db_path = db_url.replace("sqlite:///", "")
            else:
                db_path = db_url
        
        self.db_path = db_path
        self.connection: Optional[sqlite3.Connection] = None
        
    def connect(self) -> sqlite3.Connection:
        """
        Establish database connection.
        
        Returns:
            SQLite connection object
        """
        try:
            self.connection = sqlite3.connect(self.db_path)
            self.connection.row_factory = sqlite3.Row
            # Enable foreign keys
            self.connection.execute('PRAGMA foreign_keys = ON')
            logger.info(f"Connected to database: {self.db_path}")
            return self.connection
        except sqlite3.Error as e:
            logger.error(f"Error connecting to database: {e}")
            raise
    
    def close(self):
        """Close database connection."""
        if self.connection:
            self.connection.close()
            self.connection = None
            logger.info("Database connection closed")
    
    def __enter__(self):
        """Context manager entry."""
        return self.connect()
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        if exc_type is not None:
            if self.connection:
                self.connection.rollback()
                logger.warning("Transaction rolled back due to error")
        else:
            if self.connection:
                self.connection.commit()
        self.close()
        return False
    
    def execute(self, query: str, params: tuple = ()) -> sqlite3.Cursor:
        """
        Execute a single query.
        
        Args:
            query: SQL query to execute
            params: Query parameters
            
        Returns:
            Cursor object
        """
        if not self.connection:
            raise RuntimeError("Database connection not established")
        
        try:
            cursor = self.connection.cursor()
            cursor.execute(query, params)
            return cursor
        except sqlite3.Error as e:
            logger.error(f"Error executing query: {e}")
            logger.error(f"Query: {query}")
            raise
    
    def executemany(self, query: str, params_list: List[tuple]) -> sqlite3.Cursor:
        """
        Execute query with multiple parameter sets.
        
        Args:
            query: SQL query to execute
            params_list: List of parameter tuples
            
        Returns:
            Cursor object
        """
        if not self.connection:
            raise RuntimeError("Database connection not established")
        
        try:
            cursor = self.connection.cursor()
            cursor.executemany(query, params_list)
            return cursor
        except sqlite3.Error as e:
            logger.error(f"Error executing batch query: {e}")
            raise
    
    def fetchone(self, query: str, params: tuple = ()) -> Optional[sqlite3.Row]:
        """
        Execute query and fetch single result.
        
        Args:
            query: SQL query to execute
            params: Query parameters
            
        Returns:
            Single row result or None
        """
        cursor = self.execute(query, params)
        return cursor.fetchone()
    
    def fetchall(self, query: str, params: tuple = ()) -> List[sqlite3.Row]:
        """
        Execute query and fetch all results.
        
        Args:
            query: SQL query to execute
            params: Query parameters
            
        Returns:
            List of row results
        """
        cursor = self.execute(query, params)
        return cursor.fetchall()
    
    def commit(self):
        """Commit current transaction."""
        if self.connection:
            self.connection.commit()
    
    def rollback(self):
        """Rollback current transaction."""
        if self.connection:
            self.connection.rollback()


def get_db_connection(db_path: Optional[str] = None) -> DatabaseConnection:
    """
    Factory function to create database connection.
    
    Args:
        db_path: Optional path to database file
        
    Returns:
        DatabaseConnection instance
    """
    return DatabaseConnection(db_path)


@contextmanager
def get_db_session(db_path: Optional[str] = None):
    """
    Context manager for database sessions.
    
    Usage:
        with get_db_session() as conn:
            conn.execute("SELECT * FROM controls")
    
    Args:
        db_path: Optional path to database file
        
    Yields:
        SQLite connection object
    """
    db = DatabaseConnection(db_path)
    conn = db.connect()
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        logger.error(f"Database session error: {e}")
        raise
    finally:
        db.close()
