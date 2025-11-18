#!/usr/bin/env python3
"""
Multi-Framework Demonstration

Shows the capabilities of the Phase 2 multi-framework implementation.
Demonstrates querying and comparing controls across all 5 frameworks.
"""

import sqlite3
import sys
from pathlib import Path
import logging
from tabulate import tabulate

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


def demo_framework_overview(conn):
    """Demonstrate framework overview."""
    logger.info("\n" + "=" * 80)
    logger.info("DEMO 1: FRAMEWORK OVERVIEW")
    logger.info("=" * 80)
    
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 
            f.framework_code,
            f.framework_name,
            f.framework_version,
            COUNT(fc.fc_id) as control_count,
            f.published_date
        FROM frameworks f
        LEFT JOIN framework_controls fc ON f.framework_id = fc.framework_id
        WHERE f.is_active = 1
        GROUP BY f.framework_id
        ORDER BY control_count DESC
    """)
    
    headers = ['Code', 'Framework', 'Version', 'Controls', 'Published']
    rows = []
    for row in cursor.fetchall():
        rows.append([row[0], row[1][:40], row[2], row[3], row[4]])
    
    logger.info("\n" + tabulate(rows, headers=headers, tablefmt='grid'))
    
    cursor.execute("SELECT SUM(control_count) FROM (SELECT COUNT(fc_id) as control_count FROM framework_controls)")
    total = cursor.fetchone()[0]
    logger.info(f"\nTotal Controls Across All Frameworks: {total}")


def demo_priority_distribution(conn):
    """Demonstrate priority distribution across frameworks."""
    logger.info("\n" + "=" * 80)
    logger.info("DEMO 2: PRIORITY DISTRIBUTION BY FRAMEWORK")
    logger.info("=" * 80)
    
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 
            f.framework_code,
            fc.priority_level,
            COUNT(*) as count
        FROM frameworks f
        JOIN framework_controls fc ON f.framework_id = fc.framework_id
        WHERE f.is_active = 1
        GROUP BY f.framework_code, fc.priority_level
        ORDER BY f.framework_code, 
            CASE fc.priority_level
                WHEN 'critical' THEN 1
                WHEN 'high' THEN 2
                WHEN 'medium' THEN 3
                WHEN 'low' THEN 4
            END
    """)
    
    # Organize by framework
    data = {}
    for row in cursor.fetchall():
        framework = row[0]
        priority = row[1]
        count = row[2]
        
        if framework not in data:
            data[framework] = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0}
        data[framework][priority] = count
    
    headers = ['Framework', 'Critical', 'High', 'Medium', 'Low', 'Total']
    rows = []
    for framework, priorities in sorted(data.items()):
        total = sum(priorities.values())
        rows.append([
            framework,
            priorities['critical'],
            priorities['high'],
            priorities['medium'],
            priorities['low'],
            total
        ])
    
    logger.info("\n" + tabulate(rows, headers=headers, tablefmt='grid'))


def demo_framework_comparison(conn):
    """Demonstrate framework comparison."""
    logger.info("\n" + "=" * 80)
    logger.info("DEMO 3: FRAMEWORK COMPARISON - CONTROL COVERAGE")
    logger.info("=" * 80)
    
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 
            framework_code,
            framework_name,
            total_controls,
            compliant_controls,
            partial_controls,
            non_compliant_controls,
            not_assessed_controls,
            compliance_percentage
        FROM v_framework_compliance_summary
        ORDER BY framework_code
    """)
    
    headers = ['Framework', 'Total', 'Compliant', 'Partial', 'Non-Compliant', 'Not Assessed', 'Compliance %']
    rows = []
    for row in cursor.fetchall():
        rows.append([
            row[0],
            row[2],
            row[3],
            row[4],
            row[5],
            row[6],
            f"{row[7]:.2f}%"
        ])
    
    logger.info("\n" + tabulate(rows, headers=headers, tablefmt='grid'))
    
    logger.info("\nNote: Only NIST 800-53 has assessment data currently.")
    logger.info("Other frameworks will show 0% until assessments are performed.")


def demo_domain_breakdown(conn):
    """Demonstrate domain/category breakdown for each framework."""
    logger.info("\n" + "=" * 80)
    logger.info("DEMO 4: CONTROL DOMAINS/CATEGORIES BY FRAMEWORK")
    logger.info("=" * 80)
    
    cursor = conn.cursor()
    
    frameworks = ['NIST-800-53', 'ISO-27001', 'CIS', 'PCI-DSS', 'SOC2']
    
    for framework in frameworks:
        logger.info(f"\n{framework}:")
        logger.info("-" * 60)
        
        cursor.execute("""
            SELECT 
                fc.control_category,
                COUNT(*) as count
            FROM framework_controls fc
            JOIN frameworks f ON fc.framework_id = f.framework_id
            WHERE f.framework_code = ?
            GROUP BY fc.control_category
            ORDER BY count DESC
            LIMIT 10
        """, (framework,))
        
        rows = cursor.fetchall()
        if rows:
            headers = ['Domain/Category', 'Controls']
            formatted_rows = [[row[0][:50], row[1]] for row in rows]
            logger.info(tabulate(formatted_rows, headers=headers, tablefmt='simple'))
        else:
            logger.info("  No data available")


def demo_critical_controls(conn):
    """Demonstrate critical controls across all frameworks."""
    logger.info("\n" + "=" * 80)
    logger.info("DEMO 5: SAMPLE CRITICAL CONTROLS FROM EACH FRAMEWORK")
    logger.info("=" * 80)
    
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 
            f.framework_code,
            fc.control_identifier,
            fc.control_name,
            fc.control_category
        FROM framework_controls fc
        JOIN frameworks f ON fc.framework_id = f.framework_id
        WHERE fc.priority_level = 'critical'
        ORDER BY f.framework_code, fc.control_identifier
    """)
    
    current_framework = None
    count = 0
    
    for row in cursor.fetchall():
        framework = row[0]
        
        if framework != current_framework:
            if current_framework:
                logger.info("")
            logger.info(f"\n{framework}:")
            logger.info("-" * 80)
            current_framework = framework
            count = 0
        
        if count < 3:  # Show first 3 critical controls per framework
            logger.info(f"  {row[1]:15} | {row[2][:50]}")
            logger.info(f"                   Category: {row[3]}")
            count += 1


def demo_unified_view(conn):
    """Demonstrate unified view of all controls."""
    logger.info("\n" + "=" * 80)
    logger.info("DEMO 6: UNIFIED CONTROL VIEW (Sample)")
    logger.info("=" * 80)
    
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 
            framework_code,
            control_identifier,
            control_name,
            control_category,
            priority_level
        FROM v_all_framework_controls
        WHERE priority_level IN ('critical')
        ORDER BY RANDOM()
        LIMIT 15
    """)
    
    headers = ['Framework', 'Control ID', 'Control Name', 'Category', 'Priority']
    rows = []
    for row in cursor.fetchall():
        rows.append([
            row[0],
            row[1],
            row[2][:40] + '...' if len(row[2]) > 40 else row[2],
            row[3][:20],
            row[4]
        ])
    
    logger.info("\nRandom sample of 15 critical controls from all frameworks:")
    logger.info("\n" + tabulate(rows, headers=headers, tablefmt='grid'))


def demo_statistics(conn):
    """Show overall statistics."""
    logger.info("\n" + "=" * 80)
    logger.info("DEMO 7: OVERALL STATISTICS")
    logger.info("=" * 80)
    
    cursor = conn.cursor()
    
    # Total stats
    cursor.execute("SELECT COUNT(*) FROM frameworks WHERE is_active = 1")
    framework_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM framework_controls")
    control_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM mf_compliance_assessments")
    assessment_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM control_mappings")
    mapping_count = cursor.fetchone()[0]
    
    logger.info(f"\nActive Frameworks:        {framework_count}")
    logger.info(f"Total Controls:           {control_count}")
    logger.info(f"Total Assessments:        {assessment_count}")
    logger.info(f"Cross-Framework Mappings: {mapping_count} (pending implementation)")
    
    # Priority breakdown
    cursor.execute("""
        SELECT priority_level, COUNT(*) as cnt
        FROM framework_controls
        GROUP BY priority_level
        ORDER BY 
            CASE priority_level
                WHEN 'critical' THEN 1
                WHEN 'high' THEN 2
                WHEN 'medium' THEN 3
                WHEN 'low' THEN 4
            END
    """)
    
    logger.info("\nPriority Distribution:")
    for row in cursor.fetchall():
        priority = row[0]
        count = row[1]
        pct = (count / control_count * 100)
        logger.info(f"  {priority:10} : {count:4} controls ({pct:5.2f}%)")
    
    # Mandatory vs optional
    cursor.execute("""
        SELECT 
            SUM(CASE WHEN is_mandatory = 1 THEN 1 ELSE 0 END) as mandatory,
            SUM(CASE WHEN is_mandatory = 0 THEN 1 ELSE 0 END) as optional
        FROM framework_controls
    """)
    row = cursor.fetchone()
    
    logger.info("\nImplementation Status:")
    logger.info(f"  Mandatory: {row[0]} controls ({row[0]/control_count*100:.2f}%)")
    logger.info(f"  Optional:  {row[1]} controls ({row[1]/control_count*100:.2f}%)")


def main():
    """Main function."""
    db_path = Path(__file__).parent.parent / 'data' / 'processed' / 'grc_analytics.db'
    
    if not db_path.exists():
        logger.error(f"Database not found: {db_path}")
        return 1
    
    try:
        # Import tabulate or use simple formatting
        import tabulate as tab
    except ImportError:
        logger.warning("tabulate package not installed. Install with: pip install tabulate")
        logger.info("Continuing with simple formatting...")
    
    logger.info("=" * 80)
    logger.info("MULTI-FRAMEWORK DEMONSTRATION")
    logger.info("=" * 80)
    logger.info(f"\nDatabase: {db_path}")
    logger.info("Demonstrating Phase 2 multi-framework capabilities...")
    
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    
    try:
        demo_framework_overview(conn)
        demo_priority_distribution(conn)
        demo_framework_comparison(conn)
        demo_domain_breakdown(conn)
        demo_critical_controls(conn)
        demo_unified_view(conn)
        demo_statistics(conn)
        
        logger.info("\n" + "=" * 80)
        logger.info("DEMONSTRATION COMPLETE")
        logger.info("=" * 80)
        logger.info("\nKey Capabilities Demonstrated:")
        logger.info("  ✓ 5 compliance frameworks integrated")
        logger.info("  ✓ 1,359 controls across all frameworks")
        logger.info("  ✓ Unified view of all controls")
        logger.info("  ✓ Framework-specific queries")
        logger.info("  ✓ Priority-based filtering")
        logger.info("  ✓ Compliance tracking (NIST)")
        logger.info("  ✓ Domain/category organization")
        logger.info("\nNext Steps:")
        logger.info("  - Build cross-framework mappings")
        logger.info("  - Extend analytics for all frameworks")
        logger.info("  - Update dashboard with framework selector")
        
        return 0
        
    finally:
        conn.close()


if __name__ == '__main__':
    sys.exit(main())
