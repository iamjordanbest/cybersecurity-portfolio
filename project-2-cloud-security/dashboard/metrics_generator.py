"""
CSPM Dashboard Metrics Generator
Provides data functions for the Streamlit dashboard
"""
import sqlite3
import pandas as pd
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List
import os

# Database path - robust resolution
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "data", "cspm.db")

def get_executive_metrics() -> Dict[str, Any]:
    """Get high-level compliance metrics"""
    if not os.path.exists(DB_PATH):
        # Return mock data if database doesn't exist
        return {
            "total_controls": 0,
            "passed_controls": 0,
            "failed_controls": 0,
            "score": 0,
            "timestamp": datetime.now().isoformat(),
            "account_id": "Demo"
        }
    
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    try:
        c.execute('SELECT * FROM assessments ORDER BY timestamp DESC LIMIT 1')
        row = c.fetchone()
        if row:
            return dict(row)
        else:
            return {
                "total_controls": 0,
                "passed_controls": 0,
                "failed_controls": 0,
                "score": 0,
                "timestamp": datetime.now().isoformat(),
                "account_id": "No Data"
            }
    finally:
        conn.close()

def get_category_performance() -> pd.DataFrame:
    """Get compliance performance by security category"""
    if not os.path.exists(DB_PATH):
        # Return mock data
        return pd.DataFrame({
            'category': ['IAM', 'S3', 'EC2', 'CloudTrail', 'Config'],
            'compliance_pct': [75.0, 80.0, 60.0, 90.0, 70.0],
            'passed': [3, 4, 3, 9, 7],
            'total': [4, 5, 5, 10, 10]
        })
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Get latest assessment ID
    c.execute('SELECT id FROM assessments ORDER BY timestamp DESC LIMIT 1')
    latest_assessment = c.fetchone()
    
    if not latest_assessment:
        conn.close()
        return pd.DataFrame()
    
    assessment_id = latest_assessment[0]
    
    # Get category performance from controls table joined with results
    query = '''
        SELECT 
            COALESCE(c.category, 'Unknown') as category,
            COUNT(*) as total,
            SUM(CASE WHEN ar.status = 'PASS' THEN 1 ELSE 0 END) as passed,
            ROUND(SUM(CASE WHEN ar.status = 'PASS' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1) as compliance_pct
        FROM assessment_results ar
        LEFT JOIN controls c ON ar.control_id = c.control_id
        WHERE ar.assessment_id = ?
        GROUP BY c.category
        ORDER BY compliance_pct DESC
    '''
    
    df = pd.read_sql_query(query, conn, params=(assessment_id,))
    conn.close()
    
    return df

def get_compliance_trends() -> pd.DataFrame:
    """Get historical compliance trends"""
    if not os.path.exists(DB_PATH):
        # Return mock trend data
        dates = pd.date_range(start=datetime.now() - timedelta(days=30), end=datetime.now(), freq='D')
        return pd.DataFrame({
            'date': dates,
            'score': [65 + i * 0.5 + (i % 3) * 2 for i in range(len(dates))]
        })
    
    conn = sqlite3.connect(DB_PATH)
    
    query = '''
        SELECT timestamp, score 
        FROM assessments 
        WHERE timestamp >= date('now', '-30 days')
        ORDER BY timestamp ASC
    '''
    
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    if not df.empty:
        df['date'] = pd.to_datetime(df['timestamp'])
    
    return df

def get_failed_controls() -> pd.DataFrame:
    """Get all failed controls with details"""
    if not os.path.exists(DB_PATH):
        # Return mock failed controls
        return pd.DataFrame({
            'control_id': ['CIS-1.1', 'CIS-2.1', 'CIS-4.3'],
            'title': ['Root access key usage', 'CloudTrail enabled', 'VPC flow logs enabled'],
            'category': ['IAM', 'CloudTrail', 'VPC'],
            'severity': ['CRITICAL', 'HIGH', 'MEDIUM'],
            'status': ['FAIL', 'FAIL', 'FAIL'],
            'reason': ['Root access keys detected', 'CloudTrail not configured', 'VPC flow logs disabled']
        })
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Get latest assessment ID
    c.execute('SELECT id FROM assessments ORDER BY timestamp DESC LIMIT 1')
    latest_assessment = c.fetchone()
    
    if not latest_assessment:
        conn.close()
        return pd.DataFrame()
    
    assessment_id = latest_assessment[0]
    
    query = '''
        SELECT 
            ar.control_id,
            COALESCE(c.title, ar.control_id) as title,
            COALESCE(c.category, 'Unknown') as category,
            COALESCE(c.severity, 'MEDIUM') as severity,
            ar.status,
            ar.findings as reason
        FROM assessment_results ar
        LEFT JOIN controls c ON ar.control_id = c.control_id
        WHERE ar.assessment_id = ? AND ar.status = 'FAIL'
        ORDER BY 
            CASE WHEN c.severity = 'CRITICAL' THEN 1
                 WHEN c.severity = 'HIGH' THEN 2
                 WHEN c.severity = 'MEDIUM' THEN 3
                 ELSE 4 END
    '''
    
    df = pd.read_sql_query(query, conn, params=(assessment_id,))
    conn.close()
    
    # Clean up findings JSON if needed
    if not df.empty and 'reason' in df.columns:
        df['reason'] = df['reason'].fillna('No details available')
    
    return df

def get_all_controls_status() -> pd.DataFrame:
    """Get status of all controls"""
    if not os.path.exists(DB_PATH):
        # Return comprehensive mock data showing all CIS controls
        controls_data = []
        categories = ['IAM', 'S3', 'EC2', 'CloudTrail', 'Config', 'CloudWatch', 'SNS', 'VPC']
        statuses = ['PASS', 'FAIL']
        severities = ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']
        
        for i, cat in enumerate(categories):
            for j in range(3):  # 3 controls per category
                control_id = f"CIS-{i+1}.{j+1}"
                controls_data.append({
                    'control_id': control_id,
                    'title': f"{cat} Security Control {j+1}",
                    'category': cat,
                    'severity': severities[j % len(severities)],
                    'status': statuses[j % 2],  # Alternating pass/fail
                    'description': f"Validates {cat.lower()} security configuration {j+1}"
                })
        
        return pd.DataFrame(controls_data)
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Get latest assessment ID
    c.execute('SELECT id FROM assessments ORDER BY timestamp DESC LIMIT 1')
    latest_assessment = c.fetchone()
    
    if not latest_assessment:
        conn.close()
        return pd.DataFrame()
    
    assessment_id = latest_assessment[0]
    
    query = '''
        SELECT 
            ar.control_id,
            COALESCE(c.title, ar.control_id) as title,
            COALESCE(c.category, 'Unknown') as category,
            COALESCE(c.severity, 'MEDIUM') as severity,
            ar.status,
            COALESCE(c.description, 'No description available') as description
        FROM assessment_results ar
        LEFT JOIN controls c ON ar.control_id = c.control_id
        WHERE ar.assessment_id = ?
        ORDER BY ar.control_id
    '''
    
    df = pd.read_sql_query(query, conn, params=(assessment_id,))
    conn.close()
    
    return df

def get_control_details(control_id: str) -> Dict[str, Any]:
    """Get detailed information about a specific control"""
    if not os.path.exists(DB_PATH):
        return {
            'control_id': control_id,
            'title': f'Control {control_id}',
            'description': 'Mock control for demonstration',
            'category': 'Demo',
            'severity': 'MEDIUM',
            'cis_reference': 'https://www.cisecurity.org/'
        }
    
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    c.execute('SELECT * FROM controls WHERE control_id = ?', (control_id,))
    row = c.fetchone()
    conn.close()
    
    return dict(row) if row else {}

def get_total_cis_controls() -> Dict[str, int]:
    """Get count of total CIS controls implemented"""
    if not os.path.exists(DB_PATH):
        return {
            'total_implemented': 24,  # Mock data
            'total_possible': 40,
            'implementation_percentage': 60.0
        }
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Count total controls in our system
    c.execute('SELECT COUNT(*) FROM controls')
    implemented = c.fetchone()[0]
    
    # CIS AWS Foundations Benchmark v1.4.0 - we've implemented 32 controls
    total_possible = 32
    
    conn.close()
    
    return {
        'total_implemented': implemented,
        'total_possible': total_possible,
        'implementation_percentage': (implemented / total_possible * 100) if total_possible > 0 else 0
    }