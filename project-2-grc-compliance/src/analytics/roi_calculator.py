#!/usr/bin/env python3
"""
ROI Calculator Module

Calculates return on investment for security controls and remediation:
- Risk reduction value (RALE method)
- Remediation costs
- Net ROI and payback period
- Breach cost modeling
"""

import sqlite3
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path
import yaml
import logging

logger = logging.getLogger(__name__)


class ROICalculator:
    """ROI calculator for security control investments."""
    
    def __init__(self, db_path: str, config_path: Optional[str] = None):
        """
        Initialize the ROI calculator.
        
        Args:
            db_path: Path to SQLite database
            config_path: Optional path to ROI configuration YAML
        """
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        
        # Load ROI configuration
        if config_path is None:
            project_root = Path(db_path).parent.parent.parent
            config_path = project_root / 'config' / 'roi_parameters.yaml'
        
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        self.cost_models = self.config['cost_models']
        self.roi_calc = self.config['roi_calculation']
    
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
    
    def calculate_breach_probability(self, control_failures: Dict) -> float:
        """
        Calculate breach probability based on control failures.
        
        Args:
            control_failures: Dictionary of control family failures
            
        Returns:
            Annual breach probability (0-1)
        """
        base_prob = self.cost_models['breach_probability']['base_probability']
        family_multipliers = self.cost_models['breach_probability']['family_multipliers']
        
        # Apply multipliers for failed control families
        total_multiplier = 1.0
        for family, failure_count in control_failures.items():
            if failure_count > 0 and family in family_multipliers:
                # Each failure increases risk
                multiplier = family_multipliers[family]
                total_multiplier *= (1 + (multiplier - 1) * min(failure_count / 10, 1.0))
        
        # Calculate adjusted probability
        adjusted_prob = base_prob * total_multiplier
        
        return min(adjusted_prob, 1.0)  # Cap at 100%
    
    def calculate_expected_breach_cost(self, industry: str = 'technology') -> float:
        """
        Calculate expected breach cost based on industry.
        
        Args:
            industry: Industry type
            
        Returns:
            Expected breach cost in USD
        """
        base_cost = self.cost_models['breach_costs']['base_cost']
        industry_multipliers = self.cost_models['breach_costs']['industry_multipliers']
        
        multiplier = industry_multipliers.get(industry, 1.0)
        
        return base_cost * multiplier
    
    def calculate_remediation_cost(self, control_id: str) -> Dict:
        """
        Calculate remediation cost for a specific control.
        
        Args:
            control_id: NIST control identifier
            
        Returns:
            Dictionary with cost breakdown
        """
        cursor = self.conn.cursor()
        
        # Get remediation action for this control
        cursor.execute('''
            SELECT *
            FROM remediation_actions
            WHERE control_id = ?
            ORDER BY created_at DESC
            LIMIT 1
        ''', (control_id,))
        
        action = cursor.fetchone()
        
        if action and action['estimated_cost']:
            return {
                'control_id': control_id,
                'estimated_cost': action['estimated_cost'],
                'actual_cost': action['actual_cost'],
                'source': 'database'
            }
        
        # Estimate based on control complexity
        # Get control's risk rating as proxy for complexity
        cursor.execute('''
            SELECT risk_rating
            FROM compliance_assessments
            WHERE control_id = ?
            ORDER BY assessment_date DESC
            LIMIT 1
        ''', (control_id,))
        
        assessment = cursor.fetchone()
        
        if not assessment:
            return {
                'control_id': control_id,
                'estimated_cost': 5000,  # Default estimate
                'source': 'default'
            }
        
        risk_rating = assessment['risk_rating']
        
        # Estimate based on risk/complexity
        hourly_rate = self.cost_models['remediation']['hourly_rate']
        effort_hours = self.cost_models['remediation']['effort_hours']
        
        complexity_map = {
            'critical': 'high',
            'high': 'high',
            'medium': 'medium',
            'low': 'low'
        }
        
        complexity = complexity_map.get(risk_rating, 'medium')
        hours = effort_hours[complexity]
        estimated_cost = hours * hourly_rate
        
        return {
            'control_id': control_id,
            'estimated_cost': estimated_cost,
            'effort_hours': hours,
            'hourly_rate': hourly_rate,
            'complexity': complexity,
            'source': 'estimated'
        }
    
    def calculate_control_roi(self, control_id: str, industry: str = 'technology',
                              analysis_years: int = 3) -> Dict:
        """
        Calculate ROI for remediating a specific control.
        
        Args:
            control_id: NIST control identifier
            industry: Industry type for cost modeling
            analysis_years: Number of years for NPV calculation
            
        Returns:
            Dictionary with ROI metrics
        """
        cursor = self.conn.cursor()
        
        # Get control info
        cursor.execute('''
            SELECT nc.control_id, nc.control_family, nc.control_name,
                   ca.compliance_status, ca.risk_rating,
                   crs.priority_score, crs.kev_cve_count
            FROM nist_controls nc
            LEFT JOIN compliance_assessments ca ON nc.control_id = ca.control_id
            LEFT JOIN control_risk_scores crs ON nc.control_id = crs.control_id
            WHERE nc.control_id = ?
            AND ca.assessment_id = (
                SELECT assessment_id FROM compliance_assessments ca2
                WHERE ca2.control_id = nc.control_id
                ORDER BY assessment_date DESC LIMIT 1
            )
        ''', (control_id,))
        
        control = cursor.fetchone()
        
        if not control:
            return {'error': 'Control not found'}
        
        # If already compliant, no ROI to calculate
        if control['compliance_status'] == 'compliant':
            return {
                'control_id': control_id,
                'control_name': control['control_name'],
                'status': 'already_compliant',
                'roi': 0,
                'message': 'Control is already compliant'
            }
        
        # Calculate breach costs
        breach_cost = self.calculate_expected_breach_cost(industry)
        
        # Map full family name to abbreviation for config lookup
        family_mapping = {
            'Access Control': 'AC',
            'Audit and Accountability': 'AU',
            'Identification and Authentication': 'IA',
            'System and Communications Protection': 'SC',
            'System and Information Integrity': 'SI',
            'Configuration Management': 'CM',
            'Contingency Planning': 'CP',
            'Incident Response': 'IR',
            'Risk Assessment': 'RA'
        }
        
        family = control['control_family']
        family_abbrev = family_mapping.get(family, family[:2].upper())
        
        # Calculate breach probability before (with current failures)
        cursor.execute('''
            SELECT COUNT(*) as failure_count
            FROM compliance_assessments ca
            JOIN nist_controls nc ON ca.control_id = nc.control_id
            WHERE nc.control_family = ?
            AND ca.compliance_status IN ('non_compliant', 'partial')
            AND ca.assessment_id IN (
                SELECT assessment_id FROM compliance_assessments ca2
                WHERE ca2.control_id = ca.control_id
                ORDER BY assessment_date DESC LIMIT 1
            )
        ''', (family,))
        
        current_failures = cursor.fetchone()['failure_count']
        
        control_failures_before = {family_abbrev: current_failures}
        prob_before = self.calculate_breach_probability(control_failures_before)
        
        # Calculate breach probability after (one fewer failure)
        control_failures_after = {family_abbrev: max(0, current_failures - 1)}
        prob_after = self.calculate_breach_probability(control_failures_after)
        
        # Risk reduction value (RALE method)
        risk_reduction_annual = (prob_before - prob_after) * breach_cost
        risk_reduction_total = risk_reduction_annual * analysis_years
        
        # Get remediation cost
        cost_data = self.calculate_remediation_cost(control_id)
        remediation_cost = cost_data['estimated_cost']
        
        # Calculate NPV
        discount_rate = self.roi_calc['discount_rate']
        npv = 0
        for year in range(1, analysis_years + 1):
            discount_factor = 1 / ((1 + discount_rate) ** year)
            npv += risk_reduction_annual * discount_factor
        
        npv -= remediation_cost  # Subtract initial investment
        
        # Calculate ROI percentage
        roi_percentage = ((npv) / remediation_cost * 100) if remediation_cost > 0 else 0
        
        # Calculate payback period
        if risk_reduction_annual > 0:
            payback_months = (remediation_cost / risk_reduction_annual) * 12
        else:
            payback_months = None
        
        return {
            'control_id': control_id,
            'control_name': control['control_name'],
            'control_family': family,
            'compliance_status': control['compliance_status'],
            'risk_rating': control['risk_rating'],
            'priority_score': control['priority_score'],
            'kev_cve_count': control['kev_cve_count'],
            'breach_probability_before': round(prob_before * 100, 2),
            'breach_probability_after': round(prob_after * 100, 2),
            'probability_reduction': round((prob_before - prob_after) * 100, 2),
            'expected_breach_cost': breach_cost,
            'risk_reduction_annual': round(risk_reduction_annual, 2),
            'risk_reduction_total': round(risk_reduction_total, 2),
            'remediation_cost': remediation_cost,
            'net_present_value': round(npv, 2),
            'roi_percentage': round(roi_percentage, 2),
            'payback_period_months': round(payback_months, 1) if payback_months else None,
            'analysis_years': analysis_years,
            'discount_rate': discount_rate
        }
    
    def calculate_portfolio_roi(self, control_ids: Optional[List[str]] = None,
                                industry: str = 'technology',
                                analysis_years: int = 3) -> Dict:
        """
        Calculate aggregate ROI for multiple controls.
        
        Args:
            control_ids: List of control IDs (None for all non-compliant)
            industry: Industry type
            analysis_years: Number of years for analysis
            
        Returns:
            Dictionary with portfolio ROI metrics
        """
        cursor = self.conn.cursor()
        
        # Get non-compliant controls if not specified
        if control_ids is None:
            cursor.execute('''
                SELECT DISTINCT control_id
                FROM compliance_assessments ca
                WHERE compliance_status IN ('non_compliant', 'partial')
                AND assessment_id IN (
                    SELECT assessment_id FROM compliance_assessments ca2
                    WHERE ca2.control_id = ca.control_id
                    ORDER BY assessment_date DESC LIMIT 1
                )
            ''')
            control_ids = [row['control_id'] for row in cursor.fetchall()]
        
        logger.info(f"Calculating portfolio ROI for {len(control_ids)} controls...")
        
        total_cost = 0
        total_risk_reduction = 0
        total_npv = 0
        control_rois = []
        
        for control_id in control_ids:
            roi_data = self.calculate_control_roi(control_id, industry, analysis_years)
            
            if 'error' in roi_data or 'status' in roi_data:
                continue
            
            control_rois.append(roi_data)
            total_cost += roi_data['remediation_cost']
            total_risk_reduction += roi_data['risk_reduction_total']
            total_npv += roi_data['net_present_value']
        
        # Calculate aggregate metrics
        portfolio_roi = (total_npv / total_cost * 100) if total_cost > 0 else 0
        
        # Sort controls by ROI
        control_rois.sort(key=lambda x: x['roi_percentage'], reverse=True)
        
        return {
            'total_controls': len(control_rois),
            'total_remediation_cost': round(total_cost, 2),
            'total_risk_reduction': round(total_risk_reduction, 2),
            'total_net_present_value': round(total_npv, 2),
            'portfolio_roi_percentage': round(portfolio_roi, 2),
            'analysis_years': analysis_years,
            'industry': industry,
            'top_roi_controls': control_rois[:10],  # Top 10 by ROI
            'all_controls': control_rois
        }
    
    def generate_roi_report(self, industry: str = 'technology') -> Dict:
        """
        Generate comprehensive ROI report.
        
        Args:
            industry: Industry type for cost modeling
            
        Returns:
            Dictionary with ROI analysis
        """
        logger.info("Generating ROI report...")
        
        cursor = self.conn.cursor()
        
        # Get high-priority controls
        cursor.execute('''
            SELECT crs.control_id
            FROM control_risk_scores crs
            JOIN compliance_assessments ca ON crs.control_id = ca.control_id
            WHERE crs.priority_score >= 50
            AND ca.compliance_status IN ('non_compliant', 'partial')
            AND ca.assessment_id IN (
                SELECT assessment_id FROM compliance_assessments ca2
                WHERE ca2.control_id = ca.control_id
                ORDER BY assessment_date DESC LIMIT 1
            )
            ORDER BY crs.priority_score DESC
            LIMIT 20
        ''')
        
        high_priority_controls = [row['control_id'] for row in cursor.fetchall()]
        
        # Calculate ROI for high-priority controls
        high_priority_roi = self.calculate_portfolio_roi(
            high_priority_controls, industry
        )
        
        # Calculate ROI for all non-compliant controls
        all_controls_roi = self.calculate_portfolio_roi(None, industry)
        
        report = {
            'generated_at': datetime.now().isoformat(),
            'industry': industry,
            'high_priority_investment': high_priority_roi,
            'full_remediation': all_controls_roi,
            'recommendation': self._generate_recommendation(
                high_priority_roi, all_controls_roi
            )
        }
        
        return report
    
    def _generate_recommendation(self, high_priority: Dict, full: Dict) -> Dict:
        """Generate investment recommendation based on ROI analysis."""
        
        # Calculate efficiency metrics
        hp_efficiency = high_priority['total_risk_reduction'] / high_priority['total_remediation_cost']
        full_efficiency = full['total_risk_reduction'] / full['total_remediation_cost']
        
        if high_priority['portfolio_roi_percentage'] > 200:
            priority = 'high_priority_immediate'
            rationale = "High-priority controls offer exceptional ROI (>200%). Recommend immediate investment."
        elif high_priority['portfolio_roi_percentage'] > 100:
            priority = 'high_priority_recommended'
            rationale = "High-priority controls offer strong ROI (>100%). Recommend phased investment."
        elif full['portfolio_roi_percentage'] > 100:
            priority = 'full_remediation_recommended'
            rationale = "Full remediation offers positive ROI. Recommend comprehensive program."
        else:
            priority = 'selective_remediation'
            rationale = "Focus on highest ROI controls individually. Review cost optimization opportunities."
        
        return {
            'priority': priority,
            'rationale': rationale,
            'high_priority_efficiency': round(hp_efficiency, 2),
            'full_portfolio_efficiency': round(full_efficiency, 2),
            'cost_difference': round(full['total_remediation_cost'] - high_priority['total_remediation_cost'], 2),
            'risk_reduction_difference': round(full['total_risk_reduction'] - high_priority['total_risk_reduction'], 2)
        }
