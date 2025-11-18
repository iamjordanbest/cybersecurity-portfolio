#!/usr/bin/env python3
"""
Phase 2 Validation and Testing

Comprehensive validation of multi-framework implementation:
- Database schema integrity
- Framework data completeness
- Data relationships and foreign keys
- View functionality
- Performance benchmarks
"""

import sqlite3
import sys
from pathlib import Path
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Phase2Validator:
    """Validates Phase 2 multi-framework implementation."""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = None
        self.validation_results = {}
        
    def connect(self):
        """Connect to database."""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        
    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
    
    def validate_schema(self) -> bool:
        """Validate database schema."""
        logger.info("\n" + "=" * 70)
        logger.info("TEST 1: DATABASE SCHEMA VALIDATION")
        logger.info("=" * 70)
        
        cursor = self.conn.cursor()
        
        # Check for required tables
        required_tables = [
            'frameworks',
            'framework_controls',
            'control_mappings',
            'framework_profiles',
            'profile_controls',
            'mf_compliance_assessments',
            'mf_control_risk_scores',
            'framework_metadata'
        ]
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        existing_tables = [row[0] for row in cursor.fetchall()]
        
        missing_tables = []
        for table in required_tables:
            if table in existing_tables:
                logger.info(f"✓ Table exists: {table}")
            else:
                logger.error(f"✗ Table missing: {table}")
                missing_tables.append(table)
        
        # Check for required views
        required_views = [
            'v_all_framework_controls',
            'v_unified_compliance_status',
            'v_control_mapping_relationships',
            'v_framework_compliance_summary'
        ]
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='view'")
        existing_views = [row[0] for row in cursor.fetchall()]
        
        logger.info("\nViews:")
        missing_views = []
        for view in required_views:
            if view in existing_views:
                logger.info(f"✓ View exists: {view}")
            else:
                logger.error(f"✗ View missing: {view}")
                missing_views.append(view)
        
        # Check indexes
        cursor.execute("""
            SELECT COUNT(*) FROM sqlite_master 
            WHERE type='index' AND sql IS NOT NULL
        """)
        index_count = cursor.fetchone()[0]
        logger.info(f"\n✓ Total indexes: {index_count}")
        
        success = len(missing_tables) == 0 and len(missing_views) == 0
        self.validation_results['schema'] = {
            'success': success,
            'missing_tables': missing_tables,
            'missing_views': missing_views,
            'index_count': index_count
        }
        
        return success
    
    def validate_frameworks(self) -> bool:
        """Validate framework data."""
        logger.info("\n" + "=" * 70)
        logger.info("TEST 2: FRAMEWORK DATA VALIDATION")
        logger.info("=" * 70)
        
        cursor = self.conn.cursor()
        
        # Expected frameworks
        expected_frameworks = {
            'NIST-800-53': {'min_controls': 1000, 'version': 'Revision 5'},
            'ISO-27001': {'min_controls': 100, 'version': '2013'},
            'CIS': {'min_controls': 18, 'version': 'Version 8'},
            'PCI-DSS': {'min_controls': 12, 'version': 'Version 4.0'},
            'SOC2': {'min_controls': 19, 'version': '2017'}
        }
        
        cursor.execute("""
            SELECT 
                f.framework_code,
                f.framework_name,
                f.framework_version,
                f.is_active,
                COUNT(fc.fc_id) as control_count
            FROM frameworks f
            LEFT JOIN framework_controls fc ON f.framework_id = fc.framework_id
            GROUP BY f.framework_id
        """)
        
        frameworks = cursor.fetchall()
        
        all_valid = True
        for row in frameworks:
            code = row['framework_code']
            count = row['control_count']
            version = row['framework_version']
            is_active = row['is_active']
            
            if code in expected_frameworks:
                expected = expected_frameworks[code]
                min_controls = expected['min_controls']
                
                if count >= min_controls and is_active == 1:
                    logger.info(f"✓ {code:15} | {count:4} controls | v{version}")
                else:
                    logger.error(f"✗ {code:15} | {count:4} controls (expected >={min_controls})")
                    all_valid = False
            else:
                logger.warning(f"? {code:15} | {count:4} controls | Unknown framework")
        
        self.validation_results['frameworks'] = {
            'success': all_valid,
            'framework_count': len(frameworks),
            'frameworks': [dict(row) for row in frameworks]
        }
        
        return all_valid
    
    def validate_data_integrity(self) -> bool:
        """Validate data integrity and relationships."""
        logger.info("\n" + "=" * 70)
        logger.info("TEST 3: DATA INTEGRITY VALIDATION")
        logger.info("=" * 70)
        
        cursor = self.conn.cursor()
        
        tests_passed = []
        tests_failed = []
        
        # Test 1: All framework_controls have valid framework_id
        cursor.execute("""
            SELECT COUNT(*) FROM framework_controls fc
            WHERE NOT EXISTS (
                SELECT 1 FROM frameworks f WHERE f.framework_id = fc.framework_id
            )
        """)
        orphaned_controls = cursor.fetchone()[0]
        
        if orphaned_controls == 0:
            logger.info("✓ All controls have valid framework references")
            tests_passed.append("framework_controls foreign keys")
        else:
            logger.error(f"✗ Found {orphaned_controls} orphaned controls")
            tests_failed.append("framework_controls foreign keys")
        
        # Test 2: No duplicate control identifiers within same framework
        cursor.execute("""
            SELECT framework_id, control_identifier, COUNT(*) as cnt
            FROM framework_controls
            GROUP BY framework_id, control_identifier
            HAVING cnt > 1
        """)
        duplicates = cursor.fetchall()
        
        if len(duplicates) == 0:
            logger.info("✓ No duplicate control identifiers within frameworks")
            tests_passed.append("unique control identifiers")
        else:
            logger.error(f"✗ Found {len(duplicates)} duplicate control identifiers")
            tests_failed.append("unique control identifiers")
        
        # Test 3: Priority levels are valid
        cursor.execute("""
            SELECT DISTINCT priority_level FROM framework_controls
            WHERE priority_level NOT IN ('critical', 'high', 'medium', 'low')
        """)
        invalid_priorities = cursor.fetchall()
        
        if len(invalid_priorities) == 0:
            logger.info("✓ All priority levels are valid")
            tests_passed.append("valid priority levels")
        else:
            logger.error(f"✗ Found {len(invalid_priorities)} invalid priority levels")
            tests_failed.append("valid priority levels")
        
        # Test 4: Check NIST migration completeness
        cursor.execute("SELECT COUNT(*) FROM nist_controls")
        nist_original = cursor.fetchone()[0]
        
        cursor.execute("""
            SELECT COUNT(*) FROM framework_controls
            WHERE framework_id = (SELECT framework_id FROM frameworks WHERE framework_code = 'NIST-800-53')
        """)
        nist_migrated = cursor.fetchone()[0]
        
        if nist_original == nist_migrated:
            logger.info(f"✓ NIST controls migrated: {nist_migrated}/{nist_original} (100%)")
            tests_passed.append("NIST migration completeness")
        else:
            logger.error(f"✗ NIST controls migrated: {nist_migrated}/{nist_original} ({nist_migrated/nist_original*100:.1f}%)")
            tests_failed.append("NIST migration completeness")
        
        # Test 5: Check assessment migration
        cursor.execute("SELECT COUNT(*) FROM compliance_assessments")
        orig_assessments = cursor.fetchone()[0]
        
        cursor.execute("""
            SELECT COUNT(*) FROM mf_compliance_assessments
            WHERE framework_id = (SELECT framework_id FROM frameworks WHERE framework_code = 'NIST-800-53')
        """)
        mf_assessments = cursor.fetchone()[0]
        
        migration_pct = (mf_assessments / orig_assessments * 100) if orig_assessments > 0 else 0
        if migration_pct >= 80:  # At least 80% migrated (some might be duplicates)
            logger.info(f"✓ Assessments migrated: {mf_assessments}/{orig_assessments} ({migration_pct:.1f}%)")
            tests_passed.append("assessment migration")
        else:
            logger.error(f"✗ Assessments migrated: {mf_assessments}/{orig_assessments} ({migration_pct:.1f}%)")
            tests_failed.append("assessment migration")
        
        success = len(tests_failed) == 0
        self.validation_results['data_integrity'] = {
            'success': success,
            'tests_passed': tests_passed,
            'tests_failed': tests_failed
        }
        
        return success
    
    def validate_views(self) -> bool:
        """Validate that views work correctly."""
        logger.info("\n" + "=" * 70)
        logger.info("TEST 4: VIEW FUNCTIONALITY VALIDATION")
        logger.info("=" * 70)
        
        cursor = self.conn.cursor()
        
        tests_passed = []
        tests_failed = []
        
        # Test view: v_all_framework_controls
        try:
            cursor.execute("SELECT COUNT(*) FROM v_all_framework_controls")
            count = cursor.fetchone()[0]
            logger.info(f"✓ v_all_framework_controls: {count} rows")
            tests_passed.append("v_all_framework_controls")
        except Exception as e:
            logger.error(f"✗ v_all_framework_controls failed: {e}")
            tests_failed.append("v_all_framework_controls")
        
        # Test view: v_unified_compliance_status
        try:
            cursor.execute("SELECT COUNT(*) FROM v_unified_compliance_status")
            count = cursor.fetchone()[0]
            logger.info(f"✓ v_unified_compliance_status: {count} rows")
            tests_passed.append("v_unified_compliance_status")
        except Exception as e:
            logger.error(f"✗ v_unified_compliance_status failed: {e}")
            tests_failed.append("v_unified_compliance_status")
        
        # Test view: v_framework_compliance_summary
        try:
            cursor.execute("SELECT * FROM v_framework_compliance_summary")
            rows = cursor.fetchall()
            logger.info(f"✓ v_framework_compliance_summary: {len(rows)} frameworks")
            
            # Show compliance for each framework
            for row in rows:
                code = row['framework_code']
                compliant = row['compliant_controls']
                total = row['total_controls']
                pct = row['compliance_percentage']
                logger.info(f"  {code:15} | {compliant:4}/{total:4} ({pct:5.2f}%)")
            
            tests_passed.append("v_framework_compliance_summary")
        except Exception as e:
            logger.error(f"✗ v_framework_compliance_summary failed: {e}")
            tests_failed.append("v_framework_compliance_summary")
        
        # Test view: v_control_mapping_relationships
        try:
            cursor.execute("SELECT COUNT(*) FROM v_control_mapping_relationships")
            count = cursor.fetchone()[0]
            logger.info(f"✓ v_control_mapping_relationships: {count} mappings (expected 0 for now)")
            tests_passed.append("v_control_mapping_relationships")
        except Exception as e:
            logger.error(f"✗ v_control_mapping_relationships failed: {e}")
            tests_failed.append("v_control_mapping_relationships")
        
        success = len(tests_failed) == 0
        self.validation_results['views'] = {
            'success': success,
            'tests_passed': tests_passed,
            'tests_failed': tests_failed
        }
        
        return success
    
    def validate_queries(self) -> bool:
        """Validate common query patterns."""
        logger.info("\n" + "=" * 70)
        logger.info("TEST 5: QUERY PATTERN VALIDATION")
        logger.info("=" * 70)
        
        cursor = self.conn.cursor()
        
        tests_passed = []
        tests_failed = []
        
        # Query 1: Get all controls for a specific framework
        try:
            cursor.execute("""
                SELECT COUNT(*) FROM framework_controls
                WHERE framework_id = (SELECT framework_id FROM frameworks WHERE framework_code = 'ISO-27001')
            """)
            count = cursor.fetchone()[0]
            logger.info(f"✓ Get ISO 27001 controls: {count} results")
            tests_passed.append("framework-specific query")
        except Exception as e:
            logger.error(f"✗ Framework-specific query failed: {e}")
            tests_failed.append("framework-specific query")
        
        # Query 2: Get controls by priority across all frameworks
        try:
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
            results = cursor.fetchall()
            logger.info(f"✓ Get controls by priority: {len(results)} priority levels")
            tests_passed.append("priority aggregation")
        except Exception as e:
            logger.error(f"✗ Priority aggregation failed: {e}")
            tests_failed.append("priority aggregation")
        
        # Query 3: Get framework with most controls
        try:
            cursor.execute("""
                SELECT f.framework_code, COUNT(fc.fc_id) as cnt
                FROM frameworks f
                JOIN framework_controls fc ON f.framework_id = fc.framework_id
                GROUP BY f.framework_id
                ORDER BY cnt DESC
                LIMIT 1
            """)
            result = cursor.fetchone()
            logger.info(f"✓ Framework with most controls: {result['framework_code']} ({result['cnt']} controls)")
            tests_passed.append("aggregation with join")
        except Exception as e:
            logger.error(f"✗ Aggregation with join failed: {e}")
            tests_failed.append("aggregation with join")
        
        # Query 4: Multi-framework assessment query
        try:
            cursor.execute("""
                SELECT 
                    f.framework_code,
                    COUNT(DISTINCT mfa.control_identifier) as assessed_controls
                FROM frameworks f
                LEFT JOIN mf_compliance_assessments mfa ON f.framework_id = mfa.framework_id
                GROUP BY f.framework_id
            """)
            results = cursor.fetchall()
            logger.info(f"✓ Multi-framework assessment summary: {len(results)} frameworks")
            tests_passed.append("multi-framework assessment query")
        except Exception as e:
            logger.error(f"✗ Multi-framework assessment query failed: {e}")
            tests_failed.append("multi-framework assessment query")
        
        success = len(tests_failed) == 0
        self.validation_results['queries'] = {
            'success': success,
            'tests_passed': tests_passed,
            'tests_failed': tests_failed
        }
        
        return success
    
    def performance_benchmark(self) -> bool:
        """Run performance benchmarks."""
        logger.info("\n" + "=" * 70)
        logger.info("TEST 6: PERFORMANCE BENCHMARKS")
        logger.info("=" * 70)
        
        import time
        cursor = self.conn.cursor()
        
        benchmarks = []
        
        # Benchmark 1: Framework controls query
        start = time.time()
        cursor.execute("SELECT * FROM framework_controls LIMIT 100")
        cursor.fetchall()
        elapsed_ms = (time.time() - start) * 1000
        logger.info(f"✓ Select 100 controls: {elapsed_ms:.2f}ms")
        benchmarks.append(('select_controls', elapsed_ms))
        
        # Benchmark 2: Framework summary view
        start = time.time()
        cursor.execute("SELECT * FROM v_framework_compliance_summary")
        cursor.fetchall()
        elapsed_ms = (time.time() - start) * 1000
        logger.info(f"✓ Framework summary view: {elapsed_ms:.2f}ms")
        benchmarks.append(('framework_summary', elapsed_ms))
        
        # Benchmark 3: All controls view
        start = time.time()
        cursor.execute("SELECT * FROM v_all_framework_controls LIMIT 100")
        cursor.fetchall()
        elapsed_ms = (time.time() - start) * 1000
        logger.info(f"✓ All controls view (100): {elapsed_ms:.2f}ms")
        benchmarks.append(('all_controls_view', elapsed_ms))
        
        # Benchmark 4: Complex aggregation
        start = time.time()
        cursor.execute("""
            SELECT 
                f.framework_code,
                fc.priority_level,
                COUNT(*) as cnt
            FROM frameworks f
            JOIN framework_controls fc ON f.framework_id = fc.framework_id
            GROUP BY f.framework_code, fc.priority_level
        """)
        cursor.fetchall()
        elapsed_ms = (time.time() - start) * 1000
        logger.info(f"✓ Complex aggregation: {elapsed_ms:.2f}ms")
        benchmarks.append(('complex_aggregation', elapsed_ms))
        
        # All benchmarks should be under 100ms for good performance
        avg_time = sum(b[1] for b in benchmarks) / len(benchmarks)
        logger.info(f"\n✓ Average query time: {avg_time:.2f}ms")
        
        success = avg_time < 100
        self.validation_results['performance'] = {
            'success': success,
            'avg_time_ms': avg_time,
            'benchmarks': benchmarks
        }
        
        return success
    
    def generate_report(self):
        """Generate validation report."""
        logger.info("\n" + "=" * 70)
        logger.info("PHASE 2 VALIDATION REPORT")
        logger.info("=" * 70)
        
        total_tests = 0
        passed_tests = 0
        
        for test_name, results in self.validation_results.items():
            total_tests += 1
            if results['success']:
                passed_tests += 1
                status = "✅ PASS"
            else:
                status = "❌ FAIL"
            
            logger.info(f"{test_name.upper():30} | {status}")
        
        logger.info("\n" + "-" * 70)
        logger.info(f"Total Tests: {total_tests}")
        logger.info(f"Passed: {passed_tests}")
        logger.info(f"Failed: {total_tests - passed_tests}")
        logger.info(f"Success Rate: {passed_tests/total_tests*100:.1f}%")
        
        if passed_tests == total_tests:
            logger.info("\n✅ ALL VALIDATION TESTS PASSED!")
            logger.info("Phase 2 implementation is working correctly.")
            return True
        else:
            logger.info("\n⚠ SOME VALIDATION TESTS FAILED")
            logger.info("Please review the failed tests above.")
            return False
    
    def run_all_tests(self) -> bool:
        """Run all validation tests."""
        try:
            self.connect()
            
            logger.info("=" * 70)
            logger.info("PHASE 2 VALIDATION TEST SUITE")
            logger.info("=" * 70)
            logger.info(f"Database: {self.db_path}")
            logger.info(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
            # Run all tests
            self.validate_schema()
            self.validate_frameworks()
            self.validate_data_integrity()
            self.validate_views()
            self.validate_queries()
            self.performance_benchmark()
            
            # Generate report
            success = self.generate_report()
            
            return success
            
        finally:
            self.close()


def main():
    """Main function."""
    db_path = Path(__file__).parent.parent / 'data' / 'processed' / 'grc_analytics.db'
    
    if not db_path.exists():
        logger.error(f"Database not found: {db_path}")
        return 1
    
    validator = Phase2Validator(str(db_path))
    success = validator.run_all_tests()
    
    return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())
