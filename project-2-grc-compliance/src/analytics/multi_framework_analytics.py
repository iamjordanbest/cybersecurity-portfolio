#!/usr/bin/env python3
"""
Multi-Framework Analytics Engine

Extends analytics capabilities to work across all compliance frameworks.
Provides unified risk scoring, compliance tracking, and ROI calculations
for multiple frameworks simultaneously.
"""

import sqlite3
from typing import Dict, List, Optional
from datetime import datetime
from pathlib import Path
import logging

from src.analytics.framework_mapper import FrameworkMapper

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MultiFrameworkAnalytics:
    """
    Analytics engine for multi-framework compliance.
    
    Provides risk scoring, compliance calculations, and ROI analysis
    across multiple compliance frameworks.
    """
    
    def __init__(self, db_path: str):
        """
        Initialize multi-framework analytics.
        
        Args:
            db_path: Path to GRC analytics database
        """
        self.db_path = db_path
        self.conn = None
        self.mapper = None
        
    def connect(self):
        """Connect to database."""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self.mapper = FrameworkMapper(self.db_path)
        self.mapper.connect()
        
    def close(self):
        """Close database connections."""
        if self.conn:
            self.conn.close()
        if self.mapper:
            self.mapper.close()
    
    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
    
    def get_unified_compliance_status(self) -> Dict:
        """
        Get unified compliance status across all frameworks.
        
        Returns:
            Dictionary with compliance status for each framework
        """
        cursor = self.conn.cursor()
        
        cursor.execute('''
            SELECT 
                f.framework_code,
                f.framework_name,
                COUNT(DISTINCT fc.control_identifier) as total_controls,
                COUNT(DISTINCT CASE 
                    WHEN mfa.compliance_status = 'compliant' 
                    THEN fc.control_identifier 
                END) as compliant,
                COUNT(DISTINCT CASE 
                    WHEN mfa.compliance_status = 'partially_compliant' 
                    THEN fc.control_identifier 
                END) as partial,
                COUNT(DISTINCT CASE 
                    WHEN mfa.compliance_status = 'non_compliant' 
                    THEN fc.control_identifier 
                END) as non_compliant,
                COUNT(DISTINCT CASE 
                    WHEN mfa.compliance_status IN ('not_assessed', 'not_applicable') 
                        OR mfa.compliance_status IS NULL
                    THEN fc.control_identifier 
                END) as not_assessed
            FROM frameworks f
            JOIN framework_controls fc ON f.framework_id = fc.framework_id
            LEFT JOIN mf_compliance_assessments mfa ON f.framework_id = mfa.framework_id
                AND fc.control_identifier = mfa.control_identifier
                AND mfa.assessment_id IN (
                    SELECT assessment_id
                    FROM mf_compliance_assessments mfa2
                    WHERE mfa2.framework_id = mfa.framework_id
                    AND mfa2.control_identifier = mfa.control_identifier
                    ORDER BY mfa2.assessment_date DESC
                    LIMIT 1
                )
            WHERE f.is_active = 1
            GROUP BY f.framework_id
            ORDER BY f.framework_code
        ''')
        
        results = {}
        for row in cursor.fetchall():
            code = row['framework_code']
            total = row['total_controls']
            compliant = row['compliant']
            
            compliance_pct = (compliant / total * 100) if total > 0 else 0
            
            results[code] = {
                'framework_name': row['framework_name'],
                'total_controls': total,
                'compliant': compliant,
                'partial': row['partial'],
                'non_compliant': row['non_compliant'],
                'not_assessed': row['not_assessed'],
                'compliance_percentage': round(compliance_pct, 2)
            }
        
        return results
    
    def calculate_inherited_compliance(self, framework: str) -> Dict:
        """
        Calculate compliance inherited from mapped frameworks.
        
        Args:
            framework: Target framework code
            
        Returns:
            Dictionary with inherited compliance information
        """
        cursor = self.conn.cursor()
        
        # Get framework ID
        cursor.execute("SELECT framework_id FROM frameworks WHERE framework_code = ?",
                      (framework,))
        fw_result = cursor.fetchone()
        if not fw_result:
            return {}
        
        fw_id = fw_result[0]
        
        # Get controls that have inbound mappings
        cursor.execute('''
            SELECT 
                cm.target_control_id as control_id,
                cm.mapping_type,
                cm.mapping_strength,
                sf.framework_code as source_framework,
                cm.source_control_id,
                mfa.compliance_status as source_compliance
            FROM control_mappings cm
            JOIN frameworks sf ON cm.source_framework_id = sf.framework_id
            LEFT JOIN mf_compliance_assessments mfa ON cm.source_framework_id = mfa.framework_id
                AND cm.source_control_id = mfa.control_identifier
                AND mfa.assessment_id IN (
                    SELECT assessment_id
                    FROM mf_compliance_assessments mfa2
                    WHERE mfa2.framework_id = mfa.framework_id
                    AND mfa2.control_identifier = mfa.control_identifier
                    ORDER BY mfa2.assessment_date DESC
                    LIMIT 1
                )
            WHERE cm.target_framework_id = ?
            AND mfa.compliance_status = 'compliant'
        ''', (fw_id,))
        
        inherited = {}
        for row in cursor.fetchall():
            control_id = row['control_id']
            
            if control_id not in inherited:
                inherited[control_id] = []
            
            inherited[control_id].append({
                'source_framework': row['source_framework'],
                'source_control': row['source_control_id'],
                'mapping_type': row['mapping_type'],
                'mapping_strength': row['mapping_strength'],
                'inherited_compliance': row['mapping_strength'] * 100
            })
        
        return inherited
    
    def get_multi_framework_risk_summary(self) -> Dict:
        """
        Get risk summary across all frameworks.
        
        Returns:
            Dictionary with risk metrics for each framework
        """
        cursor = self.conn.cursor()
        
        cursor.execute('''
            SELECT 
                f.framework_code,
                COUNT(*) as total_scored,
                AVG(mrs.priority_score) as avg_priority,
                SUM(CASE WHEN mrs.priority_score >= 75 THEN 1 ELSE 0 END) as critical,
                SUM(CASE WHEN mrs.priority_score >= 50 AND mrs.priority_score < 75 THEN 1 ELSE 0 END) as high,
                SUM(CASE WHEN mrs.priority_score >= 25 AND mrs.priority_score < 50 THEN 1 ELSE 0 END) as medium,
                SUM(CASE WHEN mrs.priority_score < 25 THEN 1 ELSE 0 END) as low,
                SUM(mrs.kev_cve_count) as total_kevs,
                SUM(mrs.attack_technique_count) as total_attack_techniques
            FROM frameworks f
            LEFT JOIN mf_control_risk_scores mrs ON f.framework_id = mrs.framework_id
            WHERE f.is_active = 1
            GROUP BY f.framework_id
            ORDER BY f.framework_code
        ''')
        
        results = {}
        for row in cursor.fetchall():
            code = row['framework_code']
            
            results[code] = {
                'total_scored': row['total_scored'] or 0,
                'avg_priority_score': round(row['avg_priority'] or 0, 2),
                'critical_risk': row['critical'] or 0,
                'high_risk': row['high'] or 0,
                'medium_risk': row['medium'] or 0,
                'low_risk': row['low'] or 0,
                'total_kevs': row['total_kevs'] or 0,
                'total_attack_techniques': row['total_attack_techniques'] or 0
            }
        
        return results
    
    def get_framework_comparison(self, frameworks: List[str]) -> Dict:
        """
        Compare multiple frameworks side-by-side.
        
        Args:
            frameworks: List of framework codes to compare
            
        Returns:
            Dictionary with comparison metrics
        """
        comparison = {
            'frameworks': frameworks,
            'metrics': {}
        }
        
        compliance_status = self.get_unified_compliance_status()
        risk_summary = self.get_multi_framework_risk_summary()
        
        for fw in frameworks:
            if fw in compliance_status:
                comparison['metrics'][fw] = {
                    'compliance': compliance_status[fw],
                    'risk': risk_summary.get(fw, {})
                }
        
        # Add cross-framework coverage
        for i, source_fw in enumerate(frameworks):
            for target_fw in frameworks[i+1:]:
                coverage = self.mapper.get_framework_coverage(source_fw, target_fw)
                key = f"{source_fw}_to_{target_fw}"
                comparison['metrics'][key] = {
                    'type': 'coverage',
                    'source_coverage': coverage['source_coverage_pct'],
                    'target_coverage': coverage['target_coverage_pct'],
                    'total_mappings': coverage['total_mappings']
                }
        
        return comparison
    
    def get_priority_controls_across_frameworks(self, min_priority: float = 50.0,
                                               limit: int = 20) -> List[Dict]:
        """
        Get highest priority controls across all frameworks.
        
        Args:
            min_priority: Minimum priority score threshold
            limit: Maximum number of controls to return
            
        Returns:
            List of high-priority controls from all frameworks
        """
        cursor = self.conn.cursor()
        
        cursor.execute('''
            SELECT 
                f.framework_code,
                fc.control_identifier,
                fc.control_name,
                fc.control_category,
                fc.priority_level,
                mrs.priority_score,
                mrs.kev_cve_count,
                mrs.attack_technique_count,
                mfa.compliance_status,
                mfa.risk_rating
            FROM mf_control_risk_scores mrs
            JOIN frameworks f ON mrs.framework_id = f.framework_id
            JOIN framework_controls fc ON mrs.framework_id = fc.framework_id 
                AND mrs.control_identifier = fc.control_identifier
            LEFT JOIN mf_compliance_assessments mfa ON mrs.framework_id = mfa.framework_id
                AND mrs.control_identifier = mfa.control_identifier
                AND mfa.assessment_id IN (
                    SELECT assessment_id
                    FROM mf_compliance_assessments mfa2
                    WHERE mfa2.framework_id = mfa.framework_id
                    AND mfa2.control_identifier = mfa.control_identifier
                    ORDER BY mfa2.assessment_date DESC
                    LIMIT 1
                )
            WHERE mrs.priority_score >= ?
            AND f.is_active = 1
            ORDER BY mrs.priority_score DESC, f.framework_code, fc.control_identifier
            LIMIT ?
        ''', (min_priority, limit))
        
        results = []
        for row in cursor.fetchall():
            results.append({
                'framework': row['framework_code'],
                'control_id': row['control_identifier'],
                'control_name': row['control_name'],
                'category': row['control_category'],
                'priority_level': row['priority_level'],
                'priority_score': row['priority_score'],
                'kev_count': row['kev_cve_count'],
                'attack_techniques': row['attack_technique_count'],
                'compliance_status': row['compliance_status'] or 'not_assessed',
                'risk_rating': row['risk_rating'] or 'medium'
            })
        
        return results
    
    def calculate_multi_framework_roi(self, frameworks: List[str]) -> Dict:
        """
        Calculate ROI for implementing multiple frameworks simultaneously.
        
        Args:
            frameworks: List of framework codes
            
        Returns:
            Dictionary with ROI calculations
        """
        cursor = self.conn.cursor()
        
        # Base cost per control assessment
        cost_per_control = 1000  # $1,000 per control assessment
        
        roi_data = {
            'frameworks': frameworks,
            'individual_costs': {},
            'combined_cost': 0,
            'savings': 0,
            'roi_percentage': 0
        }
        
        total_individual_cost = 0
        unique_controls = set()
        
        for fw in frameworks:
            # Get control count
            cursor.execute('''
                SELECT COUNT(*) FROM framework_controls fc
                JOIN frameworks f ON fc.framework_id = f.framework_id
                WHERE f.framework_code = ?
            ''', (fw,))
            
            count = cursor.fetchone()[0]
            cost = count * cost_per_control
            
            roi_data['individual_costs'][fw] = {
                'controls': count,
                'cost': cost
            }
            
            total_individual_cost += cost
            
            # Track unique controls
            cursor.execute('''
                SELECT control_identifier FROM framework_controls fc
                JOIN frameworks f ON fc.framework_id = f.framework_id
                WHERE f.framework_code = ?
            ''', (fw,))
            
            for row in cursor.fetchall():
                unique_controls.add((fw, row[0]))
        
        # Calculate combined cost with mapping benefits
        # For controls that map to each other, only assess once
        mapped_pairs = set()
        for i, source_fw in enumerate(frameworks):
            for target_fw in frameworks[i+1:]:
                coverage = self.mapper.get_framework_coverage(source_fw, target_fw)
                # Add benefit of mapped controls (70% cost reduction)
                mapped_pairs.add((source_fw, target_fw))
        
        # Simplified calculation: assume 20% savings through mapping synergies
        combined_cost = total_individual_cost * 0.8
        savings = total_individual_cost - combined_cost
        roi_percentage = (savings / total_individual_cost * 100) if total_individual_cost > 0 else 0
        
        roi_data['combined_cost'] = combined_cost
        roi_data['total_individual_cost'] = total_individual_cost
        roi_data['savings'] = savings
        roi_data['roi_percentage'] = round(roi_percentage, 2)
        
        return roi_data
    
    def get_compliance_gaps_across_frameworks(self) -> Dict:
        """
        Identify compliance gaps across all frameworks.
        
        Returns:
            Dictionary with gap analysis for each framework
        """
        cursor = self.conn.cursor()
        
        gaps = {}
        
        cursor.execute("SELECT framework_code FROM frameworks WHERE is_active = 1")
        frameworks = [row[0] for row in cursor.fetchall()]
        
        for fw in frameworks:
            cursor.execute('''
                SELECT 
                    fc.control_identifier,
                    fc.control_name,
                    fc.priority_level,
                    mfa.compliance_status
                FROM framework_controls fc
                JOIN frameworks f ON fc.framework_id = f.framework_id
                LEFT JOIN mf_compliance_assessments mfa ON fc.framework_id = mfa.framework_id
                    AND fc.control_identifier = mfa.control_identifier
                    AND mfa.assessment_id IN (
                        SELECT assessment_id
                        FROM mf_compliance_assessments mfa2
                        WHERE mfa2.framework_id = mfa.framework_id
                        AND mfa2.control_identifier = mfa.control_identifier
                        ORDER BY mfa2.assessment_date DESC
                        LIMIT 1
                    )
                WHERE f.framework_code = ?
                AND (mfa.compliance_status IN ('non_compliant', 'partially_compliant', 'not_assessed')
                     OR mfa.compliance_status IS NULL)
                AND fc.priority_level IN ('critical', 'high')
                ORDER BY 
                    CASE fc.priority_level
                        WHEN 'critical' THEN 1
                        WHEN 'high' THEN 2
                    END,
                    fc.control_identifier
            ''', (fw,))
            
            framework_gaps = []
            for row in cursor.fetchall():
                framework_gaps.append({
                    'control_id': row['control_identifier'],
                    'control_name': row['control_name'],
                    'priority': row['priority_level'],
                    'status': row['compliance_status'] or 'not_assessed'
                })
            
            gaps[fw] = {
                'total_gaps': len(framework_gaps),
                'gaps': framework_gaps[:10]  # Top 10 gaps
            }
        
        return gaps


def main():
    """Example usage."""
    db_path = Path(__file__).parent.parent.parent / 'data' / 'processed' / 'grc_analytics.db'
    
    with MultiFrameworkAnalytics(str(db_path)) as analytics:
        # Get unified compliance status
        compliance = analytics.get_unified_compliance_status()
        print("\nUnified Compliance Status:")
        for fw, status in compliance.items():
            print(f"  {fw}: {status['compliance_percentage']}% compliant")
        
        # Get risk summary
        risk = analytics.get_multi_framework_risk_summary()
        print("\nRisk Summary:")
        for fw, metrics in risk.items():
            print(f"  {fw}: {metrics['critical_risk']} critical, {metrics['high_risk']} high")
        
        # Get priority controls
        priorities = analytics.get_priority_controls_across_frameworks(min_priority=50.0, limit=5)
        print(f"\nTop 5 Priority Controls:")
        for ctrl in priorities:
            print(f"  {ctrl['framework']} {ctrl['control_id']}: {ctrl['priority_score']:.2f}")


if __name__ == '__main__':
    main()
