#!/usr/bin/env python3
"""
Trend Analysis Module

Analyzes compliance trends over time:
- Compliance velocity (rate of improvement)
- Trend projections
- Control aging analysis
- Family-level trend analysis
"""

import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import logging
from collections import defaultdict

logger = logging.getLogger(__name__)


class TrendAnalyzer:
    """Trend analysis for GRC compliance metrics."""
    
    def __init__(self, db_path: str):
        """
        Initialize the trend analyzer.
        
        Args:
            db_path: Path to SQLite database
        """
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
    
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
    
    def get_compliance_over_time(self, months_back: int = 6) -> List[Dict]:
        """
        Get compliance percentage over time.
        
        Args:
            months_back: Number of months to look back
            
        Returns:
            List of compliance data points by month
        """
        cursor = self.conn.cursor()
        
        # Get the date range
        start_date = datetime.now() - timedelta(days=30 * months_back)
        
        # Get assessments grouped by month
        cursor.execute('''
            SELECT 
                strftime('%Y-%m', assessment_date) as month,
                COUNT(*) as total_assessments,
                SUM(CASE WHEN compliance_status = 'compliant' THEN 1 ELSE 0 END) as compliant_count,
                SUM(CASE WHEN compliance_status = 'partial' THEN 1 ELSE 0 END) as partial_count,
                SUM(CASE WHEN compliance_status = 'non_compliant' THEN 1 ELSE 0 END) as non_compliant_count,
                SUM(CASE WHEN compliance_status = 'not_assessed' THEN 1 ELSE 0 END) as not_assessed_count
            FROM compliance_assessments
            WHERE assessment_date >= ?
            GROUP BY strftime('%Y-%m', assessment_date)
            ORDER BY month
        ''', (start_date.strftime('%Y-%m-%d'),))
        
        results = []
        for row in cursor.fetchall():
            total = row['total_assessments']
            assessed = total - row['not_assessed_count']
            compliance_pct = (row['compliant_count'] / assessed * 100) if assessed > 0 else 0
            
            results.append({
                'month': row['month'],
                'total_assessments': total,
                'compliant': row['compliant_count'],
                'partial': row['partial_count'],
                'non_compliant': row['non_compliant_count'],
                'not_assessed': row['not_assessed_count'],
                'compliance_percentage': round(compliance_pct, 2)
            })
        
        return results
    
    def calculate_compliance_velocity(self, months: int = 6) -> Dict:
        """
        Calculate compliance velocity (rate of change).
        
        Args:
            months: Number of months to analyze
            
        Returns:
            Dictionary with velocity metrics
        """
        trend_data = self.get_compliance_over_time(months)
        
        if len(trend_data) < 2:
            return {
                'velocity': 0.0,
                'trend': 'insufficient_data',
                'months_analyzed': len(trend_data)
            }
        
        # Calculate velocity using linear regression
        percentages = [d['compliance_percentage'] for d in trend_data]
        
        # Simple linear regression
        n = len(percentages)
        x = list(range(n))
        y = percentages
        
        # Calculate slope (velocity)
        x_mean = sum(x) / n
        y_mean = sum(y) / n
        
        numerator = sum((x[i] - x_mean) * (y[i] - y_mean) for i in range(n))
        denominator = sum((x[i] - x_mean) ** 2 for i in range(n))
        
        if denominator == 0:
            slope = 0
        else:
            slope = numerator / denominator
        
        # Determine trend direction
        if slope > 0.5:
            trend = 'improving'
        elif slope < -0.5:
            trend = 'degrading'
        else:
            trend = 'stable'
        
        # Calculate projected compliance for next 3 months
        current_pct = percentages[-1]
        projection_3mo = min(current_pct + (slope * 3), 100.0)
        
        # Calculate months to 95% compliance
        if slope > 0 and current_pct < 95:
            months_to_95 = (95 - current_pct) / slope
        else:
            months_to_95 = None
        
        return {
            'velocity': round(slope, 2),
            'velocity_per_month': round(slope, 2),
            'trend': trend,
            'current_compliance': round(current_pct, 2),
            'projected_3_months': round(projection_3mo, 2),
            'months_to_95_percent': round(months_to_95, 1) if months_to_95 else None,
            'months_analyzed': n,
            'start_compliance': round(percentages[0], 2),
            'end_compliance': round(percentages[-1], 2),
            'total_improvement': round(percentages[-1] - percentages[0], 2)
        }
    
    def get_family_trends(self, months_back: int = 6) -> List[Dict]:
        """
        Get compliance trends by control family.
        
        Args:
            months_back: Number of months to analyze
            
        Returns:
            List of family trend data
        """
        cursor = self.conn.cursor()
        
        start_date = datetime.now() - timedelta(days=30 * months_back)
        
        cursor.execute('''
            SELECT 
                nc.control_family,
                strftime('%Y-%m', ca.assessment_date) as month,
                COUNT(*) as total,
                SUM(CASE WHEN ca.compliance_status = 'compliant' THEN 1 ELSE 0 END) as compliant
            FROM compliance_assessments ca
            JOIN nist_controls nc ON ca.control_id = nc.control_id
            WHERE ca.assessment_date >= ?
            GROUP BY nc.control_family, strftime('%Y-%m', ca.assessment_date)
            ORDER BY nc.control_family, month
        ''', (start_date.strftime('%Y-%m-%d'),))
        
        # Organize by family
        family_data = defaultdict(list)
        for row in cursor.fetchall():
            family = row['control_family']
            total = row['total']
            compliance_pct = (row['compliant'] / total * 100) if total > 0 else 0
            
            family_data[family].append({
                'month': row['month'],
                'compliance_percentage': compliance_pct
            })
        
        # Calculate trends for each family
        results = []
        for family, data in family_data.items():
            if len(data) < 2:
                continue
            
            percentages = [d['compliance_percentage'] for d in data]
            
            # Calculate velocity
            n = len(percentages)
            x = list(range(n))
            y = percentages
            
            x_mean = sum(x) / n
            y_mean = sum(y) / n
            
            numerator = sum((x[i] - x_mean) * (y[i] - y_mean) for i in range(n))
            denominator = sum((x[i] - x_mean) ** 2 for i in range(n))
            
            velocity = numerator / denominator if denominator != 0 else 0
            
            trend = 'improving' if velocity > 0.5 else ('degrading' if velocity < -0.5 else 'stable')
            
            results.append({
                'family': family,
                'current_compliance': round(percentages[-1], 2),
                'start_compliance': round(percentages[0], 2),
                'velocity': round(velocity, 2),
                'trend': trend,
                'total_change': round(percentages[-1] - percentages[0], 2),
                'data_points': n
            })
        
        # Sort by current compliance (lowest first - needs attention)
        results.sort(key=lambda x: x['current_compliance'])
        
        return results
    
    def get_control_aging_analysis(self) -> Dict:
        """
        Analyze control assessment age and staleness.
        
        Returns:
            Dictionary with aging metrics
        """
        cursor = self.conn.cursor()
        
        cursor.execute('''
            SELECT 
                nc.control_id,
                nc.control_family,
                nc.control_name,
                ca.assessment_date,
                ca.compliance_status,
                julianday('now') - julianday(ca.assessment_date) as days_since_assessment
            FROM nist_controls nc
            LEFT JOIN (
                SELECT control_id, assessment_date, compliance_status,
                       ROW_NUMBER() OVER (PARTITION BY control_id ORDER BY assessment_date DESC) as rn
                FROM compliance_assessments
            ) ca ON nc.control_id = ca.control_id AND ca.rn = 1
        ''')
        
        age_buckets = {
            'current': 0,      # < 90 days
            'aging': 0,        # 90-180 days
            'stale': 0,        # 180-365 days
            'very_stale': 0,   # > 365 days
            'never_assessed': 0
        }
        
        stale_controls = []
        
        for row in cursor.fetchall():
            days = row['days_since_assessment']
            
            if days is None:
                age_buckets['never_assessed'] += 1
            elif days < 90:
                age_buckets['current'] += 1
            elif days < 180:
                age_buckets['aging'] += 1
                stale_controls.append(dict(row))
            elif days < 365:
                age_buckets['stale'] += 1
                stale_controls.append(dict(row))
            else:
                age_buckets['very_stale'] += 1
                stale_controls.append(dict(row))
        
        return {
            'age_distribution': age_buckets,
            'stale_controls_count': len(stale_controls),
            'stale_controls': sorted(stale_controls, 
                                    key=lambda x: x['days_since_assessment'], 
                                    reverse=True)[:20]  # Top 20 stalest
        }
    
    def get_remediation_velocity(self) -> Dict:
        """
        Calculate velocity of remediation actions.
        
        Returns:
            Dictionary with remediation metrics
        """
        cursor = self.conn.cursor()
        
        # Get remediation action statistics
        cursor.execute('''
            SELECT 
                COUNT(*) as total_actions,
                SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed,
                SUM(CASE WHEN status = 'in_progress' THEN 1 ELSE 0 END) as in_progress,
                SUM(CASE WHEN status = 'open' THEN 1 ELSE 0 END) as open,
                SUM(CASE WHEN due_date < date('now') AND status != 'completed' THEN 1 ELSE 0 END) as overdue
            FROM remediation_actions
        ''')
        
        stats = cursor.fetchone()
        
        # Calculate completion rate
        total = stats['total_actions']
        completed = stats['completed']
        completion_rate = (completed / total * 100) if total > 0 else 0
        
        # Get average time to completion (for completed actions)
        cursor.execute('''
            SELECT 
                AVG(julianday(completed_date) - julianday(created_at)) as avg_days_to_complete
            FROM remediation_actions
            WHERE status = 'completed' AND completed_date IS NOT NULL
        ''')
        
        avg_row = cursor.fetchone()
        avg_days = avg_row['avg_days_to_complete'] if avg_row['avg_days_to_complete'] else 0
        
        return {
            'total_actions': total,
            'completed': completed,
            'in_progress': stats['in_progress'],
            'open': stats['open'],
            'overdue': stats['overdue'],
            'completion_rate': round(completion_rate, 2),
            'average_days_to_complete': round(avg_days, 1) if avg_days else None
        }
    
    def get_risk_trend_analysis(self, months_back: int = 6) -> Dict:
        """
        Analyze trends in risk scores over time.
        
        Args:
            months_back: Number of months to analyze
            
        Returns:
            Dictionary with risk trend metrics
        """
        cursor = self.conn.cursor()
        
        start_date = datetime.now() - timedelta(days=30 * months_back)
        
        # Get risk scores over time (if recalculated periodically)
        cursor.execute('''
            SELECT 
                strftime('%Y-%m', calculation_date) as month,
                AVG(priority_score) as avg_priority,
                AVG(threat_adjusted_score) as avg_threat_risk,
                COUNT(CASE WHEN priority_score >= 50 THEN 1 END) as high_risk_count
            FROM control_risk_scores
            WHERE calculation_date >= ?
            GROUP BY strftime('%Y-%m', calculation_date)
            ORDER BY month
        ''', (start_date.strftime('%Y-%m-%d'),))
        
        risk_data = []
        for row in cursor.fetchall():
            risk_data.append({
                'month': row['month'],
                'avg_priority_score': round(row['avg_priority'], 2),
                'avg_threat_risk': round(row['avg_threat_risk'], 2),
                'high_risk_count': row['high_risk_count']
            })
        
        # Calculate risk velocity
        if len(risk_data) >= 2:
            priority_scores = [d['avg_priority_score'] for d in risk_data]
            n = len(priority_scores)
            x = list(range(n))
            
            x_mean = sum(x) / n
            y_mean = sum(priority_scores) / n
            
            numerator = sum((x[i] - x_mean) * (priority_scores[i] - y_mean) for i in range(n))
            denominator = sum((x[i] - x_mean) ** 2 for i in range(n))
            
            risk_velocity = numerator / denominator if denominator != 0 else 0
            
            risk_trend = 'increasing' if risk_velocity > 0.5 else ('decreasing' if risk_velocity < -0.5 else 'stable')
        else:
            risk_velocity = 0
            risk_trend = 'insufficient_data'
        
        return {
            'risk_velocity': round(risk_velocity, 2),
            'risk_trend': risk_trend,
            'monthly_data': risk_data,
            'current_avg_priority': risk_data[-1]['avg_priority_score'] if risk_data else 0,
            'high_risk_count': risk_data[-1]['high_risk_count'] if risk_data else 0
        }
    
    def generate_trend_report(self) -> Dict:
        """
        Generate comprehensive trend analysis report.
        
        Returns:
            Dictionary with all trend metrics
        """
        logger.info("Generating comprehensive trend analysis report...")
        
        report = {
            'generated_at': datetime.now().isoformat(),
            'compliance_over_time': self.get_compliance_over_time(),
            'compliance_velocity': self.calculate_compliance_velocity(),
            'family_trends': self.get_family_trends(),
            'control_aging': self.get_control_aging_analysis(),
            'remediation_velocity': self.get_remediation_velocity(),
            'risk_trends': self.get_risk_trend_analysis()
        }
        
        return report
