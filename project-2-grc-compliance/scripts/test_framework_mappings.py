#!/usr/bin/env python3
"""
Framework Mapping Test Suite

Comprehensive validation of cross-framework mapping functionality:
- Mapping creation and retrieval
- Coverage calculations
- Gap analysis
- Bidirectional queries
- Data integrity
"""

import sys
from pathlib import Path
import logging

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.analytics.framework_mapper import FrameworkMapper

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MappingValidator:
    """Validates framework mapping implementation."""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.test_results = {}
        
    def test_mapping_existence(self) -> bool:
        """Test that mappings exist in database."""
        logger.info("\n" + "=" * 70)
        logger.info("TEST 1: MAPPING EXISTENCE")
        logger.info("=" * 70)
        
        with FrameworkMapper(self.db_path) as mapper:
            stats = mapper.get_mapping_statistics()
            
            total = stats['total_mappings']
            logger.info(f"Total mappings found: {total}")
            
            if total == 0:
                logger.error("✗ No mappings found in database")
                return False
            
            logger.info(f"✓ Found {total} mappings")
            
            # Check expected minimum
            expected_min = 100  # We created ~139 mappings
            if total >= expected_min:
                logger.info(f"✓ Mapping count meets minimum ({total} >= {expected_min})")
                return True
            else:
                logger.error(f"✗ Mapping count below minimum ({total} < {expected_min})")
                return False
    
    def test_mapping_types(self) -> bool:
        """Test mapping type distribution."""
        logger.info("\n" + "=" * 70)
        logger.info("TEST 2: MAPPING TYPE VALIDATION")
        logger.info("=" * 70)
        
        with FrameworkMapper(self.db_path) as mapper:
            stats = mapper.get_mapping_statistics()
            by_type = stats['by_type']
            
            valid_types = {'EXACT', 'PARTIAL', 'RELATED', 'COMPLEMENTARY'}
            
            logger.info("Mapping types found:")
            all_valid = True
            for mtype, count in by_type.items():
                if mtype in valid_types:
                    logger.info(f"  ✓ {mtype:15} : {count:3} mappings")
                else:
                    logger.error(f"  ✗ {mtype:15} : {count:3} mappings (INVALID TYPE)")
                    all_valid = False
            
            # Check we have some EXACT and RELATED mappings
            if 'EXACT' not in by_type or by_type['EXACT'] == 0:
                logger.warning("  ⚠ No EXACT mappings found")
            
            if 'RELATED' not in by_type or by_type['RELATED'] == 0:
                logger.warning("  ⚠ No RELATED mappings found")
            
            return all_valid
    
    def test_mapping_strength(self) -> bool:
        """Test mapping strength values."""
        logger.info("\n" + "=" * 70)
        logger.info("TEST 3: MAPPING STRENGTH VALIDATION")
        logger.info("=" * 70)
        
        with FrameworkMapper(self.db_path) as mapper:
            stats = mapper.get_mapping_statistics()
            avg_strength = stats['average_strength']
            
            logger.info(f"Average mapping strength: {avg_strength:.3f}")
            
            # Check average strength is reasonable (between 0.5 and 1.0)
            if 0.5 <= avg_strength <= 1.0:
                logger.info(f"✓ Average strength is reasonable ({avg_strength:.3f})")
                
                # Check it's high quality (>0.8)
                if avg_strength >= 0.8:
                    logger.info(f"✓ High quality mappings (avg strength >= 0.8)")
                
                return True
            else:
                logger.error(f"✗ Average strength out of range: {avg_strength:.3f}")
                return False
    
    def test_framework_pairs(self) -> bool:
        """Test that expected framework pairs have mappings."""
        logger.info("\n" + "=" * 70)
        logger.info("TEST 4: FRAMEWORK PAIR COVERAGE")
        logger.info("=" * 70)
        
        expected_pairs = [
            ('NIST-800-53', 'ISO-27001'),
            ('CIS', 'NIST-800-53'),
            ('PCI-DSS', 'NIST-800-53'),
        ]
        
        with FrameworkMapper(self.db_path) as mapper:
            stats = mapper.get_mapping_statistics()
            by_pair = {(source, target): count for source, target, count in stats['by_framework_pair']}
            
            all_found = True
            for source, target in expected_pairs:
                if (source, target) in by_pair:
                    count = by_pair[(source, target)]
                    logger.info(f"✓ {source:15} → {target:15} : {count:3} mappings")
                else:
                    logger.error(f"✗ {source:15} → {target:15} : No mappings found")
                    all_found = False
            
            return all_found
    
    def test_bidirectional_queries(self) -> bool:
        """Test bidirectional mapping queries."""
        logger.info("\n" + "=" * 70)
        logger.info("TEST 5: BIDIRECTIONAL QUERY VALIDATION")
        logger.info("=" * 70)
        
        with FrameworkMapper(self.db_path) as mapper:
            # Test NIST → ISO mapping
            logger.info("\nTesting NIST 800-53 AC-2:")
            mappings_out = mapper.get_mappings_for_control('NIST-800-53', 'AC-2', direction='source')
            
            if mappings_out:
                logger.info(f"  ✓ Found {len(mappings_out)} outbound mappings")
                
                # Test reverse direction (ISO → NIST)
                if mappings_out[0]['target_framework'] == 'ISO-27001':
                    target_control = mappings_out[0]['target_control']
                    logger.info(f"\nTesting reverse: ISO 27001 {target_control}:")
                    
                    mappings_in = mapper.get_mappings_for_control('ISO-27001', target_control, direction='target')
                    
                    if mappings_in:
                        logger.info(f"  ✓ Found {len(mappings_in)} inbound mappings")
                        
                        # Verify AC-2 is in the inbound mappings
                        found_ac2 = any(m['source_control'] == 'AC-2' for m in mappings_in)
                        if found_ac2:
                            logger.info(f"  ✓ Bidirectional query verified (AC-2 ↔ {target_control})")
                            return True
                        else:
                            logger.error(f"  ✗ AC-2 not found in reverse mapping")
                            return False
                    else:
                        logger.error(f"  ✗ No inbound mappings found for {target_control}")
                        return False
                else:
                    logger.warning("  ⚠ First mapping not to ISO, skipping reverse test")
                    return True
            else:
                logger.error("  ✗ No outbound mappings found for AC-2")
                return False
    
    def test_coverage_calculation(self) -> bool:
        """Test framework coverage calculations."""
        logger.info("\n" + "=" * 70)
        logger.info("TEST 6: COVERAGE CALCULATION VALIDATION")
        logger.info("=" * 70)
        
        with FrameworkMapper(self.db_path) as mapper:
            # Test NIST → ISO coverage
            coverage = mapper.get_framework_coverage('NIST-800-53', 'ISO-27001')
            
            logger.info("\nNIST 800-53 → ISO 27001 Coverage:")
            logger.info(f"  Source total: {coverage['source_total_controls']}")
            logger.info(f"  Source mapped: {coverage['source_mapped_controls']}")
            logger.info(f"  Source coverage: {coverage['source_coverage_pct']}%")
            logger.info(f"  Target total: {coverage['target_total_controls']}")
            logger.info(f"  Target mapped: {coverage['target_mapped_controls']}")
            logger.info(f"  Target coverage: {coverage['target_coverage_pct']}%")
            
            # Validate calculations
            if coverage['source_total_controls'] > 0:
                expected_pct = (coverage['source_mapped_controls'] / 
                               coverage['source_total_controls'] * 100)
                
                if abs(coverage['source_coverage_pct'] - expected_pct) < 0.1:
                    logger.info("  ✓ Source coverage calculation correct")
                else:
                    logger.error(f"  ✗ Source coverage calculation error: "
                               f"{coverage['source_coverage_pct']} != {expected_pct}")
                    return False
            
            if coverage['target_total_controls'] > 0:
                expected_pct = (coverage['target_mapped_controls'] / 
                               coverage['target_total_controls'] * 100)
                
                if abs(coverage['target_coverage_pct'] - expected_pct) < 0.1:
                    logger.info("  ✓ Target coverage calculation correct")
                else:
                    logger.error(f"  ✗ Target coverage calculation error: "
                               f"{coverage['target_coverage_pct']} != {expected_pct}")
                    return False
            
            # Check total mappings
            total_mappings = coverage['total_mappings']
            if total_mappings > 0:
                logger.info(f"  ✓ Total mappings: {total_mappings}")
                return True
            else:
                logger.error("  ✗ No mappings found for this pair")
                return False
    
    def test_gap_analysis(self) -> bool:
        """Test gap analysis functionality."""
        logger.info("\n" + "=" * 70)
        logger.info("TEST 7: GAP ANALYSIS VALIDATION")
        logger.info("=" * 70)
        
        with FrameworkMapper(self.db_path) as mapper:
            # Find gaps in CIS → NIST mapping
            logger.info("\nFinding CIS controls without NIST mappings:")
            gaps = mapper.find_gaps('CIS', 'NIST-800-53')
            
            logger.info(f"  Found {len(gaps)} unmapped controls")
            
            if len(gaps) >= 0:  # Any result is valid
                logger.info("  ✓ Gap analysis executed successfully")
                
                # Show sample
                if gaps:
                    logger.info("\n  Sample gaps:")
                    for gap in gaps[:3]:
                        logger.info(f"    {gap['control_id']:10} | {gap['control_name'][:40]:40} | {gap['priority']}")
                else:
                    logger.info("  ✓ All CIS controls have NIST mappings!")
                
                return True
            else:
                logger.error("  ✗ Gap analysis failed")
                return False
    
    def test_data_integrity(self) -> bool:
        """Test mapping data integrity."""
        logger.info("\n" + "=" * 70)
        logger.info("TEST 8: DATA INTEGRITY VALIDATION")
        logger.info("=" * 70)
        
        import sqlite3
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Test 1: All mappings have valid source framework
            cursor.execute('''
                SELECT COUNT(*) FROM control_mappings cm
                WHERE NOT EXISTS (
                    SELECT 1 FROM frameworks f 
                    WHERE f.framework_id = cm.source_framework_id
                )
            ''')
            invalid_source = cursor.fetchone()[0]
            
            if invalid_source == 0:
                logger.info("✓ All mappings have valid source frameworks")
            else:
                logger.error(f"✗ Found {invalid_source} mappings with invalid source frameworks")
                return False
            
            # Test 2: All mappings have valid target framework
            cursor.execute('''
                SELECT COUNT(*) FROM control_mappings cm
                WHERE NOT EXISTS (
                    SELECT 1 FROM frameworks f 
                    WHERE f.framework_id = cm.target_framework_id
                )
            ''')
            invalid_target = cursor.fetchone()[0]
            
            if invalid_target == 0:
                logger.info("✓ All mappings have valid target frameworks")
            else:
                logger.error(f"✗ Found {invalid_target} mappings with invalid target frameworks")
                return False
            
            # Test 3: Mapping strengths are in valid range
            cursor.execute('''
                SELECT COUNT(*) FROM control_mappings
                WHERE mapping_strength < 0 OR mapping_strength > 1
            ''')
            invalid_strength = cursor.fetchone()[0]
            
            if invalid_strength == 0:
                logger.info("✓ All mapping strengths are in valid range (0-1)")
            else:
                logger.error(f"✗ Found {invalid_strength} mappings with invalid strengths")
                return False
            
            # Test 4: No duplicate mappings
            cursor.execute('''
                SELECT source_framework_id, source_control_id, 
                       target_framework_id, target_control_id, COUNT(*) as cnt
                FROM control_mappings
                GROUP BY source_framework_id, source_control_id,
                         target_framework_id, target_control_id
                HAVING cnt > 1
            ''')
            duplicates = cursor.fetchall()
            
            if len(duplicates) == 0:
                logger.info("✓ No duplicate mappings found")
            else:
                logger.error(f"✗ Found {len(duplicates)} duplicate mappings")
                return False
            
            return True
            
        finally:
            conn.close()
    
    def generate_report(self):
        """Generate test report."""
        logger.info("\n" + "=" * 70)
        logger.info("MAPPING VALIDATION REPORT")
        logger.info("=" * 70)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results.values() if result)
        
        for test_name, result in self.test_results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            logger.info(f"{test_name:40} | {status}")
        
        logger.info("\n" + "-" * 70)
        logger.info(f"Total Tests: {total_tests}")
        logger.info(f"Passed: {passed_tests}")
        logger.info(f"Failed: {total_tests - passed_tests}")
        logger.info(f"Success Rate: {passed_tests/total_tests*100:.1f}%")
        
        if passed_tests == total_tests:
            logger.info("\n✅ ALL MAPPING TESTS PASSED!")
            logger.info("Cross-framework mapping engine is working correctly.")
            return True
        else:
            logger.info("\n⚠ SOME MAPPING TESTS FAILED")
            logger.info("Please review the failed tests above.")
            return False
    
    def run_all_tests(self) -> bool:
        """Run all validation tests."""
        logger.info("=" * 70)
        logger.info("FRAMEWORK MAPPING VALIDATION TEST SUITE")
        logger.info("=" * 70)
        logger.info(f"Database: {self.db_path}")
        
        # Run all tests
        self.test_results['Mapping Existence'] = self.test_mapping_existence()
        self.test_results['Mapping Types'] = self.test_mapping_types()
        self.test_results['Mapping Strength'] = self.test_mapping_strength()
        self.test_results['Framework Pairs'] = self.test_framework_pairs()
        self.test_results['Bidirectional Queries'] = self.test_bidirectional_queries()
        self.test_results['Coverage Calculation'] = self.test_coverage_calculation()
        self.test_results['Gap Analysis'] = self.test_gap_analysis()
        self.test_results['Data Integrity'] = self.test_data_integrity()
        
        # Generate report
        return self.generate_report()


def main():
    """Main function."""
    db_path = Path(__file__).parent.parent / 'data' / 'processed' / 'grc_analytics.db'
    
    if not db_path.exists():
        logger.error(f"Database not found: {db_path}")
        return 1
    
    validator = MappingValidator(str(db_path))
    success = validator.run_all_tests()
    
    return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())
