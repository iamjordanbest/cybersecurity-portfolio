import boto3
import logging
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from abc import ABC, abstractmethod
from botocore.exceptions import ClientError
from models.compliance import Control, AssessmentResult, ControlStatus, EvidenceArtifact, Finding

logger = logging.getLogger(__name__)

class BaseAuditor(ABC):
    """
    Abstract base class for all compliance auditors.
    Handles AWS session management and common evidence collection.
    """
    
    def __init__(self, session: boto3.Session):
        self.session = session
        self.region = session.region_name
        self.account_id = session.client('sts').get_caller_identity()['Account']
        self._setup_clients()

    @abstractmethod
    def _setup_clients(self):
        """Initialize necessary boto3 clients"""
        pass

    @abstractmethod
    def audit_all(self) -> List[AssessmentResult]:
        """Run all controls for this auditor"""
        pass

    def create_assessment(self, 
                         control: Control, 
                         status: ControlStatus, 
                         findings: List[Finding] = None,
                         evidence: List[EvidenceArtifact] = None,
                         notes: str = None) -> AssessmentResult:
        """Helper to create a standardized assessment result"""
        return AssessmentResult(
            control_id=control.control_id,
            status=status,
            timestamp=datetime.now(),
            score=100.0 if status == ControlStatus.PASS else 0.0,
            findings=findings or [],
            evidence=evidence or [],
            notes=notes
        )

    def save_evidence(self, filename: str, content: Any) -> str:
        """
        Save evidence to disk and return path.
        In a real app, this might upload to S3.
        """
        # For now, we'll just return the content as a string representation
        # Implementation for file saving would go here
        if isinstance(content, (dict, list)):
            return json.dumps(content, default=str, indent=2)
        return str(content)

    def handle_error(self, control_id: str, error: Exception) -> AssessmentResult:
        """Standard error handler"""
        logger.error(f"Error auditing {control_id}: {str(error)}")
        return AssessmentResult(
            control_id=control_id,
            status=ControlStatus.ERROR,
            timestamp=datetime.now(),
            notes=f"Error: {str(error)}"
        )
