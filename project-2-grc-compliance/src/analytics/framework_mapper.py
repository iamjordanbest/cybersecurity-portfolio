#!/usr/bin/env python3
"""
Cross-Framework Control Mapping Engine

Maps controls across different compliance frameworks to show relationships,
equivalencies, and coverage. Supports multiple mapping types and strengths.

Mapping Types:
- EXACT: Controls are identical in scope and requirements
- PARTIAL: Controls overlap but one is broader/narrower
- RELATED: Controls address similar objectives differently
- COMPLEMENTARY: Controls work together to achieve objective
"""

import sqlite3
from typing import List, Dict, Optional, Tuple
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FrameworkMapper:
    """
    Cross-framework control mapping engine.
    
    Provides methods to create, query, and analyze control mappings
    across different compliance frameworks.
    """
    
    def __init__(self, db_path: str):
        """
        Initialize the framework mapper.
        
        Args:
            db_path: Path to the GRC analytics database
        """
        self.db_path = db_path
        self.conn = None
        
    def connect(self):
        """Connect to the database."""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        
    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
            
    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
    
    def add_mapping(self, source_framework: str, source_control: str,
                   target_framework: str, target_control: str,
                   mapping_type: str = 'RELATED', 
                   mapping_strength: float = 0.7,
                   rationale: Optional[str] = None) -> bool:
        """
        Add a control mapping between two frameworks.
        
        Args:
            source_framework: Source framework code (e.g., 'NIST-800-53')
            source_control: Source control identifier (e.g., 'AC-1')
            target_framework: Target framework code (e.g., 'ISO-27001')
            target_control: Target control identifier (e.g., 'A.9.1.1')
            mapping_type: Type of mapping (EXACT, PARTIAL, RELATED, COMPLEMENTARY)
            mapping_strength: Strength of mapping (0.0 to 1.0)
            rationale: Explanation of the mapping
            
        Returns:
            True if mapping added successfully, False otherwise
        """
        cursor = self.conn.cursor()
        
        try:
            # Get framework IDs
            cursor.execute("SELECT framework_id FROM frameworks WHERE framework_code = ?", 
                         (source_framework,))
            source_fw_id = cursor.fetchone()
            
            cursor.execute("SELECT framework_id FROM frameworks WHERE framework_code = ?",
                         (target_framework,))
            target_fw_id = cursor.fetchone()
            
            if not source_fw_id or not target_fw_id:
                logger.error(f"Framework not found: {source_framework} or {target_framework}")
                return False
            
            # Insert mapping
            cursor.execute('''
                INSERT OR REPLACE INTO control_mappings (
                    source_framework_id,
                    source_control_id,
                    target_framework_id,
                    target_control_id,
                    mapping_type,
                    mapping_strength,
                    mapping_rationale
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                source_fw_id[0],
                source_control,
                target_fw_id[0],
                target_control,
                mapping_type,
                mapping_strength,
                rationale
            ))
            
            self.conn.commit()
            logger.debug(f"Added mapping: {source_framework}:{source_control} -> "
                        f"{target_framework}:{target_control} ({mapping_type})")
            return True
            
        except Exception as e:
            logger.error(f"Error adding mapping: {e}")
            self.conn.rollback()
            return False
    
    def get_mappings_for_control(self, framework: str, control_id: str,
                                 direction: str = 'both') -> List[Dict]:
        """
        Get all mappings for a specific control.
        
        Args:
            framework: Framework code
            control_id: Control identifier
            direction: 'source', 'target', or 'both'
            
        Returns:
            List of mapping dictionaries
        """
        cursor = self.conn.cursor()
        
        # Get framework ID
        cursor.execute("SELECT framework_id FROM frameworks WHERE framework_code = ?",
                      (framework,))
        fw_result = cursor.fetchone()
        
        if not fw_result:
            logger.error(f"Framework not found: {framework}")
            return []
        
        fw_id = fw_result[0]
        mappings = []
        
        # Get mappings where this control is the source
        if direction in ('source', 'both'):
            cursor.execute('''
                SELECT 
                    cm.*,
                    sf.framework_code as source_framework,
                    tf.framework_code as target_framework,
                    fc.control_name as target_control_name
                FROM control_mappings cm
                JOIN frameworks sf ON cm.source_framework_id = sf.framework_id
                JOIN frameworks tf ON cm.target_framework_id = tf.framework_id
                LEFT JOIN framework_controls fc ON cm.target_framework_id = fc.framework_id 
                    AND cm.target_control_id = fc.control_identifier
                WHERE cm.source_framework_id = ? AND cm.source_control_id = ?
            ''', (fw_id, control_id))
            
            for row in cursor.fetchall():
                mappings.append({
                    'direction': 'outbound',
                    'mapping_type': row['mapping_type'],
                    'mapping_strength': row['mapping_strength'],
                    'target_framework': row['target_framework'],
                    'target_control': row['target_control_id'],
                    'target_control_name': row['target_control_name'],
                    'rationale': row['mapping_rationale']
                })
        
        # Get mappings where this control is the target
        if direction in ('target', 'both'):
            cursor.execute('''
                SELECT 
                    cm.*,
                    sf.framework_code as source_framework,
                    tf.framework_code as target_framework,
                    fc.control_name as source_control_name
                FROM control_mappings cm
                JOIN frameworks sf ON cm.source_framework_id = sf.framework_id
                JOIN frameworks tf ON cm.target_framework_id = tf.framework_id
                LEFT JOIN framework_controls fc ON cm.source_framework_id = fc.framework_id 
                    AND cm.source_control_id = fc.control_identifier
                WHERE cm.target_framework_id = ? AND cm.target_control_id = ?
            ''', (fw_id, control_id))
            
            for row in cursor.fetchall():
                mappings.append({
                    'direction': 'inbound',
                    'mapping_type': row['mapping_type'],
                    'mapping_strength': row['mapping_strength'],
                    'source_framework': row['source_framework'],
                    'source_control': row['source_control_id'],
                    'source_control_name': row['source_control_name'],
                    'rationale': row['mapping_rationale']
                })
        
        return mappings
    
    def get_framework_coverage(self, source_framework: str, 
                              target_framework: str) -> Dict:
        """
        Calculate coverage between two frameworks.
        
        Args:
            source_framework: Source framework code
            target_framework: Target framework code
            
        Returns:
            Dictionary with coverage statistics
        """
        cursor = self.conn.cursor()
        
        # Get framework IDs
        cursor.execute("SELECT framework_id FROM frameworks WHERE framework_code = ?",
                      (source_framework,))
        source_fw_id = cursor.fetchone()[0]
        
        cursor.execute("SELECT framework_id FROM frameworks WHERE framework_code = ?",
                      (target_framework,))
        target_fw_id = cursor.fetchone()[0]
        
        # Count total controls in each framework
        cursor.execute('''
            SELECT COUNT(*) FROM framework_controls WHERE framework_id = ?
        ''', (source_fw_id,))
        source_total = cursor.fetchone()[0]
        
        cursor.execute('''
            SELECT COUNT(*) FROM framework_controls WHERE framework_id = ?
        ''', (target_fw_id,))
        target_total = cursor.fetchone()[0]
        
        # Count mapped controls
        cursor.execute('''
            SELECT COUNT(DISTINCT source_control_id) 
            FROM control_mappings
            WHERE source_framework_id = ? AND target_framework_id = ?
        ''', (source_fw_id, target_fw_id))
        source_mapped = cursor.fetchone()[0]
        
        cursor.execute('''
            SELECT COUNT(DISTINCT target_control_id)
            FROM control_mappings
            WHERE source_framework_id = ? AND target_framework_id = ?
        ''', (source_fw_id, target_fw_id))
        target_mapped = cursor.fetchone()[0]
        
        # Count by mapping type
        cursor.execute('''
            SELECT mapping_type, COUNT(*) as cnt
            FROM control_mappings
            WHERE source_framework_id = ? AND target_framework_id = ?
            GROUP BY mapping_type
        ''', (source_fw_id, target_fw_id))
        
        mapping_types = {row[0]: row[1] for row in cursor.fetchall()}
        
        return {
            'source_framework': source_framework,
            'target_framework': target_framework,
            'source_total_controls': source_total,
            'source_mapped_controls': source_mapped,
            'source_coverage_pct': round(source_mapped / source_total * 100, 2) if source_total > 0 else 0,
            'target_total_controls': target_total,
            'target_mapped_controls': target_mapped,
            'target_coverage_pct': round(target_mapped / target_total * 100, 2) if target_total > 0 else 0,
            'total_mappings': sum(mapping_types.values()),
            'mapping_types': mapping_types
        }
    
    def find_gaps(self, source_framework: str, target_framework: str) -> List[Dict]:
        """
        Find controls in source framework without mappings to target.
        
        Args:
            source_framework: Source framework code
            target_framework: Target framework code
            
        Returns:
            List of unmapped controls
        """
        cursor = self.conn.cursor()
        
        cursor.execute('''
            SELECT 
                fc.control_identifier,
                fc.control_name,
                fc.control_category,
                fc.priority_level
            FROM framework_controls fc
            JOIN frameworks f ON fc.framework_id = f.framework_id
            WHERE f.framework_code = ?
            AND NOT EXISTS (
                SELECT 1 FROM control_mappings cm
                JOIN frameworks sf ON cm.source_framework_id = sf.framework_id
                JOIN frameworks tf ON cm.target_framework_id = tf.framework_id
                WHERE sf.framework_code = ?
                AND tf.framework_code = ?
                AND cm.source_control_id = fc.control_identifier
            )
            ORDER BY 
                CASE fc.priority_level
                    WHEN 'critical' THEN 1
                    WHEN 'high' THEN 2
                    WHEN 'medium' THEN 3
                    WHEN 'low' THEN 4
                END,
                fc.control_identifier
        ''', (source_framework, source_framework, target_framework))
        
        gaps = []
        for row in cursor.fetchall():
            gaps.append({
                'control_id': row['control_identifier'],
                'control_name': row['control_name'],
                'category': row['control_category'],
                'priority': row['priority_level']
            })
        
        return gaps
    
    def get_all_framework_pairs(self) -> List[Tuple[str, str]]:
        """
        Get all possible framework pairs for mapping.
        
        Returns:
            List of (source_framework, target_framework) tuples
        """
        cursor = self.conn.cursor()
        
        cursor.execute('''
            SELECT framework_code FROM frameworks WHERE is_active = 1
            ORDER BY framework_code
        ''')
        
        frameworks = [row[0] for row in cursor.fetchall()]
        
        pairs = []
        for i, source in enumerate(frameworks):
            for target in frameworks[i+1:]:
                pairs.append((source, target))
                pairs.append((target, source))  # Both directions
        
        return pairs
    
    def get_mapping_statistics(self) -> Dict:
        """
        Get overall mapping statistics.
        
        Returns:
            Dictionary with mapping statistics
        """
        cursor = self.conn.cursor()
        
        # Total mappings
        cursor.execute("SELECT COUNT(*) FROM control_mappings")
        total_mappings = cursor.fetchone()[0]
        
        # Mappings by type
        cursor.execute('''
            SELECT mapping_type, COUNT(*) as cnt
            FROM control_mappings
            GROUP BY mapping_type
        ''')
        by_type = {row[0]: row[1] for row in cursor.fetchall()}
        
        # Mappings by framework pair
        cursor.execute('''
            SELECT 
                sf.framework_code as source,
                tf.framework_code as target,
                COUNT(*) as cnt
            FROM control_mappings cm
            JOIN frameworks sf ON cm.source_framework_id = sf.framework_id
            JOIN frameworks tf ON cm.target_framework_id = tf.framework_id
            GROUP BY source, target
            ORDER BY cnt DESC
        ''')
        by_pair = [(row[0], row[1], row[2]) for row in cursor.fetchall()]
        
        # Average mapping strength
        cursor.execute('''
            SELECT AVG(mapping_strength) FROM control_mappings
        ''')
        avg_strength = cursor.fetchone()[0]
        
        return {
            'total_mappings': total_mappings,
            'by_type': by_type,
            'by_framework_pair': by_pair,
            'average_strength': round(avg_strength, 3) if avg_strength else 0
        }


def main():
    """Example usage."""
    db_path = Path(__file__).parent.parent.parent / 'data' / 'processed' / 'grc_analytics.db'
    
    with FrameworkMapper(str(db_path)) as mapper:
        # Example: Add a mapping
        mapper.add_mapping(
            source_framework='NIST-800-53',
            source_control='AC-1',
            target_framework='ISO-27001',
            target_control='A.9.1.1',
            mapping_type='RELATED',
            mapping_strength=0.8,
            rationale='Both address access control policies'
        )
        
        # Get mappings for a control
        mappings = mapper.get_mappings_for_control('NIST-800-53', 'AC-1')
        print(f"Found {len(mappings)} mappings for AC-1")
        
        # Get framework coverage
        coverage = mapper.get_framework_coverage('NIST-800-53', 'ISO-27001')
        print(f"Coverage: {coverage['source_coverage_pct']}%")


if __name__ == '__main__':
    main()
