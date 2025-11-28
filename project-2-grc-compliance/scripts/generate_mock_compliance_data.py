#!/usr/bin/env python3
"""
Generate Mock Compliance Data

This script generates realistic compliance assessment data for the GRC Analytics Platform.
It creates:
- Compliance assessments over 6 months
- Risk scores based on control status
- Remediation actions for failed controls
- Realistic trends (improving, stable, degrading)
"""

import sqlite3
import random
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Tuple
import json
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
ASSESSMENT_MONTHS = 6
ASSESSORS = [
    'John Smith', 'Sarah Johnson', 'Mike Davis', 'Emily Chen', 
    'David Williams', 'Lisa Anderson', 'James Brown'
]

# Status distributions (realistic for a maturing security program)
STATUS_DISTRIBUTIONS = {
    0: {'compliant': 0.68, 'partial': 0.15, 'non_compliant': 0.12, 'not_assessed': 0.05},  # Month 0 (6 months ago)
    1: {'compliant': 0.70, 'partial': 0.15, 'non_compliant': 0.11, 'not_assessed': 0.04},
    2: {'compliant': 0.73, 'partial': 0.14, 'non_compliant': 0.10, 'not_assessed': 0.03},
    3: {'compliant': 0.76, 'partial': 0.13, 'non_compliant': 0.09, 'not_assessed': 0.02},
    4: {'compliant': 0.78, 'partial': 0.13, 'non_compliant': 0.08, 'not_assessed': 0.01},
    5: {'compliant': 0.80, 'partial': 0.12, 'non_compliant': 0.07, 'not_assessed': 0.01},  # Current month
}

# Risk ratings based on control family (some families are higher risk)
HIGH_RISK_FAMILIES = ['Access Control', 'Identification and Authentication', 
                      'System and Communications Protection', 'System and Information Integrity']
MEDIUM_RISK_FAMILIES = ['Audit and Accountability', 'Configuration Management', 
                        'Incident Response', 'Contingency Planning']

# Implementation status options
IMPLEMENTATION_STATUSES = ['implemented', 'planned', 'alternative']


def get_db_connection(db_path: str) -> sqlite3.Connection:
    """Create database connection."""
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.Error as e:
        logger.error(f"Error connecting to database: {e}")
        sys.exit(1)


def get_controls_from_db(conn: sqlite3.Connection) -> List[Dict]:
    """Fetch all controls from the database."""
    cursor = conn.cursor()
    cursor.execute('''
        SELECT control_id, control_family, control_name, control_description
        FROM nist_controls
        ORDER BY control_id
    ''')
    
    controls = []
    for row in cursor.fetchall():
        controls.append({
            'control_id': row['control_id'],
            'family': row['control_family'],
            'name': row['control_name'],
            'description': row['control_description']
        })
    
    return controls


def get_control_risk_rating(control: Dict) -> str:
    """Determine risk rating for a control based on its family and threat mappings."""
    family = control['family']
    
    if family in HIGH_RISK_FAMILIES:
        # 60% critical, 30% high, 10% medium
        return random.choices(['critical', 'high', 'medium'], weights=[0.6, 0.3, 0.1])[0]
    elif family in MEDIUM_RISK_FAMILIES:
        # 20% critical, 50% high, 30% medium
        return random.choices(['critical', 'high', 'medium'], weights=[0.2, 0.5, 0.3])[0]
    else:
        # 5% critical, 25% high, 50% medium, 20% low
        return random.choices(['critical', 'high', 'medium', 'low'], weights=[0.05, 0.25, 0.5, 0.2])[0]


def generate_compliance_status(month: int, control: Dict, previous_status: str = None) -> str:
    """
    Generate compliance status for a control in a given month.
    Takes into account previous status to create realistic trends.
    """
    distribution = STATUS_DISTRIBUTIONS[month]
    
    # If we have a previous status, apply some stickiness (controls don't change dramatically)
    if previous_status:
        if previous_status == 'compliant':
            # 85% stay compliant, 10% degrade to partial, 5% to non_compliant
            status = random.choices(
                ['compliant', 'partial', 'non_compliant'],
                weights=[0.85, 0.10, 0.05]
            )[0]
        elif previous_status == 'partial':
            # 40% improve to compliant, 50% stay partial, 10% degrade
            status = random.choices(
                ['compliant', 'partial', 'non_compliant'],
                weights=[0.40, 0.50, 0.10]
            )[0]
        elif previous_status == 'non_compliant':
            # 30% improve to partial, 15% to compliant, 55% stay non-compliant
            status = random.choices(
                ['compliant', 'partial', 'non_compliant'],
                weights=[0.15, 0.30, 0.55]
            )[0]
        else:  # not_assessed
            # 70% get assessed (distributed normally), 30% stay unassessed
            if random.random() < 0.70:
                status = random.choices(
                    ['compliant', 'partial', 'non_compliant'],
                    weights=[0.70, 0.20, 0.10]
                )[0]
            else:
                status = 'not_assessed'
    else:
        # First assessment - use monthly distribution
        status = random.choices(
            list(distribution.keys()),
            weights=list(distribution.values())
        )[0]
    
    return status


def generate_assessment_date(month: int) -> datetime:
    """Generate a random assessment date within the given month."""
    base_date = datetime.now() - timedelta(days=30 * (ASSESSMENT_MONTHS - month))
    # Random day within the month
    day_offset = random.randint(0, 28)
    return base_date + timedelta(days=day_offset)


def generate_remediation_plan(control: Dict, status: str) -> str:
    """Generate a remediation plan based on control and status."""
    if status == 'compliant':
        return None
    
    templates = {
        'non_compliant': [
            f"Implement {control['name']} controls according to NIST guidelines",
            f"Deploy technical controls for {control['control_id']}",
            f"Update policies and procedures for {control['name']}",
            f"Conduct training for {control['name']} requirements",
        ],
        'partial': [
            f"Complete remaining implementation tasks for {control['name']}",
            f"Enhance existing controls for {control['control_id']}",
            f"Document procedures for {control['name']}",
            f"Remediate identified gaps in {control['control_id']}",
        ],
        'not_assessed': [
            f"Schedule assessment for {control['name']}",
            f"Prepare documentation for {control['control_id']} assessment",
        ]
    }
    
    return random.choice(templates.get(status, templates['non_compliant']))


def generate_target_date(assessment_date: datetime, status: str, risk_rating: str) -> datetime:
    """Generate target remediation date based on risk and status."""
    if status == 'compliant':
        return None
    
    # Days to remediation based on risk
    risk_days = {
        'critical': (7, 30),    # 1 week to 1 month
        'high': (30, 60),       # 1-2 months
        'medium': (60, 90),     # 2-3 months
        'low': (90, 180)        # 3-6 months
    }
    
    days_min, days_max = risk_days.get(risk_rating, (30, 90))
    days_offset = random.randint(days_min, days_max)
    
    return assessment_date + timedelta(days=days_offset)


def generate_compliance_assessments(conn: sqlite3.Connection, controls: List[Dict]):
    """Generate compliance assessments for all controls over time."""
    cursor = conn.cursor()
    
    logger.info(f"Generating {ASSESSMENT_MONTHS} months of compliance assessments for {len(controls)} controls...")
    
    total_assessments = 0
    control_history = {}  # Track previous status for each control
    
    for month in range(ASSESSMENT_MONTHS):
        assessment_date = datetime.now() - timedelta(days=30 * (ASSESSMENT_MONTHS - month - 1))
        
        logger.info(f"Generating assessments for month {month + 1}/{ASSESSMENT_MONTHS} ({assessment_date.strftime('%Y-%m')})")
        
        for control in controls:
            control_id = control['control_id']
            
            # Get previous status for this control
            previous_status = control_history.get(control_id)
            
            # Generate status for this month
            status = generate_compliance_status(month, control, previous_status)
            control_history[control_id] = status
            
            # Skip if not assessed
            if status == 'not_assessed':
                continue
            
            # Get risk rating
            risk_rating = get_control_risk_rating(control)
            
            # Generate implementation status
            if status == 'compliant':
                impl_status = 'implemented'
            elif status == 'partial':
                impl_status = random.choice(['implemented', 'alternative'])
            else:
                impl_status = random.choice(['planned', 'implemented'])
            
            # Generate assessment details
            assessor = random.choice(ASSESSORS)
            evidence_provided = status in ['compliant', 'partial']
            remediation_plan = generate_remediation_plan(control, status)
            target_date = generate_target_date(assessment_date, status, risk_rating)
            
            # Generate random assessment date within the month
            actual_assessment_date = assessment_date + timedelta(days=random.randint(0, 28))
            
            # Notes
            notes_templates = {
                'compliant': [
                    'Control is properly implemented and functioning as expected.',
                    'All requirements met. Evidence reviewed and validated.',
                    'Control tested and verified to be effective.',
                ],
                'partial': [
                    'Control partially implemented. Some gaps identified.',
                    'Technical controls in place but documentation incomplete.',
                    'Implementation in progress. Expected completion soon.',
                ],
                'non_compliant': [
                    'Control not implemented. Remediation plan required.',
                    'Significant gaps identified. Immediate action needed.',
                    'Control requirements not met. Remediation in progress.',
                ]
            }
            notes = random.choice(notes_templates.get(status, notes_templates['non_compliant']))
            
            # Insert assessment
            try:
                cursor.execute('''
                    INSERT INTO compliance_assessments (
                        control_id, assessment_date, compliance_status, 
                        implementation_status, risk_rating, assessor,
                        evidence_provided, remediation_plan, target_date,
                        notes, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                ''', (
                    control_id,
                    actual_assessment_date.strftime('%Y-%m-%d'),
                    status,
                    impl_status,
                    risk_rating,
                    assessor,
                    1 if evidence_provided else 0,
                    remediation_plan,
                    target_date.strftime('%Y-%m-%d') if target_date else None,
                    notes
                ))
                total_assessments += 1
            except sqlite3.IntegrityError as e:
                logger.warning(f"Duplicate assessment for {control_id} on {actual_assessment_date}: {e}")
    
    conn.commit()
    logger.info(f"Generated {total_assessments} compliance assessments")
    
    return total_assessments


def calculate_risk_scores(conn: sqlite3.Connection, controls: List[Dict]):
    """Calculate and store risk scores for controls."""
    cursor = conn.cursor()
    
    logger.info("Calculating risk scores based on threat intelligence and compliance status...")
    
    risk_scores_created = 0
    
    for control in controls:
        control_id = control['control_id']
        
        # Get latest assessment
        cursor.execute('''
            SELECT compliance_status, risk_rating
            FROM compliance_assessments
            WHERE control_id = ?
            ORDER BY assessment_date DESC
            LIMIT 1
        ''', (control_id,))
        
        assessment = cursor.fetchone()
        
        if not assessment:
            continue
        
        status = assessment['compliance_status']
        risk_rating = assessment['risk_rating']
        
        # Get threat intelligence counts
        cursor.execute('''
            SELECT COUNT(*) as kev_count
            FROM cve_control_mapping
            WHERE control_id = ?
        ''', (control_id,))
        kev_count = cursor.fetchone()['kev_count']
        
        cursor.execute('''
            SELECT COUNT(*) as attack_count
            FROM attack_control_mapping
            WHERE control_id = ?
        ''', (control_id,))
        attack_count = cursor.fetchone()['attack_count']
        
        # Get overdue KEV count
        cursor.execute('''
            SELECT COUNT(*) as overdue_count
            FROM cve_control_mapping ccm
            JOIN cisa_kev ck ON ccm.cve_id = ck.cve_id
            WHERE ccm.control_id = ? AND ck.due_date < date('now')
        ''', (control_id,))
        overdue_kev_count = cursor.fetchone()['overdue_count']
        
        # Get ransomware-related KEV count
        cursor.execute('''
            SELECT COUNT(*) as ransomware_count
            FROM cve_control_mapping ccm
            JOIN cisa_kev ck ON ccm.cve_id = ck.cve_id
            WHERE ccm.control_id = ? AND ck.known_ransomware_use = 1
        ''', (control_id,))
        ransomware_count = cursor.fetchone()['ransomware_count']
        
        # Calculate base risk score (0-100)
        status_multipliers = {
            'non_compliant': 3.0,
            'not_assessed': 2.0,
            'partial': 1.5,
            'compliant': 0.1
        }
        
        risk_multipliers = {
            'critical': 10.0,
            'high': 7.5,
            'medium': 5.0,
            'low': 2.5
        }
        
        base_risk = status_multipliers.get(status, 1.0) * risk_multipliers.get(risk_rating, 5.0)
        
        # Adjust for threat intelligence
        threat_factor = 1.0 + (kev_count * 0.1) + (attack_count * 0.01)
        threat_adjusted = base_risk * min(threat_factor, 3.0)  # Cap at 3x
        
        # Calculate priority score (weighted)
        priority_score = (
            threat_adjusted * 0.6 +  # 60% from risk
            overdue_kev_count * 2.0 +  # Additional weight for overdue
            ransomware_count * 1.5     # Additional weight for ransomware
        )
        
        # Normalize scores to 0-100
        base_risk = min(base_risk, 100.0)
        threat_adjusted = min(threat_adjusted, 100.0)
        priority_score = min(priority_score, 100.0)
        
        # Insert risk score
        try:
            cursor.execute('''
                INSERT INTO control_risk_scores (
                    control_id, calculation_date, base_risk_score,
                    threat_adjusted_score, kev_cve_count, attack_technique_count,
                    overdue_kev_count, ransomware_related_count, priority_score,
                    created_at
                ) VALUES (?, CURRENT_TIMESTAMP, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ''', (
                control_id, base_risk, threat_adjusted, kev_count,
                attack_count, overdue_kev_count, ransomware_count, priority_score
            ))
            risk_scores_created += 1
        except sqlite3.IntegrityError as e:
            logger.warning(f"Error inserting risk score for {control_id}: {e}")
    
    conn.commit()
    logger.info(f"Calculated {risk_scores_created} risk scores")
    
    return risk_scores_created


def generate_remediation_actions(conn: sqlite3.Connection):
    """Generate remediation actions for non-compliant controls."""
    cursor = conn.cursor()
    
    logger.info("Generating remediation actions for non-compliant controls...")
    
    # Get non-compliant and partial assessments from latest month
    cursor.execute('''
        SELECT DISTINCT
            ca.control_id,
            ca.remediation_plan,
            ca.target_date,
            ca.risk_rating,
            nc.control_name
        FROM compliance_assessments ca
        JOIN nist_controls nc ON ca.control_id = nc.control_id
        WHERE ca.compliance_status IN ('non_compliant', 'partial')
        AND ca.assessment_id IN (
            SELECT assessment_id
            FROM compliance_assessments ca2
            WHERE ca2.control_id = ca.control_id
            ORDER BY ca2.assessment_date DESC
            LIMIT 1
        )
    ''')
    
    assessments = cursor.fetchall()
    remediation_count = 0
    
    action_types = ['patch', 'config_change', 'policy_update', 'training', 'compensating_control']
    statuses = ['open', 'in_progress', 'in_progress', 'in_progress']  # Mostly in progress
    
    for assessment in assessments:
        control_id = assessment['control_id']
        
        # Get associated CVEs for this control
        cursor.execute('''
            SELECT cve_id
            FROM cve_control_mapping
            WHERE control_id = ?
            LIMIT 1
        ''', (control_id,))
        
        cve_row = cursor.fetchone()
        cve_id = cve_row['cve_id'] if cve_row else None
        
        action_type = random.choice(action_types)
        priority = assessment['risk_rating']
        status = random.choice(statuses)
        assigned_to = random.choice(ASSESSORS)
        
        # Estimate costs
        cost_ranges = {
            'critical': (5000, 15000),
            'high': (2000, 8000),
            'medium': (500, 3000),
            'low': (100, 1000)
        }
        
        min_cost, max_cost = cost_ranges.get(priority, (500, 3000))
        estimated_cost = random.randint(min_cost, max_cost)
        
        # Actual cost (if in progress, might have some cost)
        actual_cost = None
        if status == 'in_progress':
            actual_cost = random.randint(int(estimated_cost * 0.3), int(estimated_cost * 0.7))
        
        try:
            cursor.execute('''
                INSERT INTO remediation_actions (
                    control_id, cve_id, action_type, description,
                    priority, assigned_to, status, due_date,
                    estimated_cost, actual_cost, notes,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            ''', (
                control_id,
                cve_id,
                action_type,
                assessment['remediation_plan'],
                priority,
                assigned_to,
                status,
                assessment['target_date'],
                estimated_cost,
                actual_cost,
                f"Remediation action for {assessment['control_name']}"
            ))
            remediation_count += 1
        except sqlite3.IntegrityError as e:
            logger.warning(f"Error inserting remediation action for {control_id}: {e}")
    
    conn.commit()
    logger.info(f"Generated {remediation_count} remediation actions")
    
    return remediation_count


def generate_statistics(conn: sqlite3.Connection) -> Dict:
    """Generate summary statistics."""
    cursor = conn.cursor()
    
    stats = {}
    
    # Total controls
    cursor.execute('SELECT COUNT(*) as count FROM nist_controls')
    stats['total_controls'] = cursor.fetchone()['count']
    
    # Total assessments
    cursor.execute('SELECT COUNT(*) as count FROM compliance_assessments')
    stats['total_assessments'] = cursor.fetchone()['count']
    
    # Latest compliance status distribution
    cursor.execute('''
        SELECT compliance_status, COUNT(*) as count
        FROM compliance_assessments ca
        WHERE ca.assessment_id IN (
            SELECT assessment_id
            FROM compliance_assessments ca2
            WHERE ca2.control_id = ca.control_id
            ORDER BY ca2.assessment_date DESC
            LIMIT 1
        )
        GROUP BY compliance_status
    ''')
    stats['status_distribution'] = {row['compliance_status']: row['count'] for row in cursor.fetchall()}
    
    # Calculate compliance percentage
    compliant = stats['status_distribution'].get('compliant', 0)
    total_assessed = sum(v for k, v in stats['status_distribution'].items() if k != 'not_assessed')
    stats['compliance_percentage'] = round((compliant / total_assessed * 100) if total_assessed > 0 else 0, 2)
    
    # Risk scores
    cursor.execute('SELECT COUNT(*) as count FROM control_risk_scores')
    stats['risk_scores_calculated'] = cursor.fetchone()['count']
    
    # Remediation actions
    cursor.execute('SELECT COUNT(*) as count FROM remediation_actions')
    stats['remediation_actions'] = cursor.fetchone()['count']
    
    # High risk controls
    cursor.execute('''
        SELECT COUNT(*) as count
        FROM control_risk_scores
        WHERE priority_score > 50
    ''')
    stats['high_risk_controls'] = cursor.fetchone()['count']
    
    return stats


def main():
    """Main execution function."""
    project_root = Path(__file__).parent.parent
    db_file = project_root / 'data' / 'processed' / 'grc_analytics.db'
    
    logger.info("=" * 70)
    logger.info("GRC Analytics Platform - Mock Compliance Data Generator")
    logger.info("=" * 70)
    
    # Initialize database if it doesn't exist
    db_exists = db_file.exists()
    
    # Connect to database (creates it if not exists)
    conn = get_db_connection(str(db_file))
    
    if not db_exists:
        logger.info("Database not found. Initializing schema...")
        
        # Embedded schema to avoid external file dependency
        schema_sql = """
-- Enhanced GRC Analytics Platform Database Schema (SQLite Compatible)
-- Includes real threat intelligence integration

-- ============================================================================
-- Core NIST 800-53 Controls (from OSCAL)
-- ============================================================================

CREATE TABLE IF NOT EXISTS nist_controls (
    control_id VARCHAR(20) PRIMARY KEY,
    control_family VARCHAR(50) NOT NULL,
    control_name VARCHAR(255) NOT NULL,
    control_description TEXT,
    baseline_low BOOLEAN DEFAULT 0,
    baseline_moderate BOOLEAN DEFAULT 0,
    baseline_high BOOLEAN DEFAULT 0,
    control_enhancements TEXT,  -- JSON array stored as text
    related_controls TEXT,  -- JSON array stored as text
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- CISA Known Exploited Vulnerabilities
-- ============================================================================

CREATE TABLE IF NOT EXISTS cisa_kev (
    cve_id VARCHAR(20) PRIMARY KEY,
    vendor_project VARCHAR(255),
    product VARCHAR(255),
    vulnerability_name VARCHAR(500),
    short_description TEXT,
    required_action TEXT,
    known_ransomware_use BOOLEAN DEFAULT 0,
    date_added DATE NOT NULL,
    due_date DATE NOT NULL,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- NIST NVD Vulnerabilities
-- ============================================================================

CREATE TABLE IF NOT EXISTS nvd_vulnerabilities (
    cve_id VARCHAR(20) PRIMARY KEY,
    published_date TIMESTAMP,
    last_modified_date TIMESTAMP,
    description TEXT,
    cvss_v3_score DECIMAL(3,1),
    cvss_v3_severity VARCHAR(20),
    cvss_v2_score DECIMAL(3,1),
    cvss_v2_severity VARCHAR(20),
    cwe_ids TEXT,  -- JSON array stored as text
    cpe_names TEXT,  -- JSON array stored as text
    reference_urls TEXT,  -- JSON array stored as text
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- MITRE ATT&CK Techniques
-- ============================================================================

CREATE TABLE IF NOT EXISTS mitre_attack_techniques (
    technique_id VARCHAR(20) PRIMARY KEY,
    technique_name VARCHAR(255) NOT NULL,
    tactic VARCHAR(100),
    description TEXT,
    platforms TEXT,  -- JSON array stored as text
    detection TEXT,
    mitigation_ids TEXT,  -- JSON array stored as text
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- CVE to NIST Control Mapping
-- ============================================================================

CREATE TABLE IF NOT EXISTS cve_control_mapping (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cve_id VARCHAR(20) NOT NULL,
    control_id VARCHAR(20) NOT NULL,
    mapping_type VARCHAR(50), -- 'primary', 'secondary', 'related'
    confidence_score DECIMAL(3,2), -- 0.0 to 1.0
    mapping_source VARCHAR(100), -- 'automated', 'manual', 'ml_model'
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (cve_id) REFERENCES cisa_kev(cve_id) ON DELETE CASCADE,
    FOREIGN KEY (control_id) REFERENCES nist_controls(control_id) ON DELETE CASCADE,
    UNIQUE(cve_id, control_id)
);

-- ============================================================================
-- MITRE ATT&CK to NIST Control Mapping
-- ============================================================================

CREATE TABLE IF NOT EXISTS attack_control_mapping (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    technique_id VARCHAR(20) NOT NULL,
    control_id VARCHAR(20) NOT NULL,
    effectiveness VARCHAR(20), -- 'high', 'medium', 'low'
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (technique_id) REFERENCES mitre_attack_techniques(technique_id) ON DELETE CASCADE,
    FOREIGN KEY (control_id) REFERENCES nist_controls(control_id) ON DELETE CASCADE,
    UNIQUE(technique_id, control_id)
);

-- ============================================================================
-- Compliance Assessment Data
-- ============================================================================

CREATE TABLE IF NOT EXISTS compliance_assessments (
    assessment_id INTEGER PRIMARY KEY AUTOINCREMENT,
    control_id VARCHAR(20) NOT NULL,
    assessment_date DATE NOT NULL,
    compliance_status VARCHAR(20) NOT NULL, -- 'compliant', 'partial', 'non_compliant', 'not_assessed'
    implementation_status VARCHAR(20), -- 'implemented', 'planned', 'alternative'
    risk_rating VARCHAR(20), -- 'critical', 'high', 'medium', 'low'
    assessor VARCHAR(255),
    evidence_provided BOOLEAN DEFAULT 0,
    remediation_plan TEXT,
    target_date DATE,
    actual_date DATE,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (control_id) REFERENCES nist_controls(control_id) ON DELETE CASCADE
);

-- ============================================================================
-- Control Risk Scores
-- ============================================================================

CREATE TABLE IF NOT EXISTS control_risk_scores (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    control_id VARCHAR(20) NOT NULL,
    calculation_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    base_risk_score DECIMAL(5,2), -- Base risk without threat intel
    threat_adjusted_score DECIMAL(5,2), -- Adjusted with KEV/ATT&CK data
    kev_cve_count INTEGER DEFAULT 0, -- Number of KEV CVEs this control protects against
    attack_technique_count INTEGER DEFAULT 0, -- Number of ATT&CK techniques mitigated
    overdue_kev_count INTEGER DEFAULT 0, -- KEV CVEs past due date
    ransomware_related_count INTEGER DEFAULT 0, -- KEV CVEs with known ransomware use
    priority_score DECIMAL(5,2), -- Final prioritization score
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (control_id) REFERENCES nist_controls(control_id) ON DELETE CASCADE
);

-- ============================================================================
-- Remediation Tracking
-- ============================================================================

CREATE TABLE IF NOT EXISTS remediation_actions (
    action_id INTEGER PRIMARY KEY AUTOINCREMENT,
    control_id VARCHAR(20) NOT NULL,
    cve_id VARCHAR(20),
    action_type VARCHAR(50), -- 'patch', 'config_change', 'compensating_control', etc.
    description TEXT NOT NULL,
    priority VARCHAR(20), -- 'critical', 'high', 'medium', 'low'
    assigned_to VARCHAR(255),
    status VARCHAR(20), -- 'open', 'in_progress', 'completed', 'deferred'
    due_date DATE,
    completed_date DATE,
    estimated_cost DECIMAL(10,2),
    actual_cost DECIMAL(10,2),
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (cve_id) REFERENCES cisa_kev(cve_id) ON DELETE SET NULL
);

-- ============================================================================
-- Indices for Performance Optimization
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_assessments_control_date ON compliance_assessments(control_id, assessment_date);
CREATE INDEX IF NOT EXISTS idx_assessments_status ON compliance_assessments(compliance_status);
CREATE INDEX IF NOT EXISTS idx_risk_scores_control ON control_risk_scores(control_id);
CREATE INDEX IF NOT EXISTS idx_risk_scores_priority ON control_risk_scores(priority_score);
CREATE INDEX IF NOT EXISTS idx_remediation_control ON remediation_actions(control_id);
CREATE INDEX IF NOT EXISTS idx_cve_mapping_control ON cve_control_mapping(control_id);
CREATE INDEX IF NOT EXISTS idx_attack_mapping_control ON attack_control_mapping(control_id);
"""
            
        try:
            conn.executescript(schema_sql)
            logger.info("Schema initialized successfully.")
        except sqlite3.Error as e:
            logger.error(f"Error initializing schema: {e}")
            sys.exit(1)
            
    # Check if controls exist, if not, seed them
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) as count FROM nist_controls")
    if cursor.fetchone()['count'] == 0:
        logger.info("Seeding NIST controls...")
        # Seed some sample controls for the demo
        families = [
            ('AC', 'Access Control'), ('AU', 'Audit and Accountability'), 
            ('IA', 'Identification and Authentication'), ('SC', 'System and Communications Protection'),
            ('SI', 'System and Information Integrity'), ('CM', 'Configuration Management'),
            ('CP', 'Contingency Planning'), ('IR', 'Incident Response')
        ]
        
        controls_to_insert = []
        for fam_id, fam_name in families:
            for i in range(1, 6):
                controls_to_insert.append((
                    f"{fam_id}-{i}", fam_name, f"{fam_name} Control {i}", 
                    f"Description for {fam_name} Control {i}"
                ))
                
        cursor.executemany('''
            INSERT INTO nist_controls (control_id, control_family, control_name, control_description)
            VALUES (?, ?, ?, ?)
        ''', controls_to_insert)
        conn.commit()
        logger.info(f"Seeded {len(controls_to_insert)} controls.")
    
    try:
        # Get controls
        logger.info("\nFetching controls from database...")
        controls = get_controls_from_db(conn)
        logger.info(f"Found {len(controls)} controls")
        
        # Generate compliance assessments
        logger.info(f"\nGenerating {ASSESSMENT_MONTHS} months of assessment data...")
        assessments_created = generate_compliance_assessments(conn, controls)
        
        # Calculate risk scores
        logger.info("\nCalculating risk scores...")
        risk_scores_created = calculate_risk_scores(conn, controls)
        
        # Generate remediation actions
        logger.info("\nGenerating remediation actions...")
        remediation_actions_created = generate_remediation_actions(conn)
        
        # Generate statistics
        logger.info("\nGenerating statistics...")
        stats = generate_statistics(conn)
        
        # Print summary
        logger.info("\n" + "=" * 70)
        logger.info("DATA GENERATION COMPLETE")
        logger.info("=" * 70)
        logger.info(f"Total Controls: {stats['total_controls']}")
        logger.info(f"Total Assessments: {stats['total_assessments']}")
        logger.info(f"Risk Scores Calculated: {stats['risk_scores_calculated']}")
        logger.info(f"Remediation Actions: {stats['remediation_actions']}")
        logger.info(f"\nCurrent Compliance Status:")
        for status, count in stats['status_distribution'].items():
            logger.info(f"  {status}: {count}")
        logger.info(f"\nOverall Compliance: {stats['compliance_percentage']}%")
        logger.info(f"High-Risk Controls: {stats['high_risk_controls']}")
        logger.info("=" * 70)
        
    except Exception as e:
        logger.error(f"Error generating mock data: {e}", exc_info=True)
        sys.exit(1)
    finally:
        conn.close()


if __name__ == '__main__':
    main()
