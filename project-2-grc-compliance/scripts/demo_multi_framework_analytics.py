#!/usr/bin/env python3
"""
Multi-Framework Analytics Demonstration

Shows the capabilities of multi-framework analytics including:
- Unified compliance tracking
- Cross-framework risk analysis
- Compliance inheritance
- Multi-framework ROI
"""

import sys
from pathlib import Path
import logging

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.analytics.multi_framework_analytics import MultiFrameworkAnalytics

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


def demo_unified_compliance():
    """Demonstrate unified compliance status."""
    logger.info("\n" + "=" * 80)
    logger.info("DEMO 1: UNIFIED COMPLIANCE STATUS")
    logger.info("=" * 80)
    
    db_path = Path(__file__).parent.parent / 'data' / 'processed' / 'grc_analytics.db'
    
    with MultiFrameworkAnalytics(str(db_path)) as analytics:
        compliance = analytics.get_unified_compliance_status()
        
        logger.info("\nCompliance Status Across All Frameworks:")
        logger.info("-" * 80)
        
        for fw_code, status in compliance.items():
            logger.info(f"\n{fw_code} - {status['framework_name']}:")
            logger.info(f"  Total Controls:     {status['total_controls']}")
            logger.info(f"  Compliant:          {status['compliant']} ({status['compliance_percentage']}%)")
            logger.info(f"  Partially Compliant: {status['partial']}")
            logger.info(f"  Non-Compliant:      {status['non_compliant']}")
            logger.info(f"  Not Assessed:       {status['not_assessed']}")
        
        # Overall summary
        total_controls = sum(s['total_controls'] for s in compliance.values())
        total_compliant = sum(s['compliant'] for s in compliance.values())
        overall_pct = (total_compliant / total_controls * 100) if total_controls > 0 else 0
        
        logger.info("\n" + "-" * 80)
        logger.info(f"OVERALL: {total_compliant}/{total_controls} controls compliant ({overall_pct:.2f}%)")


def demo_inherited_compliance():
    """Demonstrate compliance inheritance."""
    logger.info("\n" + "=" * 80)
    logger.info("DEMO 2: COMPLIANCE INHERITANCE")
    logger.info("=" * 80)
    
    db_path = Path(__file__).parent.parent / 'data' / 'processed' / 'grc_analytics.db'
    
    with MultiFrameworkAnalytics(str(db_path)) as analytics:
        logger.info("\nISO 27001 Controls with Inherited Compliance from NIST:")
        logger.info("-" * 80)
        
        inherited = analytics.calculate_inherited_compliance('ISO-27001')
        
        if inherited:
            count = 0
            for control_id, sources in inherited.items():
                if count < 10:  # Show first 10
                    logger.info(f"\nISO {control_id}:")
                    for source in sources:
                        inherited_pct = source['inherited_compliance']
                        logger.info(f"  ← {source['source_framework']} {source['source_control']} "
                                  f"({source['mapping_type']}, ~{inherited_pct:.0f}% inherited)")
                    count += 1
            
            if len(inherited) > 10:
                logger.info(f"\n... and {len(inherited) - 10} more controls with inherited compliance")
            
            logger.info(f"\n✓ Total ISO controls with inherited compliance: {len(inherited)}")
        else:
            logger.info("  No inherited compliance found (NIST controls need assessments)")


def demo_risk_summary():
    """Demonstrate multi-framework risk summary."""
    logger.info("\n" + "=" * 80)
    logger.info("DEMO 3: MULTI-FRAMEWORK RISK SUMMARY")
    logger.info("=" * 80)
    
    db_path = Path(__file__).parent.parent / 'data' / 'processed' / 'grc_analytics.db'
    
    with MultiFrameworkAnalytics(str(db_path)) as analytics:
        risk = analytics.get_multi_framework_risk_summary()
        
        logger.info("\nRisk Distribution by Framework:")
        logger.info("-" * 80)
        
        for fw_code, metrics in risk.items():
            if metrics['total_scored'] > 0:
                logger.info(f"\n{fw_code}:")
                logger.info(f"  Scored Controls:      {metrics['total_scored']}")
                logger.info(f"  Avg Priority Score:   {metrics['avg_priority_score']:.2f}")
                logger.info(f"  Critical Risk:        {metrics['critical_risk']} controls")
                logger.info(f"  High Risk:            {metrics['high_risk']} controls")
                logger.info(f"  Medium Risk:          {metrics['medium_risk']} controls")
                logger.info(f"  Low Risk:             {metrics['low_risk']} controls")
                if metrics['total_kevs'] > 0:
                    logger.info(f"  CISA KEVs:            {metrics['total_kevs']}")
                if metrics['total_attack_techniques'] > 0:
                    logger.info(f"  ATT&CK Techniques:    {metrics['total_attack_techniques']}")
            else:
                logger.info(f"\n{fw_code}: No risk scores calculated yet")


def demo_framework_comparison():
    """Demonstrate framework comparison."""
    logger.info("\n" + "=" * 80)
    logger.info("DEMO 4: FRAMEWORK COMPARISON")
    logger.info("=" * 80)
    
    db_path = Path(__file__).parent.parent / 'data' / 'processed' / 'grc_analytics.db'
    
    with MultiFrameworkAnalytics(str(db_path)) as analytics:
        frameworks = ['NIST-800-53', 'ISO-27001', 'CIS']
        comparison = analytics.get_framework_comparison(frameworks)
        
        logger.info(f"\nComparing: {', '.join(frameworks)}")
        logger.info("-" * 80)
        
        # Compliance comparison
        logger.info("\nCompliance Rates:")
        for fw in frameworks:
            if fw in comparison['metrics']:
                comp = comparison['metrics'][fw].get('compliance', {})
                if comp:
                    pct = comp.get('compliance_percentage', 0)
                    logger.info(f"  {fw:15} : {pct:6.2f}% compliant")
        
        # Coverage between frameworks
        logger.info("\nCross-Framework Coverage:")
        for key, value in comparison['metrics'].items():
            if value.get('type') == 'coverage':
                parts = key.split('_to_')
                if len(parts) == 2:
                    logger.info(f"  {parts[0]:15} → {parts[1]:15} : {value['source_coverage']:.2f}% coverage")


def demo_priority_controls():
    """Demonstrate priority controls across frameworks."""
    logger.info("\n" + "=" * 80)
    logger.info("DEMO 5: HIGH-PRIORITY CONTROLS ACROSS FRAMEWORKS")
    logger.info("=" * 80)
    
    db_path = Path(__file__).parent.parent / 'data' / 'processed' / 'grc_analytics.db'
    
    with MultiFrameworkAnalytics(str(db_path)) as analytics:
        priorities = analytics.get_priority_controls_across_frameworks(
            min_priority=50.0,
            limit=15
        )
        
        if priorities:
            logger.info(f"\nTop 15 Highest Priority Controls (across all frameworks):")
            logger.info("-" * 80)
            
            for ctrl in priorities:
                logger.info(f"\n{ctrl['framework']} {ctrl['control_id']} (Score: {ctrl['priority_score']:.2f})")
                logger.info(f"  {ctrl['control_name'][:70]}")
                logger.info(f"  Category: {ctrl['category']} | Status: {ctrl['compliance_status']} | "
                          f"Risk: {ctrl['risk_rating']}")
                if ctrl['kev_count'] > 0:
                    logger.info(f"  ⚠ {ctrl['kev_count']} CISA KEVs, {ctrl['attack_techniques']} ATT&CK techniques")
        else:
            logger.info("\nNo priority controls found (risk scores need to be calculated)")


def demo_multi_framework_roi():
    """Demonstrate multi-framework ROI calculation."""
    logger.info("\n" + "=" * 80)
    logger.info("DEMO 6: MULTI-FRAMEWORK ROI ANALYSIS")
    logger.info("=" * 80)
    
    db_path = Path(__file__).parent.parent / 'data' / 'processed' / 'grc_analytics.db'
    
    with MultiFrameworkAnalytics(str(db_path)) as analytics:
        frameworks = ['NIST-800-53', 'ISO-27001', 'PCI-DSS']
        roi = analytics.calculate_multi_framework_roi(frameworks)
        
        logger.info(f"\nROI Analysis for implementing: {', '.join(frameworks)}")
        logger.info("-" * 80)
        
        logger.info("\nIndividual Framework Costs (if implemented separately):")
        for fw, data in roi['individual_costs'].items():
            logger.info(f"  {fw:15} : {data['controls']:4} controls × $1,000 = ${data['cost']:,}")
        
        logger.info(f"\nTotal Individual Cost: ${roi['total_individual_cost']:,}")
        logger.info(f"Combined Cost (with synergies): ${roi['combined_cost']:,}")
        logger.info(f"Savings: ${roi['savings']:,}")
        logger.info(f"ROI: {roi['roi_percentage']:.2f}%")
        
        logger.info("\nSavings come from:")
        logger.info("  • Shared control assessments (mapping overlap)")
        logger.info("  • Reusable documentation")
        logger.info("  • Unified compliance tracking")
        logger.info("  • Reduced redundant work")


def demo_compliance_gaps():
    """Demonstrate compliance gap analysis."""
    logger.info("\n" + "=" * 80)
    logger.info("DEMO 7: COMPLIANCE GAP ANALYSIS")
    logger.info("=" * 80)
    
    db_path = Path(__file__).parent.parent / 'data' / 'processed' / 'grc_analytics.db'
    
    with MultiFrameworkAnalytics(str(db_path)) as analytics:
        gaps = analytics.get_compliance_gaps_across_frameworks()
        
        logger.info("\nHigh-Priority Gaps by Framework:")
        logger.info("-" * 80)
        
        for fw, gap_data in gaps.items():
            total = gap_data['total_gaps']
            if total > 0:
                logger.info(f"\n{fw}: {total} critical/high priority gaps")
                
                for gap in gap_data['gaps'][:5]:  # Show first 5
                    logger.info(f"  {gap['control_id']:10} | {gap['priority']:8} | "
                              f"{gap['status']:20} | {gap['control_name'][:40]}")
                
                if total > 5:
                    logger.info(f"  ... and {total - 5} more gaps")
            else:
                logger.info(f"\n{fw}: ✓ No critical/high priority gaps")


def demo_use_cases():
    """Show practical use cases."""
    logger.info("\n" + "=" * 80)
    logger.info("DEMO 8: PRACTICAL USE CASES")
    logger.info("=" * 80)
    
    logger.info("\n1. COMPLIANCE DASHBOARD")
    logger.info("   Track compliance across all frameworks in a single view")
    logger.info("   → See overall compliance percentage")
    logger.info("   → Identify frameworks needing attention")
    
    logger.info("\n2. RISK PRIORITIZATION")
    logger.info("   Identify highest-risk controls across all frameworks")
    logger.info("   → Focus remediation efforts on critical gaps")
    logger.info("   → See which frameworks have the most risk")
    
    logger.info("\n3. COMPLIANCE PLANNING")
    logger.info("   Use inherited compliance to reduce workload")
    logger.info("   → If NIST control is compliant, ISO inherits status")
    logger.info("   → Calculate actual work needed for new frameworks")
    
    logger.info("\n4. EXECUTIVE REPORTING")
    logger.info("   Generate unified compliance reports")
    logger.info("   → Show compliance across all frameworks")
    logger.info("   → Demonstrate ROI of multi-framework approach")
    
    logger.info("\n5. AUDIT PREPARATION")
    logger.info("   Prepare for multiple audits simultaneously")
    logger.info("   → Use cross-framework mappings")
    logger.info("   → Show compliance inheritance")
    logger.info("   → Reduce duplicate assessments")


def main():
    """Run all demonstrations."""
    logger.info("=" * 80)
    logger.info("MULTI-FRAMEWORK ANALYTICS DEMONSTRATION")
    logger.info("=" * 80)
    logger.info("\nShowing unified analytics across all compliance frameworks...")
    
    try:
        demo_unified_compliance()
        demo_inherited_compliance()
        demo_risk_summary()
        demo_framework_comparison()
        demo_priority_controls()
        demo_multi_framework_roi()
        demo_compliance_gaps()
        demo_use_cases()
        
        logger.info("\n" + "=" * 80)
        logger.info("DEMONSTRATION COMPLETE")
        logger.info("=" * 80)
        logger.info("\nKey Capabilities Demonstrated:")
        logger.info("  ✓ Unified compliance tracking across 5 frameworks")
        logger.info("  ✓ Compliance inheritance through mappings")
        logger.info("  ✓ Multi-framework risk analysis")
        logger.info("  ✓ Framework comparison and coverage")
        logger.info("  ✓ Priority control identification")
        logger.info("  ✓ ROI calculation with synergies")
        logger.info("  ✓ Gap analysis across frameworks")
        
        return 0
        
    except Exception as e:
        logger.error(f"\n✗ Error during demonstration: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
