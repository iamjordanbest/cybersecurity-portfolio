from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Any, Dict
from enum import Enum

class ControlStatus(Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    ERROR = "ERROR"
    MANUAL = "MANUAL"

class Severity(Enum):
    CRITICAL = "Critical"
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"

@dataclass
class Control:
    control_id: str
    title: str
    description: str
    severity: Severity
    category: str
    cis_reference: str

@dataclass
class EvidenceArtifact:
    control_id: str
    artifact_type: str  # "api_output", "screenshot", "terraform_state"
    description: str
    content: Any  # JSON, text, or path to file
    timestamp: datetime = field(default_factory=datetime.now)

@dataclass
class Finding:
    control_id: str
    severity: Severity
    description: str
    remediation: str
    resource_id: Optional[str] = None

@dataclass
class AssessmentResult:
    control_id: str
    status: ControlStatus
    timestamp: datetime
    score: float = 0.0
    findings: List[Finding] = field(default_factory=list)
    evidence: List[EvidenceArtifact] = field(default_factory=list)
    notes: Optional[str] = None
