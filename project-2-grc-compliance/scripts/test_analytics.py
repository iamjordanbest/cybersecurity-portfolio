#!/usr/bin/env python3
"""
Test Analytics Modules

Tests the risk scoring, trend analysis, and ROI calculation modules.
"""

import sys
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / 'src'))

from analytics.risk_scoring import RiskScoringEngine
from analytics.trend_analysis import TrendAnalyzer
from analytics.roi_calculator import ROICalculator
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def test_risk_scoring():
    """Test risk scoring engine."""
    logger.info("\n" + "=" * 70)
    logger.info("TESTING RISK SCORING ENGINE")
    logger.info("=" * 70)
    
    db_path = project_root / 'data' / 'processed' / 'grc_analytics.db'
    
    with RiskScoringEngine(str(db_path)) as engine:
        # Test single control risk score
        logger.info("\n1. Testing single control risk calculation...")
        score = engine.calculate_control_risk_score('AC-1')
        logger.info(f"   Control: {score['control_id']} - {score['control_name']}")
        logger.info(f"   Base Risk: {score['base_risk_score']}")
        logger.info(f"   Threat Adjusted: {score['threat_adjusted_score']}")
        logger.info(f"   Priority Score: {score['priority_score']}")
        logger.info(f"   KEV CVEs: {score['kev_cve_count']}, ATT&CK: {score['attack_technique_count']}")
        
        # Get high-risk controls
        logger.info("\n2. Getting high-risk controls...")
        high_risk = engine.get_high_risk_controls(threshold=50, limit=5)
        logger.info(f"   Found {len(high_risk)} high-risk controls:")
        for ctrl in high_risk[:5]:
            logger.info(f"   - {ctrl['control_id']}: Priority={ctrl['priority_score']:.2f}, "
                       f"KEV={ctrl['kev_cve_count']}, Status={ctrl['compliance_status']}")
        
        # Get summary
        logger.info("\n3. Risk score summary...")
        summary = engine.get_risk_score_summary()
        logger.info(f"   Total Controls: {summary['total_controls']}")
        logger.info(f"   Avg Priority: {summary['average_priority_score']:.2f}")
        logger.info(f"   Critical: {summary['critical_risk_controls']}")
        logger.info(f"   High: {summary['high_risk_controls']}")
        logger.info(f"   Medium: {summary['medium_risk_controls']}")
        logger.info(f"   Low: {summary['low_risk_controls']}")


def test_trend_analysis():
    """Test trend analysis module."""
    logger.info("\n" + "=" * 70)
    logger.info("TESTING TREND ANALYSIS")
    logger.info("=" * 70)
    
    db_path = project_root / 'data' / 'processed' / 'grc_analytics.db'
    
    with TrendAnalyzer(str(db_path)) as analyzer:
        # Compliance over time
        logger.info("\n1. Compliance over time...")
        compliance_data = analyzer.get_compliance_over_time(months_back=6)
        logger.info(f"   Data points: {len(compliance_data)}")
        if compliance_data:
            logger.info(f"   First month: {compliance_data[0]['month']} - {compliance_data[0]['compliance_percentage']:.2f}%")
            logger.info(f"   Latest month: {compliance_data[-1]['month']} - {compliance_data[-1]['compliance_percentage']:.2f}%")
        
        # Compliance velocity
        logger.info("\n2. Compliance velocity...")
        velocity = analyzer.calculate_compliance_velocity()
        logger.info(f"   Current: {velocity['current_compliance']:.2f}%")
        logger.info(f"   Velocity: {velocity['velocity_per_month']:.2f}% per month")
        logger.info(f"   Trend: {velocity['trend']}")
        logger.info(f"   Projected (3mo): {velocity['projected_3_months']:.2f}%")
        if velocity['months_to_95_percent']:
            logger.info(f"   Months to 95%: {velocity['months_to_95_percent']:.1f}")
        
        # Family trends
        logger.info("\n3. Control family trends (lowest compliance)...")
        family_trends = analyzer.get_family_trends()
        for family in family_trends[:5]:
            logger.info(f"   {family['family']}: {family['current_compliance']:.2f}% "
                       f"(velocity: {family['velocity']:.2f}% per month)")
        
        # Control aging
        logger.info("\n4. Control aging analysis...")
        aging = analyzer.get_control_aging_analysis()
        dist = aging['age_distribution']
        logger.info(f"   Current (<90 days): {dist['current']}")
        logger.info(f"   Aging (90-180 days): {dist['aging']}")
        logger.info(f"   Stale (180-365 days): {dist['stale']}")
        logger.info(f"   Very Stale (>365 days): {dist['very_stale']}")
        
        # Remediation velocity
        logger.info("\n5. Remediation velocity...")
        remediation = analyzer.get_remediation_velocity()
        logger.info(f"   Total Actions: {remediation['total_actions']}")
        logger.info(f"   Completed: {remediation['completed']}")
        logger.info(f"   In Progress: {remediation['in_progress']}")
        logger.info(f"   Overdue: {remediation['overdue']}")
        logger.info(f"   Completion Rate: {remediation['completion_rate']:.2f}%")


def test_roi_calculator():
    """Test ROI calculator module."""
    logger.info("\n" + "=" * 70)
    logger.info("TESTING ROI CALCULATOR")
    logger.info("=" * 70)
    
    db_path = project_root / 'data' / 'processed' / 'grc_analytics.db'
    
    with ROICalculator(str(db_path)) as calculator:
        # Test single control ROI
        logger.info("\n1. Testing single control ROI...")
        
        # Find a non-compliant control
        import sqlite3
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute('''
            SELECT control_id FROM compliance_assessments
            WHERE compliance_status = 'non_compliant'
            LIMIT 1
        ''')
        control = cursor.fetchone()
        conn.close()
        
        if control:
            control_id = control['control_id']
            roi = calculator.calculate_control_roi(control_id)
            
            if 'error' not in roi and 'status' not in roi:
                logger.info(f"   Control: {roi['control_id']} - {roi['control_name']}")
                logger.info(f"   Remediation Cost: ${roi['remediation_cost']:,.0f}")
                logger.info(f"   Annual Risk Reduction: ${roi['risk_reduction_annual']:,.0f}")
                logger.info(f"   Total Risk Reduction (3yr): ${roi['risk_reduction_total']:,.0f}")
                logger.info(f"   Net Present Value: ${roi['net_present_value']:,.0f}")
                logger.info(f"   ROI: {roi['roi_percentage']:.2f}%")
                if roi['payback_period_months']:
                    logger.info(f"   Payback Period: {roi['payback_period_months']:.1f} months")
            else:
                logger.info(f"   Status: {roi.get('status', roi.get('error'))}")
        
        # Portfolio ROI
        logger.info("\n2. Portfolio ROI (top 10 high-priority controls)...")
        portfolio = calculator.calculate_portfolio_roi(
            control_ids=None,  # Will use non-compliant controls
            industry='technology'
        )
        
        logger.info(f"   Total Controls: {portfolio['total_controls']}")
        logger.info(f"   Total Investment: ${portfolio['total_remediation_cost']:,.0f}")
        logger.info(f"   Total Risk Reduction: ${portfolio['total_risk_reduction']:,.0f}")
        logger.info(f"   Net Present Value: ${portfolio['total_net_present_value']:,.0f}")
        logger.info(f"   Portfolio ROI: {portfolio['portfolio_roi_percentage']:.2f}%")
        
        logger.info("\n   Top 5 controls by ROI:")
        for ctrl in portfolio['top_roi_controls'][:5]:
            logger.info(f"   - {ctrl['control_id']}: ROI={ctrl['roi_percentage']:.2f}%, "
                       f"Cost=${ctrl['remediation_cost']:,.0f}")


def main():
    """Run all tests."""
    logger.info("=" * 70)
    logger.info("GRC ANALYTICS PLATFORM - MODULE TESTING")
    logger.info("=" * 70)
    
    try:
        test_risk_scoring()
        test_trend_analysis()
        test_roi_calculator()
        
        logger.info("\n" + "=" * 70)
        logger.info("✅ ALL TESTS COMPLETED SUCCESSFULLY")
        logger.info("=" * 70)
        
    except Exception as e:
        logger.error(f"\n❌ TEST FAILED: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
