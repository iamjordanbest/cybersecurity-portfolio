#!/usr/bin/env python3
"""
Risk Scoring Engine with Caching and Performance Monitoring

Enhanced version of risk_scoring.py with:
- Redis caching for frequently accessed scores
- Connection pooling for better concurrency
- Performance monitoring and metrics
- Optimized query patterns
"""

import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import yaml
import logging

from src.cache.redis_manager import CacheManager
from src.database.pool import SQLiteConnectionPool, get_pool
from src.utils.performance_monitor import monitor_performance, monitor_query, PerformanceTimer

logger = logging.getLogger(__name__)


class RiskScoringEngine:
    """Risk scoring engine with caching and performance optimizations."""
    
    def __init__(self, db_path: str = None, config_path: Optional[str] = None, 
                 cache_manager: Optional[CacheManager] = None,
                 connection_pool: Optional[SQLiteConnectionPool] = None):
        """
        Initialize the risk scoring engine.
        
        Args:
            db_path: Path to SQLite database (optional if using pool)
            config_path: Optional path to scoring configuration YAML
            cache_manager: Optional CacheManager instance
            connection_pool: Optional connection pool instance
        """
        self.db_path = db_path
        self.pool = connection_pool
        self.conn = None
        
        # Set up database connection
        if self.pool is None:
            if db_path is None:
                raise ValueError("Either db_path or connection_pool must be provided")
            self.conn = sqlite3.connect(db_path)
            self.conn.row_factory = sqlite3.Row
        
        # Set up cache
        self.cache = cache_manager or CacheManager()
        
        # Load scoring configuration
        if config_path is None and db_path:
            project_root = Path(db_path).parent.parent.parent
            config_path = project_root / 'config' / 'scoring.yaml'
        
        if config_path:
            with open(config_path, 'r') as f:
                self.config = yaml.safe_load(f)
            self.scoring = self.config['scoring']
        else:
            # Default configuration
            self.scoring = self._get_default_scoring_config()
    
    def _get_default_scoring_config(self) -> Dict:
        """Get default scoring configuration."""
        return {
            'status_multipliers': {
                'compliant': 0.5,
                'partially_compliant': 1.0,
                'non_compliant': 2.0,
                'not_assessed': 1.5
            },
            'staleness': {
                'enabled': True,
                'base_factor': 1.0,
                'daily_penalty': 0.005,
                'max_factor': 2.0
            }
        }
    
    def _get_connection(self):
        """Get database connection (from pool or direct)."""
        if self.pool:
            return self.pool.get_connection_context()
        else:
            # Return a context manager that does nothing
            from contextlib import contextmanager
            @contextmanager
            def dummy_context():
                yield self.conn
            return dummy_context()
    
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
    
    @monitor_performance(threshold_ms=50)
    def calculate_control_risk_score(self, control_id: str, use_cache: bool = True) -> Dict:
        """
        Calculate comprehensive risk score for a single control.
        
        Args:
            control_id: NIST control identifier
            use_cache: Whether to use cached results
            
        Returns:
            Dictionary containing all risk score components
        """
        # Check cache first
        if use_cache:
            cached_score = self.cache.get_risk_scores(control_id)
            if cached_score:
                logger.debug(f"Using cached risk score for {control_id}")
                return cached_score
        
        with PerformanceTimer(f"calculate_risk_score:{control_id}", threshold_ms=100):
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Get latest assessment
                assessment = self._get_latest_assessment(cursor, control_id)
                
                if not assessment:
                    return {
                        'control_id': control_id,
                        'error': 'No assessment found',
                        'base_risk_score': 0,
                        'threat_adjusted_score': 0,
                        'priority_score': 0
                    }
                
                # Get control info
                control_info = self._get_control_info(cursor, control_id)
                
                # Calculate base risk score
                base_risk = self._calculate_base_risk(assessment)
                
                # Get threat intelligence counts
                threat_data = self._get_threat_intelligence(cursor, control_id)
                
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
                
                result = {
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
                    'assessment_date': assessment['assessment_date'],
                    'cached_at': datetime.now().isoformat()
                }
                
                # Cache the result (24 hour TTL)
                if use_cache:
                    self.cache.cache_risk_scores(control_id, result, 
                                                ttl=CacheManager.TTL_LONG)
                
                return result
    
    @monitor_query(threshold_ms=20)
    def _get_latest_assessment(self, cursor, control_id: str) -> Optional[sqlite3.Row]:
        """Get latest assessment for a control."""
        cursor.execute('''
            SELECT *
            FROM compliance_assessments
            WHERE control_id = ?
            ORDER BY assessment_date DESC
            LIMIT 1
        ''', (control_id,))
        
        return cursor.fetchone()
    
    @monitor_query(threshold_ms=10)
    def _get_control_info(self, cursor, control_id: str) -> sqlite3.Row:
        """Get control information."""
        cursor.execute('''
            SELECT control_family, control_name
            FROM nist_controls
            WHERE control_id = ?
        ''', (control_id,))
        
        return cursor.fetchone()
    
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
    
    @monitor_query(threshold_ms=30)
    def _get_threat_intelligence(self, cursor, control_id: str) -> Dict:
        """Get threat intelligence metrics for a control (optimized query)."""
        # Single query to get all threat intelligence data
        cursor.execute('''
            SELECT 
                (SELECT COUNT(*) FROM cve_control_mapping WHERE control_id = ?) as kev_count,
                (SELECT COUNT(*) FROM attack_control_mapping WHERE control_id = ?) as attack_count,
                (SELECT COUNT(*) FROM cve_control_mapping ccm
                 JOIN cisa_kev ck ON ccm.cve_id = ck.cve_id
                 WHERE ccm.control_id = ? AND ck.due_date < date('now')) as overdue_kev,
                (SELECT COUNT(*) FROM cve_control_mapping ccm
                 JOIN cisa_kev ck ON ccm.cve_id = ck.cve_id
                 WHERE ccm.control_id = ? AND ck.known_ransomware_use = 1) as ransomware_count
        ''', (control_id, control_id, control_id, control_id))
        
        row = cursor.fetchone()
        
        return {
            'kev_count': row['kev_count'] or 0,
            'attack_count': row['attack_count'] or 0,
            'overdue_kev': row['overdue_kev'] or 0,
            'ransomware_count': row['ransomware_count'] or 0
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
    
    @monitor_performance(threshold_ms=5000)
    def calculate_all_risk_scores(self, recalculate: bool = False, 
                                  use_cache: bool = True) -> Dict:
        """
        Calculate risk scores for all controls.
        
        Args:
            recalculate: If True, recalculate even if scores exist
            use_cache: Whether to use cached results
            
        Returns:
            Dictionary with statistics about calculated scores
        """
        # Check if we have cached summary
        if use_cache and not recalculate:
            cached_summary = self.cache.get(f"{CacheManager.PREFIX_RISK}:summary")
            if cached_summary:
                logger.info("Using cached risk score summary")
                return cached_summary
        
        with PerformanceTimer("calculate_all_risk_scores", threshold_ms=10000):
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
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
                    score_data = self.calculate_control_risk_score(control_id, use_cache)
                    
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
                
                conn.commit()
                
                result = {
                    'total_controls': len(controls),
                    'scores_calculated': scores_calculated,
                    'scores_updated': scores_updated,
                    'high_risk_controls': high_risk_count,
                    'timestamp': datetime.now().isoformat()
                }
                
                # Cache the summary (1 hour TTL)
                if use_cache:
                    self.cache.set(f"{CacheManager.PREFIX_RISK}:summary", 
                                  result, ttl=CacheManager.TTL_MEDIUM)
                
                # Invalidate individual control caches if recalculated
                if recalculate:
                    self.cache.invalidate_risk_scores()
                
                return result
    
    @monitor_performance(threshold_ms=100)
    def get_high_risk_controls(self, threshold: float = 50.0, limit: int = 20,
                              use_cache: bool = True) -> List[Dict]:
        """
        Get controls with highest risk/priority scores.
        
        Args:
            threshold: Minimum priority score threshold
            limit: Maximum number of controls to return
            use_cache: Whether to use cached results
            
        Returns:
            List of high-risk control dictionaries
        """
        cache_key = f"{CacheManager.PREFIX_RISK}:high_risk:{threshold}:{limit}"
        
        if use_cache:
            cached = self.cache.get(cache_key)
            if cached:
                logger.debug("Using cached high-risk controls")
                return cached
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
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
            
            results = [dict(row) for row in cursor.fetchall()]
            
            # Cache the results (1 hour TTL)
            if use_cache:
                self.cache.set(cache_key, results, ttl=CacheManager.TTL_MEDIUM)
            
            return results
    
    @monitor_performance(threshold_ms=50)
    def get_risk_score_summary(self, use_cache: bool = True) -> Dict:
        """Get summary statistics of risk scores."""
        cache_key = f"{CacheManager.PREFIX_RISK}:stats:summary"
        
        if use_cache:
            cached = self.cache.get(cache_key)
            if cached:
                logger.debug("Using cached risk score summary")
                return cached
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
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
            
            result = {
                'total_controls': row['total'],
                'average_priority_score': round(row['avg_priority'] or 0, 2),
                'average_threat_risk': round(row['avg_threat_risk'] or 0, 2),
                'critical_risk_controls': row['critical_count'] or 0,
                'high_risk_controls': row['high_count'] or 0,
                'medium_risk_controls': row['medium_count'] or 0,
                'low_risk_controls': row['low_count'] or 0,
                'timestamp': datetime.now().isoformat()
            }
            
            # Cache the summary (30 minutes TTL)
            if use_cache:
                self.cache.set(cache_key, result, ttl=1800)
            
            return result
    
    def invalidate_cache(self, control_id: Optional[str] = None):
        """
        Invalidate cached risk scores.
        
        Args:
            control_id: If provided, invalidate only this control's cache
        """
        if control_id:
            self.cache.invalidate_risk_scores(control_id)
            logger.info(f"Invalidated cache for control {control_id}")
        else:
            self.cache.invalidate_risk_scores()
            self.cache.invalidate_pattern(f"{CacheManager.PREFIX_RISK}:*")
            logger.info("Invalidated all risk score caches")
