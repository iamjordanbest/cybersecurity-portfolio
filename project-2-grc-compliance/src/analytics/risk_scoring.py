#!/usr/bin/env python3
"""
Risk Scoring Engine

Calculates risk scores for controls based on:
- Compliance status and implementation
- Threat intelligence (KEV, MITRE ATT&CK)
- Control criticality and business impact
- Staleness and overdue remediations
"""

import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import yaml
import logging

logger = logging.getLogger(__name__)


class RiskScoringEngine:
    """Risk scoring engine for GRC compliance controls."""
    
    def __init__(self, db_path: str, config_path: Optional[str] = None):
        """
        Initialize the risk scoring engine.
        
        Args:
            db_path: Path to SQLite database
            config_path: Optional path to scoring configuration YAML
        """
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        
        # Load scoring configuration
        if config_path is None:
            project_root = Path(db_path).parent.parent.parent
            config_path = project_root / 'config' / 'scoring.yaml'
        
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        self.scoring = self.config['scoring']
    
    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
    
    def calculate_control_risk_score(self, control_id: str) -> Dict:
        """
        Calculate comprehensive risk score for a single control.
        
        Args:
            control_id: NIST control identifier
            
        Returns:
            Dictionary containing all risk score components
        """
        cursor = self.conn.cursor()
        
        # Get latest assessment
        cursor.execute('''
            SELECT *
            FROM compliance_assessments
            WHERE control_id = ?
            ORDER BY assessment_date DESC
            LIMIT 1
        ''', (control_id,))
        
        assessment = cursor.fetchone()
        
        if not assessment:
            return {
                'control_id': control_id,
                'error': 'No assessment found',
                'base_risk_score': 0,
                'threat_adjusted_score': 0,
                'priority_score': 0
            }
        
        # Get control info
        cursor.execute('''
            SELECT control_family, control_name
            FROM nist_controls
            WHERE control_id = ?
        ''', (control_id,))
        
        control_info = cursor.fetchone()
        
        # Calculate base risk score
        base_risk = self._calculate_base_risk(assessment)
        
        # Get threat intelligence counts
        threat_data = self._get_threat_intelligence(control_id)
        
        # Calculate threat-adjusted score
        threat_adjusted = self._calculate_threat_adjusted_risk(base_risk, threat_data)
        
        # Calculate staleness factor
        staleness_factor = self._calculate_staleness_factor(assessment)
        
        # Apply staleness
        staleness_adjusted = threat_adjusted * staleness_factor
        
        # Calculate priority score
        priority_score = self._calculate_priority_score(
            staleness_adjusted, threat_data, assessment
        )
        
        return {
            'control_id': control_id,
            'control_family': control_info['control_family'],
            'control_name': control_info['control_name'],
            'base_risk_score': round(base_risk, 2),
            'threat_adjusted_score': round(threat_adjusted, 2),
            'staleness_adjusted_score': round(staleness_adjusted, 2),
            'priority_score': round(priority_score, 2),
            'staleness_factor': round(staleness_factor, 2),
            'kev_cve_count': threat_data['kev_count'],
            'attack_technique_count': threat_data['attack_count'],
            'overdue_kev_count': threat_data['overdue_kev'],
            'ransomware_related_count': threat_data['ransomware_count'],
            'compliance_status': assessment['compliance_status'],
            'risk_rating': assessment['risk_rating'],
            'assessment_date': assessment['assessment_date']
        }
    
    def _calculate_base_risk(self, assessment: sqlite3.Row) -> float:
        """Calculate base risk score from assessment status."""
        status = assessment['compliance_status']
        risk_rating = assessment['risk_rating']
        
        # Status multiplier
        status_multiplier = self.scoring['status_multipliers'].get(status, 1.0)
        
        # Risk rating base weight
        risk_weights = {
            'critical': 10.0,
            'high': 7.5,
            'medium': 5.0,
            'low': 2.5
        }
        risk_weight = risk_weights.get(risk_rating, 5.0)
        
        # Calculate base risk
        base_risk = status_multiplier * risk_weight
        
        return min(base_risk, 100.0)  # Cap at 100
    
    def _get_threat_intelligence(self, control_id: str) -> Dict:
        """Get threat intelligence metrics for a control."""
        cursor = self.conn.cursor()
        
        # Get KEV count
        cursor.execute('''
            SELECT COUNT(*) as count
            FROM cve_control_mapping
            WHERE control_id = ?
        ''', (control_id,))
        kev_count = cursor.fetchone()['count']
        
        # Get ATT&CK count
        cursor.execute('''
            SELECT COUNT(*) as count
            FROM attack_control_mapping
            WHERE control_id = ?
        ''', (control_id,))
        attack_count = cursor.fetchone()['count']
        
        # Get overdue KEV count
        cursor.execute('''
            SELECT COUNT(*) as count
            FROM cve_control_mapping ccm
            JOIN cisa_kev ck ON ccm.cve_id = ck.cve_id
            WHERE ccm.control_id = ? AND ck.due_date < date('now')
        ''', (control_id,))
        overdue_kev = cursor.fetchone()['count']
        
        # Get ransomware-related KEV count
        cursor.execute('''
            SELECT COUNT(*) as count
            FROM cve_control_mapping ccm
            JOIN cisa_kev ck ON ccm.cve_id = ck.cve_id
            WHERE ccm.control_id = ? AND ck.known_ransomware_use = 1
        ''', (control_id,))
        ransomware_count = cursor.fetchone()['count']
        
        return {
            'kev_count': kev_count,
            'attack_count': attack_count,
            'overdue_kev': overdue_kev,
            'ransomware_count': ransomware_count
        }
    
    def _calculate_threat_adjusted_risk(self, base_risk: float, threat_data: Dict) -> float:
        """Adjust risk score based on threat intelligence."""
        # Threat multiplier based on KEV and ATT&CK mappings
        kev_factor = 1.0 + (threat_data['kev_count'] * 0.05)  # 5% increase per KEV
        attack_factor = 1.0 + (threat_data['attack_count'] * 0.005)  # 0.5% increase per technique
        
        # Combined threat factor (capped at 3x)
        threat_factor = min(kev_factor * attack_factor, 3.0)
        
        # Apply threat adjustment
        threat_adjusted = base_risk * threat_factor
        
        return min(threat_adjusted, 100.0)
    
    def _calculate_staleness_factor(self, assessment: sqlite3.Row) -> float:
        """Calculate staleness factor based on assessment age."""
        if not self.scoring['staleness']['enabled']:
            return 1.0
        
        assessment_date = datetime.strptime(assessment['assessment_date'], '%Y-%m-%d')
        days_old = (datetime.now() - assessment_date).days
        
        # If compliant and recently assessed, no staleness penalty
        if assessment['compliance_status'] == 'compliant' and days_old < 90:
            return 1.0
        
        # Calculate staleness factor
        base_factor = self.scoring['staleness']['base_factor']
        daily_penalty = self.scoring['staleness']['daily_penalty']
        max_factor = self.scoring['staleness']['max_factor']
        
        staleness = base_factor + (days_old * daily_penalty)
        
        return min(staleness, max_factor)
    
    def _calculate_priority_score(self, base_score: float, threat_data: Dict, 
                                   assessment: sqlite3.Row) -> float:
        """
        Calculate final priority score for remediation.
        
        Higher scores = higher priority for remediation
        """
        # Start with staleness-adjusted risk
        priority = base_score
        
        # Add urgency for overdue KEVs
        priority += threat_data['overdue_kev'] * 5.0
        
        # Add urgency for ransomware
        priority += threat_data['ransomware_count'] * 3.0
        
        # Add urgency based on target date
        if assessment['target_date']:
            target_date = datetime.strptime(assessment['target_date'], '%Y-%m-%d')
            days_until_due = (target_date - datetime.now()).days
            
            if days_until_due < 0:
                # Overdue - increase priority
                priority += min(abs(days_until_due) * 0.5, 20.0)
            elif days_until_due < 30:
                # Due soon - moderate increase
                priority += (30 - days_until_due) * 0.3
        
        return min(priority, 100.0)
    
    def calculate_all_risk_scores(self, recalculate: bool = False) -> Dict:
        """
        Calculate risk scores for all controls.
        
        Args:
            recalculate: If True, recalculate even if scores exist
            
        Returns:
            Dictionary with statistics about calculated scores
        """
        cursor = self.conn.cursor()
        
        # Get all controls
        cursor.execute('SELECT control_id FROM nist_controls')
        controls = cursor.fetchall()
        
        logger.info(f"Calculating risk scores for {len(controls)} controls...")
        
        scores_calculated = 0
        scores_updated = 0
        high_risk_count = 0
        
        for control in controls:
            control_id = control['control_id']
            
            # Calculate score
            score_data = self.calculate_control_risk_score(control_id)
            
            if 'error' in score_data:
                continue
            
            # Check if score already exists
            cursor.execute('''
                SELECT id FROM control_risk_scores
                WHERE control_id = ?
                ORDER BY calculation_date DESC
                LIMIT 1
            ''', (control_id,))
            
            existing = cursor.fetchone()
            
            if existing and not recalculate:
                scores_updated += 1
                cursor.execute('''
                    UPDATE control_risk_scores
                    SET base_risk_score = ?,
                        threat_adjusted_score = ?,
                        kev_cve_count = ?,
                        attack_technique_count = ?,
                        overdue_kev_count = ?,
                        ransomware_related_count = ?,
                        priority_score = ?,
                        calculation_date = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', (
                    score_data['base_risk_score'],
                    score_data['threat_adjusted_score'],
                    score_data['kev_cve_count'],
                    score_data['attack_technique_count'],
                    score_data['overdue_kev_count'],
                    score_data['ransomware_related_count'],
                    score_data['priority_score'],
                    existing['id']
                ))
            else:
                scores_calculated += 1
                cursor.execute('''
                    INSERT INTO control_risk_scores (
                        control_id, calculation_date, base_risk_score,
                        threat_adjusted_score, kev_cve_count, attack_technique_count,
                        overdue_kev_count, ransomware_related_count, priority_score,
                        created_at
                    ) VALUES (?, CURRENT_TIMESTAMP, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ''', (
                    control_id,
                    score_data['base_risk_score'],
                    score_data['threat_adjusted_score'],
                    score_data['kev_cve_count'],
                    score_data['attack_technique_count'],
                    score_data['overdue_kev_count'],
                    score_data['ransomware_related_count'],
                    score_data['priority_score']
                ))
            
            if score_data['priority_score'] > 50:
                high_risk_count += 1
        
        self.conn.commit()
        
        return {
            'total_controls': len(controls),
            'scores_calculated': scores_calculated,
            'scores_updated': scores_updated,
            'high_risk_controls': high_risk_count
        }
    
    def get_high_risk_controls(self, threshold: float = 50.0, limit: int = 20) -> List[Dict]:
        """
        Get controls with highest risk/priority scores.
        
        Args:
            threshold: Minimum priority score threshold
            limit: Maximum number of controls to return
            
        Returns:
            List of high-risk control dictionaries
        """
        cursor = self.conn.cursor()
        
        cursor.execute('''
            SELECT 
                crs.control_id,
                nc.control_name,
                nc.control_family,
                crs.priority_score,
                crs.threat_adjusted_score,
                crs.kev_cve_count,
                crs.attack_technique_count,
                crs.overdue_kev_count,
                crs.ransomware_related_count,
                ca.compliance_status,
                ca.risk_rating,
                ca.target_date
            FROM control_risk_scores crs
            JOIN nist_controls nc ON crs.control_id = nc.control_id
            LEFT JOIN compliance_assessments ca ON crs.control_id = ca.control_id
            WHERE crs.priority_score >= ?
            AND ca.assessment_id IN (
                SELECT assessment_id
                FROM compliance_assessments ca2
                WHERE ca2.control_id = ca.control_id
                ORDER BY ca2.assessment_date DESC
                LIMIT 1
            )
            ORDER BY crs.priority_score DESC
            LIMIT ?
        ''', (threshold, limit))
        
        results = []
        for row in cursor.fetchall():
            results.append(dict(row))
        
        return results
    
    def get_risk_score_summary(self) -> Dict:
        """Get summary statistics of risk scores."""
        cursor = self.conn.cursor()
        
        cursor.execute('''
            SELECT 
                COUNT(*) as total,
                AVG(priority_score) as avg_priority,
                AVG(threat_adjusted_score) as avg_threat_risk,
                SUM(CASE WHEN priority_score >= 75 THEN 1 ELSE 0 END) as critical_count,
                SUM(CASE WHEN priority_score >= 50 AND priority_score < 75 THEN 1 ELSE 0 END) as high_count,
                SUM(CASE WHEN priority_score >= 25 AND priority_score < 50 THEN 1 ELSE 0 END) as medium_count,
                SUM(CASE WHEN priority_score < 25 THEN 1 ELSE 0 END) as low_count
            FROM control_risk_scores
        ''')
        
        row = cursor.fetchone()
        
        return {
            'total_controls': row['total'],
            'average_priority_score': round(row['avg_priority'], 2),
            'average_threat_risk': round(row['avg_threat_risk'], 2),
            'critical_risk_controls': row['critical_count'],
            'high_risk_controls': row['high_count'],
            'medium_risk_controls': row['medium_count'],
            'low_risk_controls': row['low_count']
        }
