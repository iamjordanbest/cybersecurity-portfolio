#!/usr/bin/env python3
"""
Test Analytics Modules

Comprehensive test of all analytics modules for Project 2.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / 'src'))

from analytics.risk_scoring import RiskScoringEngine
from analytics.trend_analysis import TrendAnalyzer
from analytics.roi_calculator import ROICalculator

DB_PATH = str(project_root / 'data' / 'processed' / 'grc_analytics.db')

def test_risk_scoring():
    """Test RiskScoringEngine."""
    print("\n" + "="*70)
    print("Testing RiskScoringEngine")
    print("="*70)
    
    try:
        with RiskScoringEngine(DB_PATH) as engine:
            # Get risk summary
            summary = engine.get_risk_score_summary()
            print(f"\n[OK] Risk Score Summary:")
            print(f"  Total Controls: {summary['total_controls']}")
            print(f"  Avg Priority Score: {summary['average_priority_score']}")
            print(f"  Critical Risk: {summary['critical_risk_controls']}")
            print(f"  High Risk: {summary['high_risk_controls']}")
            print(f"  Medium Risk: {summary['medium_risk_controls']}")
            print(f"  Low Risk: {summary['low_risk_controls']}")
            
            # Get high risk controls
            high_risk = engine.get_high_risk_controls(threshold=50, limit=5)
            print(f"\n[OK] High Risk Controls (Top 5):")
            for ctrl in high_risk[:5]:
                print(f"  {ctrl['control_id']}: Priority={ctrl['priority_score']:.2f}")
            
        return True
    except Exception as e:
        print(f"\n[FAIL] RiskScoringEngine FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_trend_analysis():
    """Test TrendAnalyzer."""
    print("\n" + "="*70)
    print("Testing TrendAnalyzer")
    print("="*70)
    
    try:
        with TrendAnalyzer(DB_PATH) as analyzer:
            # Get compliance over time
            trend = analyzer.get_compliance_over_time(months_back=6)
            print(f"\n[OK] Compliance Trend (last 6 months): {len(trend)} data points")
            if trend:
                latest = trend[-1]
                print(f"  Latest Month: {latest['month']}")
                print(f"  Compliance: {latest['compliance_percentage']:.1f}%")
            
            # Get velocity
            velocity = analyzer.calculate_compliance_velocity()
            print(f"\n[OK] Compliance Velocity:")
            print(f"  Current: {velocity['current_compliance']:.1f}%")
            print(f"  Velocity: {velocity['velocity_per_month']:.2f}%/month")
            print(f"  Trend: {velocity['trend']}")
            
            # Family trends
            families = analyzer.get_family_trends()
            print(f"\n[OK] Family Trends: {len(families)} families")
            if families:
                print(f"  Sample: {families[0]['family']}")
            
        return True
    except Exception as e:
        print(f"\n[FAIL] TrendAnalyzer FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_roi_calculator():
    """Test ROICalculator."""
    print("\n" + "="*70)
    print("Testing ROICalculator")
    print("="*70)
    
    try:
        with ROICalculator(DB_PATH) as calculator:
            # Generate ROI report
            report = calculator.generate_roi_report()
            print(f"\n[OK] ROI Report Generated:")
            
            hp_invest = report['high_priority_investment']
            print(f"  Portfolio ROI: {hp_invest['portfolio_roi_percentage']:.0f}%")
            print(f"  Total Investment: ${hp_invest['total_remediation_cost']:,.0f}")
            print(f"  Risk Reduction: ${hp_invest['total_risk_reduction']:,.0f}")
            print(f"  Top Controls: {len(hp_invest['top_roi_controls'])}")
            
        return True
    except Exception as e:
        print(f"\n[FAIL] ROICalculator FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests."""
    print("\n" + "="*70)
    print("GRC Analytics - Module Testing")
    print("="*70)
    
    results = {
        'RiskScoringEngine': test_risk_scoring(),
        'TrendAnalyzer': test_trend_analysis(),
        'ROICalculator': test_roi_calculator()
    }
    
    print("\n" + "="*70)
    print("TEST RESULTS")
    print("="*70)
    for module, passed in results.items():
        status = "[OK] PASSED" if passed else "[FAIL] FAILED"
        print(f"{module}: {status}")
    
    all_passed = all(results.values())
    print("\n" + "="*70)
    if all_passed:
        print("ALL TESTS PASSED [OK]")
    else:
        print("SOME TESTS FAILED [X]")
    print("="*70)
    
    return 0 if all_passed else 1

if __name__ == '__main__':
    sys.exit(main())
