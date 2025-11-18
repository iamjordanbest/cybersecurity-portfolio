"""
Data models for GRC Analytics Platform

Defines data structures and validation for database entities.
"""

from dataclasses import dataclass, field
from datetime import datetime, date
from typing import Optional, List, Dict, Any
from enum import Enum


class ImplementationStatus(str, Enum):
    """Control implementation status."""
    NOT_IMPLEMENTED = 'not_implemented'
    PLANNED = 'planned'
    PARTIALLY_IMPLEMENTED = 'partially_implemented'
    IMPLEMENTED = 'implemented'
    NOT_APPLICABLE = 'not_applicable'


class RiskLevel(str, Enum):
    """Risk level classification."""
    CRITICAL = 'critical'
    HIGH = 'high'
    MEDIUM = 'medium'
    LOW = 'low'
    INFO = 'info'


class Framework(str, Enum):
    """Compliance frameworks."""
    NIST_800_53 = 'NIST_800_53'
    NIST_800_171 = 'NIST_800_171'
    CIS = 'CIS'
    ISO_27001 = 'ISO_27001'
    SOC2 = 'SOC2'
    PCI_DSS = 'PCI_DSS'


@dataclass
class Control:
    """
    Security control definition.
    """
    control_id: str
    framework: str
    family: str
    title: str
    description: str
    priority: str = 'P2'
    baseline: Optional[str] = None
    id: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'id': self.id,
            'control_id': self.control_id,
            'framework': self.framework,
            'family': self.family,
            'title': self.title,
            'description': self.description,
            'priority': self.priority,
            'baseline': self.baseline
        }


@dataclass
class ControlAssessment:
    """
    Assessment of a control's implementation status.
    """
    control_id: str
    assessment_date: date
    implementation_status: str
    compliance_score: float
    evidence_quality: float
    risk_level: str
    assessor: str
    notes: Optional[str] = None
    remediation_deadline: Optional[date] = None
    id: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'id': self.id,
            'control_id': self.control_id,
            'assessment_date': self.assessment_date.isoformat() if isinstance(self.assessment_date, date) else self.assessment_date,
            'implementation_status': self.implementation_status,
            'compliance_score': self.compliance_score,
            'evidence_quality': self.evidence_quality,
            'risk_level': self.risk_level,
            'assessor': self.assessor,
            'notes': self.notes,
            'remediation_deadline': self.remediation_deadline.isoformat() if isinstance(self.remediation_deadline, date) else self.remediation_deadline
        }


@dataclass
class Vulnerability:
    """
    Vulnerability information from NVD/CISA KEV.
    """
    cve_id: str
    description: str
    cvss_score: float
    severity: str
    published_date: date
    is_kev: bool = False
    exploit_available: bool = False
    vendor: Optional[str] = None
    product: Optional[str] = None
    cwe_id: Optional[str] = None
    id: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'id': self.id,
            'cve_id': self.cve_id,
            'description': self.description,
            'cvss_score': self.cvss_score,
            'severity': self.severity,
            'published_date': self.published_date.isoformat() if isinstance(self.published_date, date) else self.published_date,
            'is_kev': self.is_kev,
            'exploit_available': self.exploit_available,
            'vendor': self.vendor,
            'product': self.product,
            'cwe_id': self.cwe_id
        }


@dataclass
class ThreatMapping:
    """
    Mapping between vulnerabilities, MITRE ATT&CK, and controls.
    """
    control_id: str
    mitre_technique_id: Optional[str] = None
    cve_id: Optional[str] = None
    mapping_confidence: float = 0.8
    mapping_source: str = 'automated'
    notes: Optional[str] = None
    id: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'id': self.id,
            'control_id': self.control_id,
            'mitre_technique_id': self.mitre_technique_id,
            'cve_id': self.cve_id,
            'mapping_confidence': self.mapping_confidence,
            'mapping_source': self.mapping_source,
            'notes': self.notes
        }


@dataclass
class ComplianceScore:
    """
    Aggregated compliance score for a framework or domain.
    """
    framework: str
    domain: str
    score_date: date
    overall_score: float
    controls_total: int
    controls_implemented: int
    controls_partial: int
    controls_not_implemented: int
    risk_score: float
    trend: Optional[str] = None
    id: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'id': self.id,
            'framework': self.framework,
            'domain': self.domain,
            'score_date': self.score_date.isoformat() if isinstance(self.score_date, date) else self.score_date,
            'overall_score': self.overall_score,
            'controls_total': self.controls_total,
            'controls_implemented': self.controls_implemented,
            'controls_partial': self.controls_partial,
            'controls_not_implemented': self.controls_not_implemented,
            'risk_score': self.risk_score,
            'trend': self.trend
        }


@dataclass
class RemediationPlan:
    """
    Remediation plan for addressing control gaps.
    """
    control_id: str
    priority: str
    estimated_effort_hours: float
    estimated_cost: float
    expected_risk_reduction: float
    roi_score: float
    recommended_actions: str
    assigned_to: Optional[str] = None
    target_completion_date: Optional[date] = None
    status: str = 'pending'
    id: Optional[int] = None
    created_date: Optional[date] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'id': self.id,
            'control_id': self.control_id,
            'priority': self.priority,
            'estimated_effort_hours': self.estimated_effort_hours,
            'estimated_cost': self.estimated_cost,
            'expected_risk_reduction': self.expected_risk_reduction,
            'roi_score': self.roi_score,
            'recommended_actions': self.recommended_actions,
            'assigned_to': self.assigned_to,
            'target_completion_date': self.target_completion_date.isoformat() if isinstance(self.target_completion_date, date) else self.target_completion_date,
            'status': self.status,
            'created_date': self.created_date.isoformat() if isinstance(self.created_date, date) else self.created_date
        }
