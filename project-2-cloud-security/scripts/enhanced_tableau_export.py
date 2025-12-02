import sys
import os
import sqlite3
import pandas as pd
import json
from datetime import datetime

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class EnhancedTableauExporter:
    def __init__(self, db_path="data/cspm.db", output_dir="tableau"):
        self.db_path = db_path
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def clean_severity(self, severity_str):
        """Clean severity format: 'Severity.HIGH' -> 'HIGH'"""
        if severity_str and isinstance(severity_str, str):
            return severity_str.replace('Severity.', '')
        return severity_str

    def parse_findings(self, findings_json):
        """Parse findings JSON and extract key fields for Tableau"""
        if not findings_json or findings_json == "[]":
            return {
                'finding_count': 0,
                'primary_severity': None,
                'primary_description': None,
                'primary_remediation': None,
                'resource_ids': None
            }
        
        try:
            findings = json.loads(findings_json)
            if not findings:
                return {
                    'finding_count': 0,
                    'primary_severity': None,
                    'primary_description': None,
                    'primary_remediation': None,
                    'resource_ids': None
                }
            
            # Get primary (first) finding for main details
            primary = findings[0]
            
            # Extract all resource IDs
            resource_ids = []
            for f in findings:
                if f.get('resource_id'):
                    resource_ids.append(f['resource_id'])
            
            return {
                'finding_count': len(findings),
                'primary_severity': self.clean_severity(primary.get('severity')),
                'primary_description': primary.get('description', ''),
                'primary_remediation': primary.get('remediation', ''),
                'resource_ids': ', '.join(resource_ids) if resource_ids else None
            }
            
        except (json.JSONDecodeError, Exception) as e:
            print(f"Error parsing findings: {e}")
            return {
                'finding_count': 0,
                'primary_severity': None,
                'primary_description': f"Parse error: {str(e)}",
                'primary_remediation': None,
                'resource_ids': None
            }

    def export_all_enhanced(self):
        print("Exporting enhanced data for Tableau...")
        self.export_compliance_summary_enhanced()
        self.export_control_details_enhanced()
        self.export_compliance_trends_enhanced()
        self.export_findings_detail()
        print(f"Enhanced exports saved to {self.output_dir}/")

    def export_compliance_summary_enhanced(self):
        """Enhanced compliance summary with better ratings"""
        conn = sqlite3.connect(self.db_path)
        query = """
        SELECT 
            a.id as assessment_id,
            a.timestamp,
            a.account_id,
            a.total_controls,
            a.passed_controls,
            a.failed_controls,
            a.score,
            CASE 
                WHEN a.score >= 90 THEN 'Excellent'
                WHEN a.score >= 80 THEN 'Good'
                WHEN a.score >= 70 THEN 'Fair'
                WHEN a.score >= 60 THEN 'Poor'
                ELSE 'Critical'
            END as rating,
            date(a.timestamp) as assessment_date,
            strftime('%Y-%m', a.timestamp) as assessment_month
        FROM assessments a
        ORDER BY a.timestamp DESC
        """
        df = pd.read_sql_query(query, conn)
        df.to_csv(f"{self.output_dir}/compliance_summary_enhanced.csv", index=False)
        conn.close()

    def export_control_details_enhanced(self):
        """Enhanced control details with parsed findings - ALL ASSESSMENTS"""
        conn = sqlite3.connect(self.db_path)
        
        # FIXED: Get ALL assessments, not just latest
        query = """
        SELECT 
            r.assessment_id,
            r.control_id,
            COALESCE(c.title, 'Unknown Control: ' || r.control_id) as title,
            COALESCE(c.description, 'No description available for ' || r.control_id) as description,
            COALESCE(c.severity, 'Unknown') as control_severity,
            COALESCE(c.category, 'Uncategorized') as category,
            r.status,
            r.findings,
            r.timestamp as last_checked,
            CASE 
                WHEN r.status = 'PASS' THEN 'Compliant'
                WHEN r.status = 'FAIL' THEN 'Non-Compliant'
                ELSE 'Unknown'
            END as compliance_status,
            CASE COALESCE(c.severity, 'Unknown')
                WHEN 'Critical' THEN 4
                WHEN 'High' THEN 3
                WHEN 'Medium' THEN 2
                WHEN 'Low' THEN 1
                ELSE 0
            END as severity_score
        FROM assessment_results r
        LEFT JOIN controls c ON r.control_id = c.control_id
        ORDER BY r.assessment_id DESC, severity_score DESC, r.control_id
        """
        
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        # Parse findings and add columns
        findings_data = []
        for _, row in df.iterrows():
            finding_info = self.parse_findings(row['findings'])
            findings_data.append(finding_info)
        
        findings_df = pd.DataFrame(findings_data)
        
        # Combine original data with parsed findings
        enhanced_df = pd.concat([df.drop('findings', axis=1), findings_df], axis=1)
        enhanced_df.to_csv(f"{self.output_dir}/control_details_enhanced.csv", index=False)
        print(f"  ✓ Exported {len(enhanced_df)} control results across all assessments")

    def export_compliance_trends_enhanced(self):
        """Enhanced trends with additional metrics"""
        conn = sqlite3.connect(self.db_path)
        query = """
        SELECT 
            date(timestamp) as date,
            AVG(score) as avg_score,
            MAX(score) as max_score,
            MIN(score) as min_score,
            COUNT(*) as assessment_count,
            AVG(passed_controls) as avg_passed,
            AVG(failed_controls) as avg_failed,
            strftime('%w', timestamp) as day_of_week,
            strftime('%Y-%m', timestamp) as year_month
        FROM assessments
        GROUP BY date(timestamp)
        ORDER BY date(timestamp)
        """
        df = pd.read_sql_query(query, conn)
        
        # Add trend indicators
        df['score_trend'] = df['avg_score'].diff().fillna(0)
        df['trend_direction'] = df['score_trend'].apply(
            lambda x: 'Improving' if x > 0 else 'Declining' if x < 0 else 'Stable'
        )
        
        df.to_csv(f"{self.output_dir}/compliance_trends_enhanced.csv", index=False)
        conn.close()

    def export_findings_detail(self):
        """Separate detailed findings table for drill-down analysis"""
        conn = sqlite3.connect(self.db_path)
        
        # Get findings from latest assessment
        latest_id = conn.execute("SELECT id FROM assessments ORDER BY timestamp DESC LIMIT 1").fetchone()[0]
        
        query = f"""
        SELECT 
            r.assessment_id,
            r.control_id,
            c.title as control_title,
            c.category,
            c.severity as control_severity,
            r.findings,
            r.timestamp
        FROM assessment_results r
        JOIN controls c ON r.control_id = c.control_id
        WHERE r.assessment_id = {latest_id} AND r.findings != '[]'
        """
        
        results = conn.execute(query).fetchall()
        conn.close()
        
        # Flatten findings into individual rows
        flattened_findings = []
        
        for row in results:
            assessment_id, control_id, control_title, category, control_severity, findings_json, timestamp = row
            
            try:
                findings = json.loads(findings_json)
                for i, finding in enumerate(findings):
                    flattened_findings.append({
                        'assessment_id': assessment_id,
                        'control_id': control_id,
                        'control_title': control_title,
                        'category': category,
                        'control_severity': control_severity,
                        'finding_number': i + 1,
                        'finding_severity': self.clean_severity(finding.get('severity')),
                        'description': finding.get('description', ''),
                        'remediation': finding.get('remediation', ''),
                        'resource_id': finding.get('resource_id'),
                        'timestamp': timestamp
                    })
            except (json.JSONDecodeError, Exception) as e:
                print(f"Error processing findings for {control_id}: {e}")
        
        findings_df = pd.DataFrame(flattened_findings)
        if not findings_df.empty:
            findings_df.to_csv(f"{self.output_dir}/findings_detail.csv", index=False)
        else:
            print("No detailed findings to export")

    def generate_summary_stats(self):
        """Generate summary statistics for the dashboard"""
        conn = sqlite3.connect(self.db_path)
        
        # Latest assessment stats
        latest_stats = conn.execute("""
            SELECT 
                score,
                total_controls,
                passed_controls,
                failed_controls,
                timestamp
            FROM assessments 
            ORDER BY timestamp DESC 
            LIMIT 1
        """).fetchone()
        
        # Category breakdown
        category_stats = conn.execute("""
            SELECT 
                c.category,
                COUNT(*) as total_controls,
                SUM(CASE WHEN r.status = 'PASS' THEN 1 ELSE 0 END) as passed_controls,
                SUM(CASE WHEN r.status = 'FAIL' THEN 1 ELSE 0 END) as failed_controls,
                ROUND(AVG(CASE WHEN r.status = 'PASS' THEN 100.0 ELSE 0.0 END), 2) as category_score
            FROM controls c
            JOIN assessment_results r ON c.control_id = r.control_id
            WHERE r.assessment_id = (SELECT id FROM assessments ORDER BY timestamp DESC LIMIT 1)
            GROUP BY c.category
            ORDER BY category_score DESC
        """).fetchall()
        
        conn.close()
        
        # Save summary stats
        summary_data = {
            'latest_assessment': {
                'score': latest_stats[0] if latest_stats else 0,
                'total_controls': latest_stats[1] if latest_stats else 0,
                'passed_controls': latest_stats[2] if latest_stats else 0,
                'failed_controls': latest_stats[3] if latest_stats else 0,
                'timestamp': latest_stats[4] if latest_stats else None
            },
            'category_breakdown': [
                {
                    'category': row[0],
                    'total_controls': row[1],
                    'passed_controls': row[2],
                    'failed_controls': row[3],
                    'category_score': row[4]
                }
                for row in category_stats
            ]
        }
        
        with open(f"{self.output_dir}/dashboard_summary.json", 'w') as f:
            json.dump(summary_data, f, indent=2)
        
        return summary_data

if __name__ == "__main__":
    exporter = EnhancedTableauExporter()
    exporter.export_all_enhanced()
    stats = exporter.generate_summary_stats()
    
    print("\n=== EXPORT SUMMARY ===")
    print(f"Latest Score: {stats['latest_assessment']['score']}%")
    print(f"Controls: {stats['latest_assessment']['passed_controls']}/{stats['latest_assessment']['total_controls']} passing")
    print("\nCategory Performance:")
    for cat in stats['category_breakdown']:
        print(f"  {cat['category']}: {cat['category_score']}% ({cat['passed_controls']}/{cat['total_controls']})")