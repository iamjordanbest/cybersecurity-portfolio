import sys
import os
import random
from datetime import datetime, timedelta
import json

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data.database import DatabaseManager
from models.compliance import AssessmentResult, ControlStatus, Finding, Severity

def generate_history():
    print("Generating mock historical data...")
    db = DatabaseManager()
    
    # Simulation parameters
    days_back = 30
    account_id = "307940789526" # Use the real account ID if possible, or mock
    
    # Controls list (simplified for mock generation)
    controls = [
        "CIS-1.4", "CIS-1.12", "CIS-1.16", "CIS-1.20",
        "CIS-2.1", "CIS-2.2", "CIS-2.7",
        "CIS-2.1.1", "CIS-2.1.2", "CIS-2.1.5",
        "CIS-4.1", "CIS-4.2", "CIS-4.3", "CIS-4.4", "CIS-4.5", "CIS-4.9"
    ]

    # Trend: Start low, improve over time
    base_pass_rate = 0.4
    
    for i in range(days_back, 0, -1):
        date = datetime.now() - timedelta(days=i)
        
        # Improve pass rate slightly each day
        pass_rate = min(0.95, base_pass_rate + (0.5 * (1 - i/days_back)))
        
        results = []
        for ctrl_id in controls:
            is_pass = random.random() < pass_rate
            
            status = ControlStatus.PASS if is_pass else ControlStatus.FAIL
            findings = []
            
            if not is_pass:
                findings.append(Finding(
                    control_id=ctrl_id,
                    severity=Severity.HIGH,
                    description="Mock finding for historical data",
                    remediation="Fix it"
                ))
            
            result = AssessmentResult(
                control_id=ctrl_id,
                status=status,
                timestamp=date,
                score=100.0 if is_pass else 0.0,
                findings=findings
            )
            results.append(result)
            
        # Save to DB manually to override timestamp
        # We need to modify save_assessment or just insert manually here
        # For simplicity, let's use the DB manager but we might need to patch the timestamp
        # Actually, save_assessment uses datetime.now(). Let's just insert manually for history.
        
        conn = db._init_db() # Re-init to get connection? No, _init_db closes it.
        import sqlite3
        conn = sqlite3.connect(db.db_path)
        c = conn.cursor()
        
        total = len(results)
        passed = sum(1 for r in results if r.status == ControlStatus.PASS)
        failed = sum(1 for r in results if r.status == ControlStatus.FAIL)
        score = (passed / total * 100) if total > 0 else 0
        
        c.execute('''
            INSERT INTO assessments (timestamp, account_id, total_controls, passed_controls, failed_controls, score)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (date.isoformat(), account_id, total, passed, failed, score))
        
        assessment_id = c.lastrowid
        
        for r in results:
            findings_json = json.dumps([f.__dict__ for f in r.findings], default=str)
            c.execute('''
                INSERT INTO assessment_results (assessment_id, control_id, status, timestamp, findings, evidence_path)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (assessment_id, r.control_id, r.status.value, date.isoformat(), findings_json, ""))
            
        conn.commit()
        conn.close()
        
        print(f"Generated run for {date.date()}: Score {score:.1f}%")

    print("History generation complete.")

if __name__ == "__main__":
    generate_history()
