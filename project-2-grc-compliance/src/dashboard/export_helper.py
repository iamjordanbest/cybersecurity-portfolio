#!/usr/bin/env python3
"""
Simple export helper for GRC dashboard.

Provides CSV and simple text-based "PDF" exports for dashboard data.
"""

import pandas as pd
from datetime import datetime


def export_high_risk_controls_csv(df):
    """Export high-risk controls to CSV format."""
    if df.empty:
        return "control_id,control_name,priority_score\n# No high-risk controls found\n".encode('utf-8')
    
    # Select key columns
    export_df = df[['control_id', 'control_name', 'priority_score', 
                    'compliance_status', 'kev_cve_count', 'attack_technique_count']].copy()
    
    return export_df.to_csv(index=False).encode('utf-8')


def export_high_risk_controls_txt(df):
    """Export high-risk controls to text format (simpler than PDF)."""
    output = []
    output.append("=" * 80)
    output.append("GRC ANALYTICS - HIGH-RISK CONTROLS REPORT")
    output.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    output.append("=" * 80)
    output.append("")
    
    if df.empty:
        output.append("No high-risk controls identified.")
    else:
        output.append(f"Total High-Risk Controls: {len(df)}")
        output.append("")
        output.append("-" * 80)
        
        for idx, row in df.iterrows():
            output.append(f"\nControl ID: {row['control_id']}")
            output.append(f"Name: {row['control_name']}")
            output.append(f"Priority Score: {row['priority_score']:.2f}")
            output.append(f"Status: {row['compliance_status']}")
            output.append(f"KEV CVEs: {row.get('kev_cve_count', 0)}")
            output.append(f"MITRE ATT&CK: {row.get('attack_technique_count', 0)}")
            output.append("-" * 80)
    
    output.append("")
    output.append("End of Report")
    output.append("=" * 80)
    
    return "\n".join(output).encode('utf-8')
