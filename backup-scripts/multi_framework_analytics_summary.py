#!/usr/bin/env python3
"""
Multi-Framework Analytics Summary

This is a condensed version of the multi-framework analytics module from Project 2.
Contains the key analytical functions for cross-framework compliance analysis.

Key Features:
- Framework gap analysis
- Cross-framework trend analysis
- Multi-framework compliance scoring
- Executive reporting and insights

Author: Jordan Best
Date: November 2024
"""

import pandas as pd
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class MultiFrameworkAnalytics:
    """
    Provides cross-framework analytics and insights for compliance data.
    """
    
    def __init__(self):
        """Initialize Multi-Framework Analytics."""
        self.supported_frameworks = ['NIST_800-53', 'CIS_Controls', 'ISO_27001', 'NIST_CSF']
    
    def calculate_cross_framework_score(self, framework_data: Dict[str, List[Dict]]) -> Dict[str, Any]:
        """
        Calculate unified compliance score across multiple frameworks.
        
        Args:
            framework_data: Dictionary with framework names as keys and control data as values
            
        Returns:
            Cross-framework compliance analysis
        """
        total_controls = 0
        total_passed = 0
        framework_scores = {}
        
        for framework, controls in framework_data.items():
            if not controls:
                continue
                
            passed = sum(1 for c in controls if c.get('status', '').lower() == 'pass')
            total = len(controls)
            score = (passed / total * 100) if total > 0 else 0
            
            framework_scores[framework] = {
                'score': round(score, 2),
                'passed': passed,
                'total': total,
                'failed': total - passed
            }
            
            total_controls += total
            total_passed += passed
        
        unified_score = (total_passed / total_controls * 100) if total_controls > 0 else 0
        
        return {
            'unified_compliance_score': round(unified_score, 2),
            'framework_breakdown': framework_scores,
            'summary': {
                'total_controls': total_controls,
                'total_passed': total_passed,
                'total_failed': total_controls - total_passed,
                'frameworks_analyzed': len(framework_scores)
            }
        }
    
    def analyze_framework_gaps(self, framework_data: Dict[str, List[Dict]]) -> Dict[str, Any]:
        """
        Identify gaps and overlaps between frameworks.
        
        Args:
            framework_data: Framework control data
            
        Returns:
            Gap analysis results
        """
        gap_analysis = {}
        framework_coverage = {}
        
        for framework, controls in framework_data.items():
            failed_controls = [c for c in controls if c.get('status', '').lower() in ['fail', 'not_tested']]
            critical_gaps = [c for c in failed_controls if c.get('severity', '').lower() in ['critical', 'high']]
            
            framework_coverage[framework] = {
                'total_controls': len(controls),
                'gaps_identified': len(failed_controls),
                'critical_gaps': len(critical_gaps),
                'gap_percentage': round(len(failed_controls) / len(controls) * 100, 2) if controls else 0
            }
        
        # Identify common gap patterns
        all_failed_categories = []
        for framework, controls in framework_data.items():
            failed_controls = [c for c in controls if c.get('status', '').lower() in ['fail', 'not_tested']]
            categories = [c.get('category', 'Unknown') for c in failed_controls]
            all_failed_categories.extend(categories)
        
        # Count category failures across frameworks
        from collections import Counter
        category_failures = Counter(all_failed_categories)
        
        return {
            'framework_coverage': framework_coverage,
            'common_gap_categories': dict(category_failures.most_common(10)),
            'cross_framework_insights': self._generate_gap_insights(framework_coverage, category_failures)
        }
    
    def _generate_gap_insights(self, coverage: Dict, categories: 'Counter') -> List[str]:
        """Generate actionable insights from gap analysis."""
        insights = []
        
        # Framework-specific insights
        worst_framework = min(coverage.items(), key=lambda x: x[1]['gap_percentage'] if x[1]['total_controls'] > 0 else 100)
        best_framework = max(coverage.items(), key=lambda x: 100 - x[1]['gap_percentage'] if x[1]['total_controls'] > 0 else 0)
        
        if worst_framework[1]['gap_percentage'] > 25:
            insights.append(f"⚠️ {worst_framework[0]} has {worst_framework[1]['gap_percentage']}% gaps - requires immediate attention")
        
        if best_framework[1]['gap_percentage'] < 10:
            insights.append(f"✅ {best_framework[0]} shows excellent compliance at {100 - best_framework[1]['gap_percentage']:.1f}%")
        
        # Category-specific insights
        if categories:
            top_category = categories.most_common(1)[0]
            insights.append(f"🎯 Focus on '{top_category[0]}' controls - appears in {top_category[1]} framework gaps")
        
        return insights
    
    def generate_executive_summary(self, framework_data: Dict[str, List[Dict]], 
                                  assessment_date: datetime = None) -> Dict[str, Any]:
        """
        Generate executive-level summary of compliance posture.
        
        Args:
            framework_data: Framework control data
            assessment_date: Date of assessment (defaults to now)
            
        Returns:
            Executive summary with key metrics and recommendations
        """
        if assessment_date is None:
            assessment_date = datetime.now()
        
        # Calculate key metrics
        cross_framework_score = self.calculate_cross_framework_score(framework_data)
        gap_analysis = self.analyze_framework_gaps(framework_data)
        
        # Risk assessment
        total_critical_gaps = sum(
            fw['critical_gaps'] for fw in gap_analysis['framework_coverage'].values()
        )
        
        # Determine overall risk level
        unified_score = cross_framework_score['unified_compliance_score']
        if unified_score >= 90:
            risk_level = "LOW"
            risk_color = "🟢"
        elif unified_score >= 75:
            risk_level = "MEDIUM"
            risk_color = "🟡"
        else:
            risk_level = "HIGH"
            risk_color = "🔴"
        
        # Generate recommendations
        recommendations = self._generate_recommendations(cross_framework_score, gap_analysis)
        
        return {
            'assessment_summary': {
                'assessment_date': assessment_date.strftime('%Y-%m-%d'),
                'overall_compliance_score': unified_score,
                'risk_level': f"{risk_color} {risk_level}",
                'frameworks_assessed': len(framework_data),
                'total_controls_evaluated': cross_framework_score['summary']['total_controls'],
                'critical_gaps_identified': total_critical_gaps
            },
            'key_metrics': {
                'compliance_score': f"{unified_score:.1f}%",
                'controls_passing': cross_framework_score['summary']['total_passed'],
                'controls_failing': cross_framework_score['summary']['total_failed'],
                'framework_coverage': gap_analysis['framework_coverage']
            },
            'top_priorities': recommendations['immediate_actions'],
            'strategic_recommendations': recommendations['strategic_initiatives'],
            'framework_performance': cross_framework_score['framework_breakdown']
        }
    
    def _generate_recommendations(self, score_data: Dict, gap_data: Dict) -> Dict[str, List[str]]:
        """Generate actionable recommendations based on analysis."""
        immediate_actions = []
        strategic_initiatives = []
        
        # Immediate actions based on critical gaps
        total_critical = sum(
            fw['critical_gaps'] for fw in gap_data['framework_coverage'].values()
        )
        
        if total_critical > 0:
            immediate_actions.append(f"🚨 Address {total_critical} critical control gaps within 30 days")
        
        # Framework-specific recommendations
        for framework, metrics in gap_data['framework_coverage'].items():
            if metrics['gap_percentage'] > 30:
                immediate_actions.append(f"📋 Prioritize {framework} remediation - {metrics['gaps_identified']} gaps identified")
            elif metrics['gap_percentage'] < 10:
                strategic_initiatives.append(f"⭐ Use {framework} as compliance model - only {metrics['gap_percentage']:.1f}% gaps")
        
        # Category-based recommendations
        top_categories = list(gap_data['common_gap_categories'].items())[:3]
        for category, count in top_categories:
            if count >= 2:
                strategic_initiatives.append(f"🎯 Develop {category} improvement program - affects {count} frameworks")
        
        # Overall score recommendations
        unified_score = score_data['unified_compliance_score']
        if unified_score < 75:
            immediate_actions.append("⚡ Launch comprehensive compliance improvement initiative")
        elif unified_score > 90:
            strategic_initiatives.append("🏆 Consider pursuing compliance certification or audit")
        
        return {
            'immediate_actions': immediate_actions[:5],  # Limit to top 5
            'strategic_initiatives': strategic_initiatives[:5]
        }