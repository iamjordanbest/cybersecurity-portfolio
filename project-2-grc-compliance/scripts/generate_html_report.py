#!/usr/bin/env python3
"""
Generate HTML Report

Creates a static HTML report with all analytics data.
"""

import sys
from pathlib import Path
import json
from datetime import datetime

# Add src to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / 'src'))

from analytics.risk_scoring import RiskScoringEngine
from analytics.trend_analysis import TrendAnalyzer
from analytics.roi_calculator import ROICalculator

DB_PATH = str(project_root / 'data' / 'processed' / 'grc_analytics.db')


def generate_html_report():
    """Generate comprehensive HTML report."""
    
    print("Generating HTML report...")
    
    # Load data
    with RiskScoringEngine(DB_PATH) as engine:
        risk_summary = engine.get_risk_score_summary()
        high_risk_controls = engine.get_high_risk_controls(threshold=50, limit=20)
    
    with TrendAnalyzer(DB_PATH) as analyzer:
        compliance_trend = analyzer.get_compliance_over_time(months_back=6)
        velocity = analyzer.calculate_compliance_velocity()
        family_trends = analyzer.get_family_trends()
        remediation = analyzer.get_remediation_velocity()
    
    with ROICalculator(DB_PATH) as calculator:
        roi_report = calculator.generate_roi_report()
    
    # Create HTML
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>GRC Analytics Report - {datetime.now().strftime('%Y-%m-%d')}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background-color: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #1f77b4;
            border-bottom: 3px solid #1f77b4;
            padding-bottom: 10px;
        }}
        h2 {{
            color: #333;
            margin-top: 30px;
            border-bottom: 2px solid #eee;
            padding-bottom: 5px;
        }}
        .metrics {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }}
        .metric-card {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        .metric-value {{
            font-size: 2.5em;
            font-weight: bold;
            margin: 10px 0;
        }}
        .metric-label {{
            font-size: 0.9em;
            opacity: 0.9;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        th {{
            background-color: #1f77b4;
            color: white;
            padding: 12px;
            text-align: left;
        }}
        td {{
            padding: 10px;
            border-bottom: 1px solid #ddd;
        }}
        tr:hover {{
            background-color: #f5f5f5;
        }}
        .risk-critical {{ background-color: #ffcccc; }}
        .risk-high {{ background-color: #ffe6cc; }}
        .risk-medium {{ background-color: #ffffcc; }}
        .risk-low {{ background-color: #ccffcc; }}
        .status-compliant {{ color: #2ca02c; font-weight: bold; }}
        .status-partial {{ color: #ff7f0e; font-weight: bold; }}
        .status-non-compliant {{ color: #d62728; font-weight: bold; }}
        .trend-improving {{ color: #2ca02c; }}
        .trend-stable {{ color: #ff7f0e; }}
        .trend-degrading {{ color: #d62728; }}
        .footer {{
            margin-top: 40px;
            padding-top: 20px;
            border-top: 2px solid #eee;
            text-align: center;
            color: #666;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🛡️ GRC Analytics Platform - Executive Report</h1>
        <p><strong>Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        
        <h2>📊 Executive Summary</h2>
        <div class="metrics">
            <div class="metric-card">
                <div class="metric-label">Current Compliance</div>
                <div class="metric-value">{velocity['current_compliance']:.1f}%</div>
                <div class="metric-label">Velocity: {velocity['velocity_per_month']:.2f}% per month</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">High-Risk Controls</div>
                <div class="metric-value">{risk_summary['high_risk_controls'] + risk_summary['critical_risk_controls']}</div>
                <div class="metric-label">Requiring Attention</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Remediation Progress</div>
                <div class="metric-value">{remediation['completion_rate']:.1f}%</div>
                <div class="metric-label">{remediation['in_progress']} in progress</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Portfolio ROI</div>
                <div class="metric-value">{roi_report['high_priority_investment']['portfolio_roi_percentage']:.0f}%</div>
                <div class="metric-label">3-year projection</div>
            </div>
        </div>
        
        <h2>⚠️ High-Risk Controls (Top 10)</h2>
        <table>
            <thead>
                <tr>
                    <th>Control ID</th>
                    <th>Control Name</th>
                    <th>Priority Score</th>
                    <th>KEV CVEs</th>
                    <th>ATT&CK Techniques</th>
                    <th>Status</th>
                </tr>
            </thead>
            <tbody>
"""
    
    for ctrl in high_risk_controls[:10]:
        priority_class = 'risk-critical' if ctrl['priority_score'] >= 75 else 'risk-high'
        status_class = f"status-{ctrl['compliance_status'].replace('_', '-')}"
        html += f"""
                <tr class="{priority_class}">
                    <td>{ctrl['control_id']}</td>
                    <td>{ctrl['control_name']}</td>
                    <td>{ctrl['priority_score']:.2f}</td>
                    <td>{ctrl['kev_cve_count']}</td>
                    <td>{ctrl['attack_technique_count']}</td>
                    <td class="{status_class}">{ctrl['compliance_status'].replace('_', ' ').title()}</td>
                </tr>
"""
    
    html += """
            </tbody>
        </table>
        
        <h2>📈 Compliance Trends</h2>
        <table>
            <thead>
                <tr>
                    <th>Month</th>
                    <th>Compliance %</th>
                    <th>Compliant</th>
                    <th>Partial</th>
                    <th>Non-Compliant</th>
                </tr>
            </thead>
            <tbody>
"""
    
    for month_data in compliance_trend:
        html += f"""
                <tr>
                    <td>{month_data['month']}</td>
                    <td><strong>{month_data['compliance_percentage']:.2f}%</strong></td>
                    <td class="status-compliant">{month_data['compliant']}</td>
                    <td class="status-partial">{month_data['partial']}</td>
                    <td class="status-non-compliant">{month_data['non_compliant']}</td>
                </tr>
"""
    
    html += f"""
            </tbody>
        </table>
        
        <h2>📊 Control Family Performance</h2>
        <table>
            <thead>
                <tr>
                    <th>Family</th>
                    <th>Current Compliance</th>
                    <th>Trend</th>
                    <th>Velocity (per month)</th>
                </tr>
            </thead>
            <tbody>
"""
    
    for family in family_trends[:10]:
        trend_class = f"trend-{family['trend']}"
        html += f"""
                <tr>
                    <td>{family['family']}</td>
                    <td><strong>{family['current_compliance']:.2f}%</strong></td>
                    <td class="{trend_class}">{family['trend'].title()}</td>
                    <td>{family['velocity']:.2f}%</td>
                </tr>
"""
    
    html += f"""
            </tbody>
        </table>
        
        <h2>💰 ROI Analysis - Top Investment Opportunities</h2>
        <p><strong>High-Priority Portfolio Investment:</strong> ${roi_report['high_priority_investment']['total_remediation_cost']:,.0f}</p>
        <p><strong>Total Risk Reduction (3 years):</strong> ${roi_report['high_priority_investment']['total_risk_reduction']:,.0f}</p>
        <p><strong>Net Present Value:</strong> ${roi_report['high_priority_investment']['total_net_present_value']:,.0f}</p>
        
        <table>
            <thead>
                <tr>
                    <th>Control ID</th>
                    <th>Control Name</th>
                    <th>Cost</th>
                    <th>Risk Reduction</th>
                    <th>ROI %</th>
                    <th>Payback (Months)</th>
                </tr>
            </thead>
            <tbody>
"""
    
    for ctrl in roi_report['high_priority_investment']['top_roi_controls'][:10]:
        payback = f"{ctrl['payback_period_months']:.1f}" if ctrl['payback_period_months'] is not None else 'N/A'
        html += f"""
                <tr>
                    <td>{ctrl['control_id']}</td>
                    <td>{ctrl['control_name']}</td>
                    <td>${ctrl['remediation_cost']:,.0f}</td>
                    <td>${ctrl['risk_reduction_total']:,.0f}</td>
                    <td><strong>{ctrl['roi_percentage']:.1f}%</strong></td>
                    <td>{payback}</td>
                </tr>
"""
    
    html += f"""
            </tbody>
        </table>
        
        <h2>🎯 Recommendations</h2>
        <div style="background-color: #e8f4f8; padding: 20px; border-radius: 8px; margin: 20px 0;">
            <h3 style="margin-top: 0;">{roi_report['recommendation']['priority'].replace('_', ' ').title()}</h3>
            <p>{roi_report['recommendation']['rationale']}</p>
            <ul>
                <li><strong>High-Priority Efficiency:</strong> {roi_report['recommendation']['high_priority_efficiency']:.2f}</li>
                <li><strong>Full Portfolio Efficiency:</strong> {roi_report['recommendation']['full_portfolio_efficiency']:.2f}</li>
                <li><strong>Total Controls Analyzed:</strong> {risk_summary['total_controls']}</li>
                <li><strong>Remediation Actions:</strong> {remediation['total_actions']} ({remediation['completion_rate']:.1f}% complete)</li>
            </ul>
        </div>
        
        <div class="footer">
            <p><strong>GRC Analytics Platform</strong> | Powered by NIST 800-53, CISA KEV, MITRE ATT&CK</p>
            <p>For interactive dashboard, run: <code>streamlit run src/dashboard/app.py</code></p>
        </div>
    </div>
</body>
</html>
"""
    
    # Save report
    report_path = project_root / 'outputs' / 'reports' / f'grc_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.html'
    report_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"\n✅ HTML report generated: {report_path}")
    print(f"\nOpen the report in your browser:")
    print(f"  {report_path.absolute()}")
    
    return report_path


if __name__ == '__main__':
    generate_html_report()
