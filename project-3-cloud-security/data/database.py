import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Any
from models.compliance import AssessmentResult, ControlStatus

class DatabaseManager:
    def __init__(self, db_path: str = "data/cspm.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """Initialize database schema"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # Controls table (static data)
        c.execute('''
            CREATE TABLE IF NOT EXISTS controls (
                control_id TEXT PRIMARY KEY,
                title TEXT,
                description TEXT,
                severity TEXT,
                category TEXT,
                cis_reference TEXT
            )
        ''')

        # Assessments table (historical runs)
        c.execute('''
            CREATE TABLE IF NOT EXISTS assessments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                account_id TEXT,
                total_controls INTEGER,
                passed_controls INTEGER,
                failed_controls INTEGER,
                score REAL
            )
        ''')

        # Assessment Results (individual control results per run)
        c.execute('''
            CREATE TABLE IF NOT EXISTS assessment_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                assessment_id INTEGER,
                control_id TEXT,
                status TEXT,
                timestamp TEXT,
                findings TEXT,  -- JSON stored as text
                evidence_path TEXT,
                FOREIGN KEY (assessment_id) REFERENCES assessments(id),
                FOREIGN KEY (control_id) REFERENCES controls(control_id)
            )
        ''')
        
        conn.commit()
        conn.close()

    def save_assessment(self, account_id: str, results: List[AssessmentResult]) -> int:
        """Save a full audit run to the database"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # Calculate summary metrics
        total = len(results)
        passed = sum(1 for r in results if r.status == ControlStatus.PASS)
        failed = sum(1 for r in results if r.status == ControlStatus.FAIL)
        score = (passed / total * 100) if total > 0 else 0
        timestamp = datetime.now().isoformat()

        # Insert assessment run
        c.execute('''
            INSERT INTO assessments (timestamp, account_id, total_controls, passed_controls, failed_controls, score)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (timestamp, account_id, total, passed, failed, score))
        
        assessment_id = c.lastrowid

        # Insert individual results
        for r in results:
            # Ensure control exists
            # In a real app we'd populate controls separately, but here we can upsert
            # We don't have full control details in AssessmentResult, so we skip upserting static data for now
            # or we assume it's populated. Let's just store the result.
            
            findings_json = json.dumps([f.__dict__ for f in r.findings], default=str)
            
            c.execute('''
                INSERT INTO assessment_results (assessment_id, control_id, status, timestamp, findings, evidence_path)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (assessment_id, r.control_id, r.status.value, r.timestamp.isoformat(), findings_json, ""))

        conn.commit()
        conn.close()
        return assessment_id

    def get_latest_assessment(self):
        """Get the most recent assessment summary"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        
        c.execute('SELECT * FROM assessments ORDER BY timestamp DESC LIMIT 1')
        row = c.fetchone()
        conn.close()
        return dict(row) if row else None

    def get_compliance_history(self):
        """Get historical compliance scores"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        
        c.execute('SELECT timestamp, score FROM assessments ORDER BY timestamp ASC')
        rows = c.fetchall()
        conn.close()
        return [dict(row) for row in rows]
