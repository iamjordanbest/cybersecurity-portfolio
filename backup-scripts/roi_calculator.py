#!/usr/bin/env python3
"""
ROI Calculator for GRC Compliance Programs

This module calculates the Return on Investment (ROI) for compliance controls,
security investments, and remediation efforts. It provides both financial
and risk-based metrics to justify security spending.

Key Features:
- Control-level ROI analysis
- Portfolio-wide investment optimization
- Risk reduction quantification
- Time-to-value calculations
- Compliance cost modeling

Author: Jordan Best
Date: November 2024
"""

import yaml
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

# Default ROI Parameters
DEFAULT_ROI_PARAMS = {
    'average_breach_cost': 4450000,  # USD - IBM 2024 Cost of Data Breach Report
    'breach_probability_baseline': 0.27,  # 27% annual probability baseline
    'compliance_fine_range': {
        'gdpr_max': 20000000,
        'sox_max': 25000000,
        'pci_max': 500000
    },
    'operational_costs': {
        'security_analyst_hourly': 75,
        'compliance_consultant_hourly': 150,
        'audit_preparation_hours': 160
    },
    'time_value': {
        'discount_rate': 0.08,  # 8% annual discount rate
        'planning_horizon_years': 3
    }
}

class ROICalculator:
    """
    Calculate Return on Investment for compliance controls and security measures.
    """

    def __init__(self, config_path: str = "config/roi_parameters.yaml"):
        """Initialize ROI Calculator with parameters."""
        self.params = self._load_parameters(config_path)
        
    def _load_parameters(self, config_path: str) -> Dict[str, Any]:
        """Load ROI parameters from configuration file."""
        try:
            path = Path(config_path)
            if not path.exists():
                # Try relative to project root
                project_root = Path(__file__).parent.parent.parent
                path = project_root / config_path
                
            if path.exists():
                with open(path, 'r') as f:
                    config = yaml.safe_load(f)
                    # Merge with defaults
                    merged = DEFAULT_ROI_PARAMS.copy()
                    merged.update(config)
                    return merged
            else:
                logger.warning(f"ROI config not found at {path}, using defaults")
                return DEFAULT_ROI_PARAMS
                
        except Exception as e:
            logger.error(f"Error loading ROI parameters: {e}")
            return DEFAULT_ROI_PARAMS

    def calculate_control_roi(self, control: Dict[str, Any]) -> Dict[str, float]:
        """
        Calculate ROI for implementing a specific control.
        
        Args:
            control: Control dictionary with implementation cost and risk reduction
            
        Returns:
            Dictionary with ROI metrics
        """
        # Extract control parameters
        implementation_cost = float(control.get('implementation_cost', 50000))
        annual_maintenance = float(control.get('annual_maintenance_cost', 10000))
        risk_reduction_percent = float(control.get('risk_reduction_percent', 15))
        implementation_time_months = int(control.get('implementation_time_months', 6))
        
        # Calculate benefits
        annual_risk_reduction = self._calculate_annual_risk_reduction(risk_reduction_percent)
        compliance_benefits = self._calculate_compliance_benefits(control)
        operational_savings = self._calculate_operational_savings(control)
        
        # Calculate costs
        total_implementation_cost = implementation_cost
        three_year_maintenance = annual_maintenance * 3
        total_cost = total_implementation_cost + three_year_maintenance
        
        # Calculate annual benefits
        annual_benefits = annual_risk_reduction + compliance_benefits + operational_savings
        three_year_benefits = annual_benefits * 3
        
        # ROI calculations
        roi_percentage = ((three_year_benefits - total_cost) / total_cost) * 100
        payback_period_months = total_cost / (annual_benefits / 12) if annual_benefits > 0 else float('inf')
        npv = self._calculate_npv(annual_benefits, total_cost, annual_maintenance, 3)
        
        return {
            'roi_percentage': round(roi_percentage, 2),
            'payback_period_months': round(payback_period_months, 1),
            'net_present_value': round(npv, 2),
            'annual_benefits': round(annual_benefits, 2),
            'total_cost': round(total_cost, 2),
            'risk_reduction_value': round(annual_risk_reduction, 2),
            'compliance_value': round(compliance_benefits, 2),
            'operational_savings': round(operational_savings, 2)
        }

    def _calculate_annual_risk_reduction(self, risk_reduction_percent: float) -> float:
        """Calculate annual value of risk reduction."""
        baseline_probability = self.params['breach_probability_baseline']
        average_breach_cost = self.params['average_breach_cost']
        
        # Expected annual loss reduction
        reduced_probability = baseline_probability * (risk_reduction_percent / 100)
        annual_risk_reduction = reduced_probability * average_breach_cost
        
        return annual_risk_reduction

    def _calculate_compliance_benefits(self, control: Dict[str, Any]) -> float:
        """Calculate compliance-related benefits."""
        # Reduced audit costs
        audit_efficiency_gain = float(control.get('audit_efficiency_percent', 10))
        audit_cost_baseline = (
            self.params['operational_costs']['audit_preparation_hours'] * 
            self.params['operational_costs']['compliance_consultant_hourly']
        )
        audit_savings = audit_cost_baseline * (audit_efficiency_gain / 100)
        
        # Reduced fine probability
        fine_reduction = float(control.get('fine_risk_reduction_percent', 5))
        estimated_fine_exposure = self.params['compliance_fine_range']['gdpr_max'] * 0.1  # 10% probability baseline
        fine_savings = estimated_fine_exposure * (fine_reduction / 100)
        
        return audit_savings + fine_savings

    def _calculate_operational_savings(self, control: Dict[str, Any]) -> float:
        """Calculate operational efficiency savings."""
        # Automation savings
        hours_saved_monthly = float(control.get('automation_hours_saved_monthly', 20))
        analyst_hourly_rate = self.params['operational_costs']['security_analyst_hourly']
        annual_labor_savings = hours_saved_monthly * 12 * analyst_hourly_rate
        
        # Reduced manual processes
        process_efficiency_gain = float(control.get('process_efficiency_percent', 15))
        baseline_process_cost = 50000  # Annual baseline for manual security processes
        process_savings = baseline_process_cost * (process_efficiency_gain / 100)
        
        return annual_labor_savings + process_savings

    def _calculate_npv(self, annual_benefits: float, initial_cost: float, 
                      annual_costs: float, years: int) -> float:
        """Calculate Net Present Value."""
        discount_rate = self.params['time_value']['discount_rate']
        npv = -initial_cost  # Initial investment
        
        for year in range(1, years + 1):
            annual_net_benefit = annual_benefits - annual_costs
            discounted_benefit = annual_net_benefit / ((1 + discount_rate) ** year)
            npv += discounted_benefit
            
        return npv

    def calculate_portfolio_roi(self, controls: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculate ROI metrics for an entire portfolio of controls.
        
        Args:
            controls: List of control dictionaries
            
        Returns:
            Portfolio-level ROI analysis
        """
        if not controls:
            return {'error': 'No controls provided'}
            
        total_cost = 0
        total_benefits = 0
        total_npv = 0
        control_rois = []
        
        for control in controls:
            roi_data = self.calculate_control_roi(control)
            control_rois.append({
                'control_id': control.get('control_id', 'Unknown'),
                'roi_percentage': roi_data['roi_percentage'],
                'payback_months': roi_data['payback_period_months'],
                'npv': roi_data['net_present_value']
            })
            
            total_cost += roi_data['total_cost']
            total_benefits += roi_data['annual_benefits'] * 3
            total_npv += roi_data['net_present_value']
        
        # Portfolio metrics
        portfolio_roi = ((total_benefits - total_cost) / total_cost) * 100 if total_cost > 0 else 0
        average_payback = sum(c['payback_months'] for c in control_rois if c['payback_months'] != float('inf')) / len(control_rois)
        
        # Prioritization
        sorted_controls = sorted(control_rois, key=lambda x: x['roi_percentage'], reverse=True)
        
        return {
            'portfolio_metrics': {
                'total_investment': round(total_cost, 2),
                'total_benefits_3yr': round(total_benefits, 2),
                'portfolio_roi_percentage': round(portfolio_roi, 2),
                'total_npv': round(total_npv, 2),
                'average_payback_months': round(average_payback, 1)
            },
            'control_rankings': sorted_controls,
            'investment_summary': {
                'high_roi_controls': len([c for c in control_rois if c['roi_percentage'] > 100]),
                'positive_npv_controls': len([c for c in control_rois if c['npv'] > 0]),
                'quick_payback_controls': len([c for c in control_rois if c['payback_months'] < 24])
            }
        }

    def generate_investment_recommendations(self, controls: List[Dict[str, Any]], 
                                          budget_limit: float) -> Dict[str, Any]:
        """
        Generate optimal investment recommendations within budget constraints.
        
        Args:
            controls: List of controls with cost and benefit data
            budget_limit: Maximum available budget
            
        Returns:
            Optimized investment plan
        """
        # Calculate ROI for all controls
        control_analysis = []
        for control in controls:
            roi_data = self.calculate_control_roi(control)
            control_analysis.append({
                'control_id': control.get('control_id'),
                'title': control.get('title', ''),
                'implementation_cost': roi_data['total_cost'],
                'roi_percentage': roi_data['roi_percentage'],
                'npv': roi_data['net_present_value'],
                'payback_months': roi_data['payback_period_months'],
                'annual_benefits': roi_data['annual_benefits']
            })
        
        # Sort by ROI efficiency (NPV per dollar invested)
        control_analysis.sort(key=lambda x: x['npv'] / x['implementation_cost'] if x['implementation_cost'] > 0 else 0, reverse=True)
        
        # Greedy selection within budget
        selected_controls = []
        remaining_budget = budget_limit
        total_npv = 0
        total_annual_benefits = 0
        
        for control in control_analysis:
            if control['implementation_cost'] <= remaining_budget:
                selected_controls.append(control)
                remaining_budget -= control['implementation_cost']
                total_npv += control['npv']
                total_annual_benefits += control['annual_benefits']
        
        # Calculate overall metrics
        total_investment = budget_limit - remaining_budget
        portfolio_roi = (total_annual_benefits * 3 - total_investment) / total_investment * 100 if total_investment > 0 else 0
        
        return {
            'recommended_controls': selected_controls,
            'budget_utilization': {
                'total_budget': budget_limit,
                'allocated_budget': round(total_investment, 2),
                'remaining_budget': round(remaining_budget, 2),
                'budget_efficiency': round((total_investment / budget_limit) * 100, 1)
            },
            'expected_returns': {
                'total_npv': round(total_npv, 2),
                'annual_benefits': round(total_annual_benefits, 2),
                'portfolio_roi_percentage': round(portfolio_roi, 2),
                'payback_summary': f"{len(selected_controls)} controls selected"
            },
            'alternatives': {
                'deferred_controls': [c for c in control_analysis if c not in selected_controls],
                'budget_expansion_impact': self._calculate_budget_expansion_impact(control_analysis, budget_limit)
            }
        }

    def _calculate_budget_expansion_impact(self, control_analysis: List[Dict], current_budget: float) -> Dict:
        """Calculate impact of increasing budget."""
        next_control = None
        for control in control_analysis:
            total_cost = sum(c['implementation_cost'] for c in control_analysis if c in [control])
            if total_cost > current_budget:
                next_control = control
                break
        
        if next_control:
            additional_budget_needed = next_control['implementation_cost']
            additional_npv = next_control['npv']
            return {
                'next_best_control': next_control['control_id'],
                'additional_budget_needed': round(additional_budget_needed, 2),
                'additional_npv': round(additional_npv, 2),
                'marginal_efficiency': round(additional_npv / additional_budget_needed, 2)
            }
        return {'message': 'All controls can be funded within expanded budget'}

    def calculate_compliance_program_roi(self, program_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate ROI for an entire compliance program.
        
        Args:
            program_data: Dictionary containing program costs and benefits
            
        Returns:
            Comprehensive program ROI analysis
        """
        # Program costs
        staff_costs = float(program_data.get('annual_staff_costs', 500000))
        technology_costs = float(program_data.get('annual_technology_costs', 200000))
        external_audit_costs = float(program_data.get('annual_audit_costs', 100000))
        training_costs = float(program_data.get('annual_training_costs', 50000))
        
        total_annual_costs = staff_costs + technology_costs + external_audit_costs + training_costs
        
        # Program benefits
        breach_risk_reduction = float(program_data.get('breach_risk_reduction_percent', 40))
        fine_avoidance_value = float(program_data.get('estimated_fine_avoidance', 1000000))
        operational_efficiency_gains = float(program_data.get('operational_savings', 150000))
        insurance_premium_reduction = float(program_data.get('insurance_savings', 75000))
        
        # Calculate risk reduction value
        annual_risk_reduction = self._calculate_annual_risk_reduction(breach_risk_reduction)
        
        total_annual_benefits = (
            annual_risk_reduction + 
            fine_avoidance_value + 
            operational_efficiency_gains + 
            insurance_premium_reduction
        )
        
        # Multi-year analysis
        program_roi = ((total_annual_benefits - total_annual_costs) / total_annual_costs) * 100
        three_year_npv = self._calculate_npv(total_annual_benefits, 0, total_annual_costs, 3)
        
        return {
            'program_financials': {
                'annual_costs': round(total_annual_costs, 2),
                'annual_benefits': round(total_annual_benefits, 2),
                'annual_net_benefit': round(total_annual_benefits - total_annual_costs, 2),
                'program_roi_percentage': round(program_roi, 2),
                'three_year_npv': round(three_year_npv, 2)
            },
            'cost_breakdown': {
                'staff_percentage': round((staff_costs / total_annual_costs) * 100, 1),
                'technology_percentage': round((technology_costs / total_annual_costs) * 100, 1),
                'audit_percentage': round((external_audit_costs / total_annual_costs) * 100, 1),
                'training_percentage': round((training_costs / total_annual_costs) * 100, 1)
            },
            'benefit_breakdown': {
                'risk_reduction_value': round(annual_risk_reduction, 2),
                'compliance_value': round(fine_avoidance_value, 2),
                'operational_value': round(operational_efficiency_gains, 2),
                'insurance_value': round(insurance_premium_reduction, 2)
            },
            'performance_indicators': {
                'cost_per_control': round(total_annual_costs / program_data.get('total_controls', 100), 2),
                'benefit_cost_ratio': round(total_annual_benefits / total_annual_costs, 2),
                'risk_reduction_efficiency': round(annual_risk_reduction / total_annual_costs, 2)
            }
        }