#!/usr/bin/env python3
"""
Framework Mapping Demonstration

Shows how cross-framework mappings work and demonstrates
various use cases for compliance mapping analysis.
"""

import sys
from pathlib import Path
import logging

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.analytics.framework_mapper import FrameworkMapper

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


def demo_control_mappings():
    """Demonstrate control-level mappings."""
    logger.info("\n" + "=" * 80)
    logger.info("DEMO 1: CONTROL-LEVEL MAPPINGS")
    logger.info("=" * 80)
    
    db_path = Path(__file__).parent.parent / 'data' / 'processed' / 'grc_analytics.db'
    
    with FrameworkMapper(str(db_path)) as mapper:
        # Show mappings for a NIST control
        logger.info("\nNIST 800-53 AC-2 (Account Management) maps to:")
        logger.info("-" * 80)
        
        mappings = mapper.get_mappings_for_control('NIST-800-53', 'AC-2')
        for mapping in mappings:
            if mapping['direction'] == 'outbound':
                logger.info(f"  → {mapping['target_framework']:15} {mapping['target_control']:10} "
                          f"({mapping['mapping_type']:10}, strength: {mapping['mapping_strength']:.2f})")
                logger.info(f"     {mapping['target_control_name']}")
        
        # Show mappings for an ISO control
        logger.info("\n\nISO 27001 A.9.2.1 (User registration) maps to:")
        logger.info("-" * 80)
        
        mappings = mapper.get_mappings_for_control('ISO-27001', 'A.9.2.1')
        for mapping in mappings:
            if mapping['direction'] == 'inbound':
                logger.info(f"  ← {mapping['source_framework']:15} {mapping['source_control']:10} "
                          f"({mapping['mapping_type']:10}, strength: {mapping['mapping_strength']:.2f})")
        
        # Show mappings for a CIS control
        logger.info("\n\nCIS Control 1 (Asset Inventory) maps to:")
        logger.info("-" * 80)
        
        mappings = mapper.get_mappings_for_control('CIS', 'CIS-1')
        for mapping in mappings:
            if mapping['direction'] == 'outbound':
                logger.info(f"  → {mapping['target_framework']:15} {mapping['target_control']:10} "
                          f"({mapping['mapping_type']:10}, strength: {mapping['mapping_strength']:.2f})")
                logger.info(f"     {mapping['rationale']}")


def demo_framework_coverage():
    """Demonstrate framework coverage analysis."""
    logger.info("\n" + "=" * 80)
    logger.info("DEMO 2: FRAMEWORK COVERAGE ANALYSIS")
    logger.info("=" * 80)
    
    db_path = Path(__file__).parent.parent / 'data' / 'processed' / 'grc_analytics.db'
    
    with FrameworkMapper(str(db_path)) as mapper:
        # Analyze NIST to ISO coverage
        logger.info("\nNIST 800-53 → ISO 27001 Coverage:")
        logger.info("-" * 80)
        
        coverage = mapper.get_framework_coverage('NIST-800-53', 'ISO-27001')
        
        logger.info(f"Total NIST controls: {coverage['source_total_controls']}")
        logger.info(f"Mapped to ISO:       {coverage['source_mapped_controls']} ({coverage['source_coverage_pct']}%)")
        logger.info(f"\nTotal ISO controls:  {coverage['target_total_controls']}")
        logger.info(f"Covered by NIST:     {coverage['target_mapped_controls']} ({coverage['target_coverage_pct']}%)")
        
        logger.info(f"\nMapping breakdown:")
        for mtype, count in coverage['mapping_types'].items():
            logger.info(f"  {mtype:15} : {count:3} mappings")
        
        # Analyze CIS to NIST coverage
        logger.info("\n\nCIS Controls → NIST 800-53 Coverage:")
        logger.info("-" * 80)
        
        coverage = mapper.get_framework_coverage('CIS', 'NIST-800-53')
        
        logger.info(f"Total CIS controls:  {coverage['source_total_controls']}")
        logger.info(f"Mapped to NIST:      {coverage['source_mapped_controls']} ({coverage['source_coverage_pct']}%)")
        logger.info(f"\nTotal NIST controls: {coverage['target_total_controls']}")
        logger.info(f"Covered by CIS:      {coverage['target_mapped_controls']} ({coverage['target_coverage_pct']}%)")
        
        # Analyze PCI-DSS to NIST coverage
        logger.info("\n\nPCI-DSS → NIST 800-53 Coverage:")
        logger.info("-" * 80)
        
        coverage = mapper.get_framework_coverage('PCI-DSS', 'NIST-800-53')
        
        logger.info(f"Total PCI-DSS requirements: {coverage['source_total_controls']}")
        logger.info(f"Mapped to NIST:             {coverage['source_mapped_controls']} ({coverage['source_coverage_pct']}%)")
        logger.info(f"\nTotal NIST controls:        {coverage['target_total_controls']}")
        logger.info(f"Covered by PCI-DSS:         {coverage['target_mapped_controls']} ({coverage['target_coverage_pct']}%)")


def demo_gap_analysis():
    """Demonstrate gap analysis."""
    logger.info("\n" + "=" * 80)
    logger.info("DEMO 3: GAP ANALYSIS")
    logger.info("=" * 80)
    
    db_path = Path(__file__).parent.parent / 'data' / 'processed' / 'grc_analytics.db'
    
    with FrameworkMapper(str(db_path)) as mapper:
        # Find CIS controls not mapped to NIST
        logger.info("\nCIS Controls without NIST mappings:")
        logger.info("-" * 80)
        
        gaps = mapper.find_gaps('CIS', 'NIST-800-53')
        
        if gaps:
            for gap in gaps[:5]:  # Show first 5
                logger.info(f"  {gap['control_id']:10} | {gap['control_name'][:50]:50} | Priority: {gap['priority']}")
            
            if len(gaps) > 5:
                logger.info(f"  ... and {len(gaps) - 5} more")
        else:
            logger.info("  ✓ All CIS controls are mapped to NIST!")
        
        # Find ISO controls not mapped from NIST
        logger.info("\n\nISO 27001 Controls not covered by NIST mappings:")
        logger.info("-" * 80)
        
        gaps = mapper.find_gaps('ISO-27001', 'NIST-800-53')
        
        if gaps:
            logger.info(f"  Found {len(gaps)} unmapped ISO controls (showing first 10):")
            for gap in gaps[:10]:
                logger.info(f"  {gap['control_id']:10} | {gap['control_name'][:50]:50} | Priority: {gap['priority']}")
            
            if len(gaps) > 10:
                logger.info(f"  ... and {len(gaps) - 10} more")
        else:
            logger.info("  ✓ All ISO controls are covered by NIST mappings!")


def demo_compliance_inheritance():
    """Demonstrate compliance inheritance through mappings."""
    logger.info("\n" + "=" * 80)
    logger.info("DEMO 4: COMPLIANCE INHERITANCE")
    logger.info("=" * 80)
    
    logger.info("\nConcept: If you're compliant with NIST 800-53 controls,")
    logger.info("you can inherit compliance for mapped ISO 27001 controls.")
    logger.info("\nExample:")
    logger.info("-" * 80)
    
    db_path = Path(__file__).parent.parent / 'data' / 'processed' / 'grc_analytics.db'
    
    with FrameworkMapper(str(db_path)) as mapper:
        # Get NIST AC-2 mappings
        mappings = mapper.get_mappings_for_control('NIST-800-53', 'AC-2')
        
        logger.info("\nIf NIST 800-53 AC-2 (Account Management) is COMPLIANT:")
        logger.info("Then the following ISO controls inherit compliance:")
        
        for mapping in mappings:
            if mapping['direction'] == 'outbound' and mapping['target_framework'] == 'ISO-27001':
                inherited_compliance = mapping['mapping_strength'] * 100
                logger.info(f"  → ISO {mapping['target_control']:10} : ~{inherited_compliance:.0f}% compliant "
                          f"(based on {mapping['mapping_type']} mapping)")
                logger.info(f"     {mapping['target_control_name']}")


def demo_multi_framework_compliance():
    """Demonstrate multi-framework compliance tracking."""
    logger.info("\n" + "=" * 80)
    logger.info("DEMO 5: MULTI-FRAMEWORK COMPLIANCE SCENARIO")
    logger.info("=" * 80)
    
    logger.info("\nScenario: Organization needs to comply with:")
    logger.info("  - NIST 800-53 (Federal requirements)")
    logger.info("  - ISO 27001 (International certification)")
    logger.info("  - PCI-DSS (Payment card processing)")
    logger.info("\n" + "-" * 80)
    
    db_path = Path(__file__).parent.parent / 'data' / 'processed' / 'grc_analytics.db'
    
    with FrameworkMapper(str(db_path)) as mapper:
        # Show how PCI-DSS maps through NIST to ISO
        logger.info("\nPCI-DSS Requirement 8 (Identity Management):")
        logger.info("  → Maps to NIST 800-53 IA-2, IA-5")
        logger.info("  → Which map to ISO 27001 A.9.2.1, A.9.2.4")
        logger.info("\nResult: Implementing NIST controls satisfies all three frameworks!")
        
        # Show statistics
        stats = mapper.get_mapping_statistics()
        
        logger.info("\n\nCurrent Mapping Statistics:")
        logger.info(f"  Total mappings: {stats['total_mappings']}")
        logger.info(f"  Average strength: {stats['average_strength']:.3f}")
        logger.info(f"  Framework pairs covered: {len(stats['by_framework_pair'])}")


def demo_use_cases():
    """Show practical use cases."""
    logger.info("\n" + "=" * 80)
    logger.info("DEMO 6: PRACTICAL USE CASES")
    logger.info("=" * 80)
    
    logger.info("\n1. COMPLIANCE PLANNING")
    logger.info("   Use mappings to identify which controls satisfy multiple frameworks")
    logger.info("   → Prioritize controls that give you the most 'bang for your buck'")
    
    logger.info("\n2. GAP ANALYSIS")
    logger.info("   Compare your current framework compliance against target frameworks")
    logger.info("   → See what additional work is needed for new certifications")
    
    logger.info("\n3. AUDIT PREPARATION")
    logger.info("   Show auditors how your existing controls map to their requirements")
    logger.info("   → Reduce redundant documentation and assessments")
    
    logger.info("\n4. RISK ASSESSMENT")
    logger.info("   Use mapping strength to assess coverage confidence")
    logger.info("   → EXACT mappings = high confidence, RELATED = review needed")
    
    logger.info("\n5. CONTINUOUS COMPLIANCE")
    logger.info("   Track compliance across multiple frameworks simultaneously")
    logger.info("   → Single assessment updates multiple framework statuses")


def main():
    """Run all demonstrations."""
    logger.info("=" * 80)
    logger.info("CROSS-FRAMEWORK MAPPING DEMONSTRATION")
    logger.info("=" * 80)
    logger.info("\nShowing how control mappings enable multi-framework compliance...")
    
    try:
        demo_control_mappings()
        demo_framework_coverage()
        demo_gap_analysis()
        demo_compliance_inheritance()
        demo_multi_framework_compliance()
        demo_use_cases()
        
        logger.info("\n" + "=" * 80)
        logger.info("DEMONSTRATION COMPLETE")
        logger.info("=" * 80)
        logger.info("\nKey Takeaways:")
        logger.info("  ✓ 139 cross-framework mappings created")
        logger.info("  ✓ Supports compliance inheritance")
        logger.info("  ✓ Enables gap analysis")
        logger.info("  ✓ Reduces redundant work")
        logger.info("  ✓ Multi-framework tracking ready")
        
        return 0
        
    except Exception as e:
        logger.error(f"\n✗ Error during demonstration: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
