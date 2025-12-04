#!/usr/bin/env python3
"""
Data Export Module for Cloud Security Posture Management (CSPM) Auditor

This module exports compliance assessment data from the SQLite database 
to CSV files optimized for programmatic dashboard creation (Grafana).

Features:
- Clean CSV exports without visualization-specific formatting
- Standardized data structure for dashboard consumption
- Efficient queries for real-time dashboard updates
- Flexible output formats for various dashboard tools

Author: Jordan Best
Date: December 2024
"""

import sys
import os
import sqlite3
import pandas as pd
import json
from datetime import datetime
from pathlib import Path

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class CSPMDataExporter:
    """
    Export CSPM audit data to CSV files for dashboard consumption.
    """
    
    def __init__(self, db_path="data/cspm.db", output_dir="exports"):
        """
        Initialize the data exporter.
        
        Args:
            db_path: Path to SQLite database
            output_dir: Directory for CSV exports
        """
        self.db_path = db_path
        self.output_dir = output_dir
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Create output directory
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
    def export_all_data(self):
        """Export all data sets for dashboard creation."""
        print(f"🔄 Exporting CSMP audit data to {self.output_dir}/")
        
        try:
            # Core assessment data
            self.export_compliance_summary()
            self.export_control_details()
            self.export_compliance_trends()
            
            # Additional analytical data
            self.export_findings_summary()
            self.export_category_breakdown()
            self.export_severity_distribution()
            
            # Metadata for dashboard configuration
            self.export_metadata()
            
            print(f"✅ Data export completed successfully")
            print(f"📁 Files saved to: {self.output_dir}/")
            
        except Exception as e:
            print(f"❌ Export failed: {e}")
            raise
    
    def export_compliance_summary(self):
        """Export high-level compliance metrics over time."""
        query = """
        SELECT 
            a.id as assessment_id,
            a.timestamp,
            a.account_id,
            a.total_controls,
            a.passed_controls,
            a.failed_controls,
            a.score,
            ROUND(a.score, 2) as score_rounded,
            CASE 
                WHEN a.score >= 90 THEN 'Excellent'
                WHEN a.score >= 80 THEN 'Good'
                WHEN a.score >= 70 THEN 'Fair'
                ELSE 'Poor'
            END as compliance_rating,
            date(a.timestamp) as assessment_date,
            time(a.timestamp) as assessment_time
        FROM assessments a
        ORDER BY a.timestamp DESC
        """
        
        df = self._execute_query(query)
        filename = f"{self.output_dir}/compliance_summary.csv"
        df.to_csv(filename, index=False)
        print(f"📊 Exported compliance summary: {len(df)} assessments")
    
    def export_control_details(self):
        """Export detailed control results for the latest assessment."""
        # Get latest assessment ID
        conn = sqlite3.connect(self.db_path)
        latest_result = conn.execute(
            "SELECT id FROM assessments ORDER BY timestamp DESC LIMIT 1"
        ).fetchone()
        
        if not latest_result:
            print("⚠️  No assessments found in database")
            conn.close()
            return
            
        latest_id = latest_result[0]
        
        query = f"""
        SELECT 
            r.assessment_id,
            r.control_id,
            r.status,
            r.findings,
            r.timestamp as last_checked,
            CASE 
                WHEN r.status = 'PASS' THEN 1 
                ELSE 0 
            END as is_compliant,
            CASE 
                WHEN r.status = 'PASS' THEN 100 
                ELSE 0 
            END as score
        FROM assessment_results r
        WHERE r.assessment_id = {latest_id}
        ORDER BY r.control_id
        """
        
        df = self._execute_query(query)
        
        # Add control metadata (since we don't have controls table populated)
        df['title'] = df['control_id']  # Use control_id as title for now
        df['category'] = df['control_id'].str.extract(r'(CIS-\d+)')[0]  # Extract CIS category
        df['severity'] = 'HIGH'  # Default severity
        
        filename = f"{self.output_dir}/control_details.csv"
        df.to_csv(filename, index=False)
        print(f"🔍 Exported control details: {len(df)} controls")
        conn.close()
    
    def export_compliance_trends(self):
        """Export daily compliance trends for time-series visualization."""
        query = """
        SELECT 
            date(timestamp) as date,
            AVG(score) as avg_score,
            MAX(score) as max_score,
            MIN(score) as min_score,
            COUNT(*) as assessments_count,
            AVG(passed_controls) as avg_passed,
            AVG(failed_controls) as avg_failed,
            strftime('%Y-%m', timestamp) as year_month,
            strftime('%w', timestamp) as day_of_week,
            strftime('%Y', timestamp) as year
        FROM assessments
        GROUP BY date(timestamp)
        ORDER BY date(timestamp)
        """
        
        df = self._execute_query(query)
        filename = f"{self.output_dir}/compliance_trends.csv"
        df.to_csv(filename, index=False)
        print(f"📈 Exported compliance trends: {len(df)} time periods")
    
    def export_findings_summary(self):
        """Export aggregated findings data for dashboard insights."""
        conn = sqlite3.connect(self.db_path)
        
        # Get latest assessment ID
        latest_result = conn.execute(
            "SELECT id FROM assessments ORDER BY timestamp DESC LIMIT 1"
        ).fetchone()
        
        if not latest_result:
            conn.close()
            return
            
        latest_id = latest_result[0]
        
        query = f"""
        SELECT 
            SUBSTR(r.control_id, 1, 5) as category,
            'HIGH' as severity,
            COUNT(*) as total_controls,
            SUM(CASE WHEN r.status = 'PASS' THEN 1 ELSE 0 END) as passed_controls,
            SUM(CASE WHEN r.status = 'FAIL' THEN 1 ELSE 0 END) as failed_controls,
            ROUND(
                (SUM(CASE WHEN r.status = 'PASS' THEN 1 ELSE 0 END) * 100.0) / COUNT(*), 
                2
            ) as pass_rate
        FROM assessment_results r
        WHERE r.assessment_id = {latest_id}
        GROUP BY SUBSTR(r.control_id, 1, 5)
        ORDER BY category
        """
        
        df = self._execute_query(query)
        df['severity_clean'] = df['severity'].str.replace('Severity.', '', regex=False)
        
        filename = f"{self.output_dir}/findings_summary.csv"
        df.to_csv(filename, index=False)
        print(f"📋 Exported findings summary: {len(df)} category/severity combinations")
        conn.close()
    
    def export_category_breakdown(self):
        """Export category-level compliance breakdown."""
        conn = sqlite3.connect(self.db_path)
        
        # Get latest assessment ID
        latest_result = conn.execute(
            "SELECT id FROM assessments ORDER BY timestamp DESC LIMIT 1"
        ).fetchone()
        
        if not latest_result:
            conn.close()
            return
            
        latest_id = latest_result[0]
        
        query = f"""
        SELECT 
            SUBSTR(r.control_id, 1, 5) as category,
            COUNT(*) as total_controls,
            SUM(CASE WHEN r.status = 'PASS' THEN 1 ELSE 0 END) as passed_controls,
            SUM(CASE WHEN r.status = 'FAIL' THEN 1 ELSE 0 END) as failed_controls,
            ROUND(AVG(CASE WHEN r.status = 'PASS' THEN 100 ELSE 0 END), 2) as avg_score,
            ROUND(
                (SUM(CASE WHEN r.status = 'PASS' THEN 1 ELSE 0 END) * 100.0) / COUNT(*), 
                2
            ) as compliance_percentage
        FROM assessment_results r
        WHERE r.assessment_id = {latest_id}
        GROUP BY SUBSTR(r.control_id, 1, 5)
        ORDER BY compliance_percentage DESC
        """
        
        df = self._execute_query(query)
        filename = f"{self.output_dir}/category_breakdown.csv"
        df.to_csv(filename, index=False)
        print(f"📂 Exported category breakdown: {len(df)} categories")
        conn.close()
    
    def export_severity_distribution(self):
        """Export severity distribution for risk analysis."""
        conn = sqlite3.connect(self.db_path)
        
        # Get latest assessment ID
        latest_result = conn.execute(
            "SELECT id FROM assessments ORDER BY timestamp DESC LIMIT 1"
        ).fetchone()
        
        if not latest_result:
            conn.close()
            return
            
        latest_id = latest_result[0]
        
        query = f"""
        SELECT 
            'HIGH' as severity,
            r.status,
            COUNT(*) as count,
            ROUND(
                (COUNT(*) * 100.0) / (
                    SELECT COUNT(*) 
                    FROM assessment_results ar 
                    WHERE ar.assessment_id = {latest_id}
                ), 
                2
            ) as percentage
        FROM assessment_results r
        WHERE r.assessment_id = {latest_id}
        GROUP BY r.status
        ORDER BY r.status
        """
        
        df = self._execute_query(query)
        # Severity is already clean
        
        filename = f"{self.output_dir}/severity_distribution.csv"
        df.to_csv(filename, index=False)
        print(f"⚠️  Exported severity distribution: {len(df)} severity/status combinations")
        conn.close()
    
    def export_metadata(self):
        """Export metadata about the assessment for dashboard configuration."""
        conn = sqlite3.connect(self.db_path)
        
        # Get latest assessment info
        assessment_query = """
        SELECT 
            id, timestamp, account_id, total_controls, 
            passed_controls, failed_controls, score
        FROM assessments 
        ORDER BY timestamp DESC 
        LIMIT 1
        """
        
        assessment_result = conn.execute(assessment_query).fetchone()
        
        if not assessment_result:
            conn.close()
            return
        
        # Get unique categories and severities
        categories = [row[0] for row in conn.execute("SELECT DISTINCT category FROM controls").fetchall()]
        severities = [row[0] for row in conn.execute("SELECT DISTINCT severity FROM controls").fetchall()]
        
        metadata = {
            "export_timestamp": self.timestamp,
            "latest_assessment": {
                "id": assessment_result[0],
                "timestamp": assessment_result[1],
                "account_id": assessment_result[2],
                "total_controls": assessment_result[3],
                "passed_controls": assessment_result[4],
                "failed_controls": assessment_result[5],
                "score": assessment_result[6]
            },
            "available_categories": categories,
            "available_severities": [s.replace('Severity.', '') for s in severities],
            "export_files": [
                "compliance_summary.csv",
                "control_details.csv", 
                "compliance_trends.csv",
                "findings_summary.csv",
                "category_breakdown.csv",
                "severity_distribution.csv"
            ]
        }
        
        filename = f"{self.output_dir}/export_metadata.json"
        with open(filename, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        print(f"📄 Exported metadata: {filename}")
        conn.close()
    
    def _execute_query(self, query):
        """Execute SQL query and return pandas DataFrame."""
        conn = sqlite3.connect(self.db_path)
        try:
            df = pd.read_sql_query(query, conn)
            return df
        finally:
            conn.close()
    
    def generate_export_summary(self):
        """Generate a summary of the exported data."""
        print("\n" + "="*50)
        print("📊 CSPM DATA EXPORT SUMMARY")
        print("="*50)
        
        # Check if files exist and show their sizes
        files_info = []
        for filename in [
            "compliance_summary.csv",
            "control_details.csv",
            "compliance_trends.csv", 
            "findings_summary.csv",
            "category_breakdown.csv",
            "severity_distribution.csv",
            "export_metadata.json"
        ]:
            filepath = Path(self.output_dir) / filename
            if filepath.exists():
                size = filepath.stat().st_size
                rows = 0
                if filename.endswith('.csv'):
                    try:
                        df = pd.read_csv(filepath)
                        rows = len(df)
                    except:
                        rows = "Unknown"
                        
                files_info.append({
                    'file': filename,
                    'size_kb': round(size / 1024, 2),
                    'rows': rows
                })
        
        for info in files_info:
            if info['file'].endswith('.json'):
                print(f"📄 {info['file']}: {info['size_kb']} KB")
            else:
                print(f"📊 {info['file']}: {info['rows']} rows, {info['size_kb']} KB")
        
        print(f"\n✅ Export completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"📁 Output directory: {self.output_dir}/")

if __name__ == "__main__":
    # Initialize and run exporter
    exporter = CSPMDataExporter()
    
    try:
        exporter.export_all_data()
        exporter.generate_export_summary()
        
    except Exception as e:
        print(f"❌ Export failed: {e}")
        import traceback
        traceback.print_exc()