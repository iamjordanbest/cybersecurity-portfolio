#!/usr/bin/env python3
"""
Run All Framework Ingestion

Master script to ingest all supported compliance frameworks:
- NIST 800-53 Rev 5 (already in database)
- ISO 27001:2013
- CIS Controls v8
- PCI-DSS v4.0
- SOC 2 Trust Services Criteria
"""

import sys
import subprocess
from pathlib import Path
import sqlite3
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def run_ingestion_script(script_name: str) -> bool:
    """Run an ingestion script."""
    script_path = Path(__file__).parent / script_name
    
    logger.info(f"\n{'=' * 70}")
    logger.info(f"Running: {script_name}")
    logger.info('=' * 70)
    
    try:
        result = subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=False,
            check=True
        )
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to run {script_name}: {e}")
        return False


def show_framework_summary(db_path: str):
    """Show summary of all frameworks in the database."""
    logger.info("\n" + "=" * 70)
    logger.info("MULTI-FRAMEWORK SUMMARY")
    logger.info("=" * 70)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Framework summary
        cursor.execute('''
            SELECT 
                f.framework_code,
                f.framework_name,
                f.framework_version,
                COUNT(fc.fc_id) as control_count
            FROM frameworks f
            LEFT JOIN framework_controls fc ON f.framework_id = fc.framework_id
            WHERE f.is_active = 1
            GROUP BY f.framework_id
            ORDER BY f.framework_code
        ''')
        
        frameworks = cursor.fetchall()
        
        logger.info("\n✓ Supported Frameworks:")
        total_controls = 0
        for code, name, version, count in frameworks:
            logger.info(f"  {code:15} | {name:40} | v{version:8} | {count:4} controls")
            total_controls += count
        
        logger.info(f"\n  Total: {len(frameworks)} frameworks, {total_controls} controls")
        
        # Priority distribution across all frameworks
        cursor.execute('''
            SELECT 
                fc.priority_level,
                COUNT(*) as cnt,
                ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM framework_controls), 2) as pct
            FROM framework_controls fc
            JOIN frameworks f ON fc.framework_id = f.framework_id
            WHERE f.is_active = 1
            GROUP BY fc.priority_level
            ORDER BY 
                CASE fc.priority_level
                    WHEN 'critical' THEN 1
                    WHEN 'high' THEN 2
                    WHEN 'medium' THEN 3
                    WHEN 'low' THEN 4
                END
        ''')
        
        logger.info("\n✓ Overall Priority Distribution:")
        for priority, cnt, pct in cursor.fetchall():
            logger.info(f"  {priority:10} | {cnt:4} controls ({pct:5.2f}%)")
        
        # Check for NIST migration
        cursor.execute('''
            SELECT COUNT(*) FROM framework_controls
            WHERE framework_id = (SELECT framework_id FROM frameworks WHERE framework_code = 'NIST-800-53')
        ''')
        nist_count = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM nist_controls')
        original_nist = cursor.fetchone()[0]
        
        if nist_count == original_nist:
            logger.info(f"\n✓ NIST 800-53 migration: {nist_count}/{original_nist} controls (100%)")
        else:
            logger.warning(f"\n⚠ NIST 800-53 migration: {nist_count}/{original_nist} controls")
        
        # Check for existing assessments
        cursor.execute('SELECT COUNT(*) FROM mf_compliance_assessments')
        mf_assessments = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM compliance_assessments')
        original_assessments = cursor.fetchone()[0]
        
        logger.info(f"\n✓ Assessment Migration:")
        logger.info(f"  Original table: {original_assessments} assessments")
        logger.info(f"  Multi-framework table: {mf_assessments} assessments")
        
        # Show framework comparison view
        cursor.execute('''
            SELECT * FROM v_framework_compliance_summary
            ORDER BY framework_code
        ''')
        
        compliance_data = cursor.fetchall()
        if compliance_data:
            logger.info("\n✓ Framework Compliance Status:")
            for row in compliance_data:
                code, name, total, compliant, partial, non_compliant, not_assessed, pct = row
                logger.info(f"  {code:15} | {compliant:3}/{total:4} compliant ({pct:5.2f}%)")
        
    finally:
        conn.close()


def main():
    """Main function."""
    db_path = Path(__file__).parent.parent.parent / 'data' / 'processed' / 'grc_analytics.db'
    
    if not db_path.exists():
        logger.error(f"Database not found: {db_path}")
        return 1
    
    logger.info("=" * 70)
    logger.info("MULTI-FRAMEWORK INGESTION - MASTER SCRIPT")
    logger.info("=" * 70)
    logger.info("\nThis script will ingest all compliance frameworks:")
    logger.info("  1. ISO 27001:2013 (114 controls)")
    logger.info("  2. CIS Controls v8 (18 controls)")
    logger.info("  3. PCI-DSS v4.0 (12 requirements)")
    logger.info("  4. SOC 2 (19 criteria)")
    logger.info("\nNote: NIST 800-53 is already in the database (1,196 controls)")
    
    # Run ingestion scripts
    results = {
        'ISO 27001': run_ingestion_script('ingest_iso27001.py'),
        'CIS Controls': run_ingestion_script('ingest_cis_controls.py'),
        'PCI-DSS': run_ingestion_script('ingest_pci_dss.py'),
        'SOC 2': run_ingestion_script('ingest_soc2.py')
    }
    
    # Show results
    logger.info("\n" + "=" * 70)
    logger.info("INGESTION RESULTS")
    logger.info("=" * 70)
    
    for framework, success in results.items():
        status = "✅ SUCCESS" if success else "❌ FAILED"
        logger.info(f"  {framework:20} | {status}")
    
    all_success = all(results.values())
    
    # Show summary
    show_framework_summary(str(db_path))
    
    # Final message
    logger.info("\n" + "=" * 70)
    if all_success:
        logger.info("✅ ALL FRAMEWORKS INGESTED SUCCESSFULLY!")
    else:
        logger.info("⚠ SOME FRAMEWORKS FAILED TO INGEST")
    logger.info("=" * 70)
    
    logger.info("\nNext steps:")
    logger.info("  1. Build cross-framework mappings")
    logger.info("  2. Update analytics for multi-framework support")
    logger.info("  3. Update dashboard with framework selector")
    logger.info("  4. Generate unified compliance reports")
    
    return 0 if all_success else 1


if __name__ == '__main__':
    sys.exit(main())
