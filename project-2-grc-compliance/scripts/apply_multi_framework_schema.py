#!/usr/bin/env python3
"""
Apply Multi-Framework Schema Extensions

This script applies the Phase 2 database schema updates to support
multiple compliance frameworks (ISO 27001, CIS Controls, PCI-DSS, SOC 2).
"""

import sqlite3
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def apply_schema(db_path: str):
    """Apply multi-framework schema to database."""
    
    logger.info(f"Connecting to database: {db_path}")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Read SQL file
        sql_file = Path(__file__).parent / 'create_multi_framework_schema.sql'
        logger.info(f"Reading SQL schema from: {sql_file}")
        
        with open(sql_file, 'r') as f:
            sql_script = f.read()
        
        # Execute SQL script
        logger.info("Executing schema updates...")
        cursor.executescript(sql_script)
        
        conn.commit()
        logger.info("✓ Schema applied successfully")
        
        # Verify tables were created
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' 
            AND (name LIKE '%framework%' OR name LIKE 'mf_%')
            ORDER BY name
        """)
        
        tables = [row[0] for row in cursor.fetchall()]
        logger.info(f"\n✓ Created {len(tables)} new tables:")
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            logger.info(f"  - {table}: {count} rows")
        
        # Show framework summary
        cursor.execute("""
            SELECT 
                (SELECT COUNT(*) FROM frameworks) as total_frameworks,
                (SELECT COUNT(*) FROM framework_controls) as total_controls,
                (SELECT COUNT(*) FROM mf_compliance_assessments) as total_assessments,
                (SELECT COUNT(*) FROM mf_control_risk_scores) as total_risk_scores
        """)
        
        stats = cursor.fetchone()
        logger.info(f"\n✓ Migration Summary:")
        logger.info(f"  Frameworks: {stats[0]}")
        logger.info(f"  Framework Controls: {stats[1]}")
        logger.info(f"  Assessments: {stats[2]}")
        logger.info(f"  Risk Scores: {stats[3]}")
        
        # Show available frameworks
        cursor.execute("SELECT framework_code, framework_name, framework_version FROM frameworks")
        frameworks = cursor.fetchall()
        logger.info(f"\n✓ Available Frameworks:")
        for fw in frameworks:
            logger.info(f"  - {fw[0]}: {fw[1]} {fw[2]}")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Error applying schema: {e}")
        conn.rollback()
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        conn.close()


def main():
    """Main function."""
    db_path = Path(__file__).parent.parent / 'data' / 'processed' / 'grc_analytics.db'
    
    if not db_path.exists():
        logger.error(f"Database not found: {db_path}")
        return 1
    
    logger.info("=" * 70)
    logger.info("PHASE 2: MULTI-FRAMEWORK SCHEMA APPLICATION")
    logger.info("=" * 70)
    
    success = apply_schema(str(db_path))
    
    if success:
        logger.info("\n" + "=" * 70)
        logger.info("✅ Schema application complete!")
        logger.info("=" * 70)
        logger.info("\nNext steps:")
        logger.info("  1. Ingest ISO 27001 controls")
        logger.info("  2. Ingest CIS Controls")
        logger.info("  3. Ingest PCI-DSS requirements")
        logger.info("  4. Ingest SOC 2 criteria")
        logger.info("  5. Build cross-framework mappings")
        return 0
    else:
        logger.info("\n" + "=" * 70)
        logger.info("⚠ Schema application failed")
        logger.info("=" * 70)
        return 1


if __name__ == '__main__':
    sys.exit(main())
