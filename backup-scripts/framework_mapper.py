#!/usr/bin/env python3
"""
Framework Mapping Utilities

This module provides cross-framework mapping capabilities for compliance
controls across different security frameworks (NIST, CIS, ISO 27001, etc.).

Key Features:
- Multi-framework control mapping
- Coverage gap analysis
- Framework harmonization
- Control overlap detection

Author: Jordan Best
Date: November 2024
"""

import json
from pathlib import Path
from typing import Dict, Any, List, Optional, Set, Tuple
import logging
from dataclasses import dataclass, field
from collections import defaultdict

logger = logging.getLogger(__name__)

@dataclass
class ControlMapping:
    """Represents a mapping between controls in different frameworks."""
    source_framework: str
    source_control_id: str
    target_framework: str
    target_control_id: str
    mapping_strength: float  # 0.0 to 1.0
    mapping_type: str  # 'direct', 'partial', 'conceptual'
    notes: Optional[str] = None

@dataclass
class FrameworkControl:
    """Represents a control within a security framework."""
    framework: str
    control_id: str
    title: str
    description: str
    category: str
    severity: str = "medium"
    implementation_guidance: Optional[str] = None
    mappings: List[ControlMapping] = field(default_factory=list)

class FrameworkMapper:
    """
    Provides mapping and analysis capabilities across security frameworks.
    """
    
    def __init__(self, mappings_file: str = "data/framework_mappings.json"):
        """
        Initialize Framework Mapper.
        
        Args:
            mappings_file: Path to framework mappings configuration
        """
        self.mappings_file = mappings_file
        self.control_mappings: List[ControlMapping] = []
        self.framework_controls: Dict[str, List[FrameworkControl]] = defaultdict(list)
        self._load_mappings()
    
    def _load_mappings(self):
        """Load framework mappings from configuration file."""
        try:
            mappings_path = Path(self.mappings_file)
            if mappings_path.exists():
                with open(mappings_path, 'r') as f:
                    data = json.load(f)
                    self._parse_mappings(data)
            else:
                logger.warning(f"Mappings file not found: {mappings_path}")
                self._load_default_mappings()
        except Exception as e:
            logger.error(f"Error loading mappings: {e}")
            self._load_default_mappings()
    
    def _parse_mappings(self, data: Dict[str, Any]):
        """Parse mappings from loaded JSON data."""
        # Parse control mappings
        for mapping_data in data.get('mappings', []):
            mapping = ControlMapping(
                source_framework=mapping_data['source_framework'],
                source_control_id=mapping_data['source_control'],
                target_framework=mapping_data['target_framework'],
                target_control_id=mapping_data['target_control'],
                mapping_strength=float(mapping_data.get('strength', 0.8)),
                mapping_type=mapping_data.get('type', 'direct'),
                notes=mapping_data.get('notes')
            )
            self.control_mappings.append(mapping)
        
        # Parse framework controls
        for framework, controls in data.get('frameworks', {}).items():
            for control_data in controls:
                control = FrameworkControl(
                    framework=framework,
                    control_id=control_data['control_id'],
                    title=control_data['title'],
                    description=control_data['description'],
                    category=control_data.get('category', 'General'),
                    severity=control_data.get('severity', 'medium'),
                    implementation_guidance=control_data.get('guidance')
                )
                self.framework_controls[framework].append(control)
    
    def _load_default_mappings(self):
        """Load default framework mappings."""
        # Sample mappings between common frameworks
        default_mappings = [
            # NIST 800-53 to CIS Controls
            ControlMapping('NIST_800-53', 'AC-2', 'CIS', '16.1', 0.9, 'direct', 'Account management'),
            ControlMapping('NIST_800-53', 'AC-3', 'CIS', '14.1', 0.8, 'direct', 'Access enforcement'),
            ControlMapping('NIST_800-53', 'AU-2', 'CIS', '8.2', 0.9, 'direct', 'Event logging'),
            ControlMapping('NIST_800-53', 'CM-2', 'CIS', '1.1', 0.8, 'direct', 'Baseline configuration'),
            ControlMapping('NIST_800-53', 'IA-2', 'CIS', '16.3', 0.9, 'direct', 'User identification'),
            
            # CIS Controls to ISO 27001
            ControlMapping('CIS', '1.1', 'ISO_27001', 'A.12.6.1', 0.8, 'partial', 'Configuration management'),
            ControlMapping('CIS', '8.2', 'ISO_27001', 'A.12.4.1', 0.9, 'direct', 'Event logging'),
            ControlMapping('CIS', '14.1', 'ISO_27001', 'A.9.4.1', 0.8, 'direct', 'Access control'),
            ControlMapping('CIS', '16.1', 'ISO_27001', 'A.9.2.1', 0.9, 'direct', 'User registration'),
            
            # NIST to ISO 27001
            ControlMapping('NIST_800-53', 'AC-2', 'ISO_27001', 'A.9.2.1', 0.8, 'direct', 'User access management'),
            ControlMapping('NIST_800-53', 'AU-2', 'ISO_27001', 'A.12.4.1', 0.9, 'direct', 'Event logging'),
        ]
        
        self.control_mappings = default_mappings
        logger.info(f"Loaded {len(default_mappings)} default mappings")
    
    def find_mappings(self, framework: str, control_id: str) -> List[ControlMapping]:
        """
        Find all mappings for a specific control.
        
        Args:
            framework: Source framework name
            control_id: Source control identifier
            
        Returns:
            List of mappings for the specified control
        """
        mappings = []
        for mapping in self.control_mappings:
            if (mapping.source_framework == framework and 
                mapping.source_control_id == control_id):
                mappings.append(mapping)
        
        return mappings
    
    def find_reverse_mappings(self, framework: str, control_id: str) -> List[ControlMapping]:
        """
        Find controls that map TO the specified control.
        
        Args:
            framework: Target framework name
            control_id: Target control identifier
            
        Returns:
            List of mappings that target the specified control
        """
        mappings = []
        for mapping in self.control_mappings:
            if (mapping.target_framework == framework and 
                mapping.target_control_id == control_id):
                mappings.append(mapping)
        
        return mappings
    
    def calculate_framework_coverage(self, source_framework: str, 
                                   target_framework: str) -> Dict[str, Any]:
        """
        Calculate coverage between two frameworks.
        
        Args:
            source_framework: Framework to analyze coverage from
            target_framework: Framework to analyze coverage to
            
        Returns:
            Coverage analysis results
        """
        source_controls = set()
        target_controls = set()
        mapped_source_controls = set()
        mapped_target_controls = set()
        
        # Collect all controls and mapped controls
        for mapping in self.control_mappings:
            if mapping.source_framework == source_framework:
                source_controls.add(mapping.source_control_id)
                mapped_source_controls.add(mapping.source_control_id)
                
            if mapping.target_framework == target_framework:
                target_controls.add(mapping.target_control_id)
                mapped_target_controls.add(mapping.target_control_id)
        
        # Add controls from framework definitions
        for control in self.framework_controls[source_framework]:
            source_controls.add(control.control_id)
        for control in self.framework_controls[target_framework]:
            target_controls.add(control.control_id)
        
        # Calculate coverage percentages
        source_coverage = (len(mapped_source_controls) / len(source_controls) * 100 
                          if source_controls else 0)
        target_coverage = (len(mapped_target_controls) / len(target_controls) * 100 
                          if target_controls else 0)
        
        # Find gaps
        unmapped_source = source_controls - mapped_source_controls
        unmapped_target = target_controls - mapped_target_controls
        
        return {
            'source_framework': source_framework,
            'target_framework': target_framework,
            'coverage_metrics': {
                'source_controls_total': len(source_controls),
                'source_controls_mapped': len(mapped_source_controls),
                'source_coverage_percentage': round(source_coverage, 2),
                'target_controls_total': len(target_controls),
                'target_controls_mapped': len(mapped_target_controls),
                'target_coverage_percentage': round(target_coverage, 2)
            },
            'gaps': {
                'unmapped_source_controls': list(unmapped_source),
                'unmapped_target_controls': list(unmapped_target)
            },
            'mapping_quality': self._assess_mapping_quality(source_framework, target_framework)
        }
    
    def _assess_mapping_quality(self, source_framework: str, target_framework: str) -> Dict[str, Any]:
        """Assess the quality of mappings between frameworks."""
        relevant_mappings = [
            m for m in self.control_mappings 
            if m.source_framework == source_framework and m.target_framework == target_framework
        ]
        
        if not relevant_mappings:
            return {'average_strength': 0, 'mapping_types': {}}
        
        strengths = [m.mapping_strength for m in relevant_mappings]
        avg_strength = sum(strengths) / len(strengths)
        
        # Count mapping types
        type_counts = defaultdict(int)
        for mapping in relevant_mappings:
            type_counts[mapping.mapping_type] += 1
        
        return {
            'average_strength': round(avg_strength, 3),
            'total_mappings': len(relevant_mappings),
            'mapping_types': dict(type_counts)
        }
    
    def generate_harmonized_framework(self, frameworks: List[str], 
                                    name: str = "Harmonized Framework") -> Dict[str, Any]:
        """
        Generate a harmonized framework from multiple source frameworks.
        
        Args:
            frameworks: List of framework names to harmonize
            name: Name for the harmonized framework
            
        Returns:
            Harmonized framework definition
        """
        harmonized_controls = {}
        control_sources = defaultdict(list)
        
        # Collect all unique controls across frameworks
        for framework in frameworks:
            for control in self.framework_controls[framework]:
                control_key = f"{control.category}_{control.title}"
                
                if control_key not in harmonized_controls:
                    harmonized_controls[control_key] = {
                        'harmonized_id': f"H-{len(harmonized_controls) + 1}",
                        'title': control.title,
                        'category': control.category,
                        'description': control.description,
                        'severity': control.severity,
                        'source_controls': []
                    }
                
                harmonized_controls[control_key]['source_controls'].append({
                    'framework': framework,
                    'control_id': control.control_id,
                    'description': control.description
                })
        
        # Calculate coverage statistics
        total_controls = sum(len(self.framework_controls[f]) for f in frameworks)
        harmonized_count = len(harmonized_controls)
        consolidation_ratio = total_controls / harmonized_count if harmonized_count > 0 else 0
        
        return {
            'framework_name': name,
            'source_frameworks': frameworks,
            'harmonized_controls': list(harmonized_controls.values()),
            'statistics': {
                'source_control_count': total_controls,
                'harmonized_control_count': harmonized_count,
                'consolidation_ratio': round(consolidation_ratio, 2),
                'framework_coverage': {
                    framework: len(self.framework_controls[framework])
                    for framework in frameworks
                }
            }
        }
    
    def identify_control_overlaps(self, frameworks: List[str]) -> Dict[str, Any]:
        """
        Identify overlapping controls across multiple frameworks.
        
        Args:
            frameworks: List of frameworks to analyze
            
        Returns:
            Analysis of control overlaps
        """
        overlaps = defaultdict(list)
        control_clusters = []
        
        # Find controls that map to each other
        for framework1 in frameworks:
            for framework2 in frameworks:
                if framework1 != framework2:
                    for mapping in self.control_mappings:
                        if (mapping.source_framework == framework1 and 
                            mapping.target_framework == framework2):
                            
                            overlap_key = f"{mapping.source_control_id}_{mapping.target_control_id}"
                            overlaps[overlap_key].append(mapping)
        
        # Group related controls
        processed_controls = set()
        for mapping_group in overlaps.values():
            if not mapping_group:
                continue
                
            cluster = {
                'controls': [],
                'frameworks': set(),
                'mapping_strength': 0
            }
            
            for mapping in mapping_group:
                if mapping.source_control_id not in processed_controls:
                    cluster['controls'].append({
                        'framework': mapping.source_framework,
                        'control_id': mapping.source_control_id
                    })
                    cluster['frameworks'].add(mapping.source_framework)
                    processed_controls.add(mapping.source_control_id)
                
                if mapping.target_control_id not in processed_controls:
                    cluster['controls'].append({
                        'framework': mapping.target_framework,
                        'control_id': mapping.target_control_id
                    })
                    cluster['frameworks'].add(mapping.target_framework)
                    processed_controls.add(mapping.target_control_id)
                
                cluster['mapping_strength'] += mapping.mapping_strength
            
            if len(cluster['controls']) > 1:
                cluster['frameworks'] = list(cluster['frameworks'])
                cluster['mapping_strength'] /= len(mapping_group)
                control_clusters.append(cluster)
        
        return {
            'overlap_analysis': {
                'total_overlapping_controls': len(processed_controls),
                'control_clusters': len(control_clusters),
                'average_cluster_size': (
                    sum(len(c['controls']) for c in control_clusters) / len(control_clusters)
                    if control_clusters else 0
                )
            },
            'clusters': control_clusters,
            'framework_interaction_matrix': self._build_interaction_matrix(frameworks)
        }
    
    def _build_interaction_matrix(self, frameworks: List[str]) -> Dict[str, Dict[str, int]]:
        """Build a matrix showing mapping counts between frameworks."""
        matrix = {f1: {f2: 0 for f2 in frameworks} for f1 in frameworks}
        
        for mapping in self.control_mappings:
            if (mapping.source_framework in frameworks and 
                mapping.target_framework in frameworks):
                matrix[mapping.source_framework][mapping.target_framework] += 1
        
        return matrix
    
    def export_mappings(self, output_file: str = "framework_mappings_export.json"):
        """Export current mappings to a JSON file."""
        export_data = {
            'mappings': [
                {
                    'source_framework': m.source_framework,
                    'source_control': m.source_control_id,
                    'target_framework': m.target_framework,
                    'target_control': m.target_control_id,
                    'strength': m.mapping_strength,
                    'type': m.mapping_type,
                    'notes': m.notes
                }
                for m in self.control_mappings
            ],
            'frameworks': {
                framework: [
                    {
                        'control_id': c.control_id,
                        'title': c.title,
                        'description': c.description,
                        'category': c.category,
                        'severity': c.severity
                    }
                    for c in controls
                ]
                for framework, controls in self.framework_controls.items()
            },
            'export_metadata': {
                'total_mappings': len(self.control_mappings),
                'frameworks_count': len(self.framework_controls),
                'export_date': str(datetime.now())
            }
        }
        
        with open(output_file, 'w') as f:
            json.dump(export_data, f, indent=2)
        
        logger.info(f"Mappings exported to {output_file}")
        return output_file