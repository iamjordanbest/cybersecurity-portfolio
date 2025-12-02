import sys
import os
import sqlite3
import pandas as pd
from datetime import datetime

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data.database import DatabaseManager

class TableauExporter:
    def __init__(self, db_path="data/cspm.db", output_dir="tableau"):
        self.db_path = db_path
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def export_all(self):
        print("Exporting data for Tableau...")
        self.export_compliance_summary()
        self.export_control_details()
        self.export_compliance_trends()
        print(f"Exports saved to {self.output_dir}/")

    def export_compliance_summary(self):
        """Export high-level compliance metrics"""
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
                ELSE 'Poor'
            END as rating
        FROM assessments a
        ORDER BY a.timestamp DESC
        """
        df = pd.read_sql_query(query, conn)
        df.to_csv(f"{self.output_dir}/compliance_summary.csv", index=False)
        conn.close()

    def export_control_details(self):
        """Export detailed findings for the latest assessment"""
        conn = sqlite3.connect(self.db_path)
        
        # Get latest assessment ID
        latest_id = conn.execute("SELECT id FROM assessments ORDER BY timestamp DESC LIMIT 1").fetchone()[0]
        
        query = f"""
        SELECT 
            r.control_id,
            c.title,
            c.description,
            c.severity,
            c.category,
            r.status,
            r.findings,
            r.timestamp as last_checked
        FROM assessment_results r
        JOIN controls c ON r.control_id = c.control_id
        WHERE r.assessment_id = {latest_id}
        """
        df = pd.read_sql_query(query, conn)
        df.to_csv(f"{self.output_dir}/control_details.csv", index=False)
        conn.close()

    def export_compliance_trends(self):
        """Export daily compliance trends"""
        conn = sqlite3.connect(self.db_path)
        query = """
        SELECT 
            date(timestamp) as date,
            AVG(score) as avg_score,
            MAX(score) as max_score,
            MIN(score) as min_score
        FROM assessments
        GROUP BY date(timestamp)
        ORDER BY date(timestamp)
        """
        df = pd.read_sql_query(query, conn)
        df.to_csv(f"{self.output_dir}/compliance_trends.csv", index=False)
        conn.close()

if __name__ == "__main__":
    exporter = TableauExporter()
    exporter.export_all()
