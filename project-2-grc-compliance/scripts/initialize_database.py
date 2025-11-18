#!/usr/bin/env python3
"""
Initialize the GRC Analytics Database

This script creates the SQLite database and applies the enhanced schema.
"""

import sqlite3
import os
from pathlib import Path

def initialize_database():
    """Create the database and apply the enhanced schema."""
    
    # Get the project root directory
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    
    # Paths
    db_path = project_root / "data" / "processed" / "grc_analytics.db"
    schema_path = project_root / "scripts" / "create_enhanced_schema_sqlite.sql"
    
    # Ensure the processed data directory exists
    db_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Remove existing database if it exists
    if db_path.exists():
        print(f"⚠️  Removing existing database: {db_path}")
        db_path.unlink()
    
    # Read the schema SQL
    print(f"📖 Reading schema from: {schema_path}")
    with open(schema_path, 'r', encoding='utf-8') as f:
        schema_sql = f.read()
    
    # Create the database and apply schema
    print(f"🔨 Creating database: {db_path}")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Execute the schema (split by semicolon to handle multiple statements)
        cursor.executescript(schema_sql)
        conn.commit()
        print("✅ Schema applied successfully")
        
        # Verify tables were created
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = cursor.fetchall()
        
        print(f"\n📊 Created {len(tables)} tables:")
        for table in tables:
            print(f"   - {table[0]}")
        
        # Verify views were created
        cursor.execute("SELECT name FROM sqlite_master WHERE type='view' ORDER BY name")
        views = cursor.fetchall()
        
        if views:
            print(f"\n👁️  Created {len(views)} views:")
            for view in views:
                print(f"   - {view[0]}")
        
        # Verify indexes were created
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND name NOT LIKE 'sqlite_%' ORDER BY name")
        indexes = cursor.fetchall()
        
        if indexes:
            print(f"\n🔍 Created {len(indexes)} indexes:")
            for index in indexes:
                print(f"   - {index[0]}")
        
        print(f"\n✨ Database initialized successfully at: {db_path}")
        print(f"📏 Database size: {db_path.stat().st_size / 1024:.2f} KB")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating database: {e}")
        conn.rollback()
        return False
        
    finally:
        conn.close()

if __name__ == "__main__":
    print("=" * 70)
    print("GRC Analytics Platform - Database Initialization")
    print("=" * 70)
    print()
    
    success = initialize_database()
    
    print()
    print("=" * 70)
    if success:
        print("✅ Database initialization completed successfully!")
        print("\nNext steps:")
        print("  1. Run ingestion scripts to populate data:")
        print("     python src/ingestion/run_all_ingestion.py")
        print("  2. Or run individual ingestion scripts as needed")
    else:
        print("❌ Database initialization failed. Check errors above.")
    print("=" * 70)
