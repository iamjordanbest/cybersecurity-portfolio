"""
Pydantic Models for API Request/Response

Defines data models for API endpoints with validation.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import date


# Framework Models
class FrameworkBase(BaseModel):
    """Base framework model."""
    framework_code: str = Field(..., example="NIST-800-53")
    framework_name: str = Field(..., example="NIST Special Publication 800-53")
    framework_version: str = Field(..., example="Revision 5")
    
class FrameworkResponse(FrameworkBase):
    """Framework response model."""
    framework_id: int
    control_count: int
    is_active: bool
    
    class Config:
        from_attributes = True


# Control Models
class ControlBase(BaseModel):
    """Base control model."""
    control_identifier: str = Field(..., example="AC-1")
    control_name: str = Field(..., example="Access Control Policy and Procedures")
    control_description: Optional[str] = None
    control_category: Optional[str] = Field(None, example="Access Control")
    priority_level: Optional[str] = Field(None, example="high")

class ControlResponse(ControlBase):
    """Control response model."""
    framework_code: str
    
    class Config:
        from_attributes = True


# Compliance Models
class ComplianceStatus(BaseModel):
    """Compliance status model."""
    framework_code: str
    control_identifier: str
    compliance_status: str = Field(..., example="compliant")
    assessment_date: date
    risk_rating: Optional[str] = Field(None, example="low")

class ComplianceSummary(BaseModel):
    """Compliance summary model."""
    framework_code: str
    framework_name: str
    total_controls: int
    compliant: int
    partial: int
    non_compliant: int
    not_assessed: int
    compliance_percentage: float


# Risk Models
class RiskScore(BaseModel):
    """Risk score model."""
    control_id: str
    priority_score: float
    kev_cve_count: int
    attack_technique_count: int
    compliance_status: Optional[str] = None

class RiskSummary(BaseModel):
    """Risk summary model."""
    framework_code: str
    total_scored: int
    avg_priority_score: float
    critical_risk: int
    high_risk: int
    medium_risk: int
    low_risk: int


# Mapping Models
class ControlMapping(BaseModel):
    """Control mapping model."""
    source_framework: str
    source_control: str
    target_framework: str
    target_control: str
    mapping_type: str = Field(..., example="EXACT")
    mapping_strength: float = Field(..., ge=0.0, le=1.0)
    
class MappingCreate(BaseModel):
    """Create mapping request."""
    source_framework: str = Field(..., example="NIST-800-53")
    source_control: str = Field(..., example="AC-1")
    target_framework: str = Field(..., example="ISO-27001")
    target_control: str = Field(..., example="A.9.1.1")
    mapping_type: str = Field(..., example="RELATED")
    mapping_strength: float = Field(..., ge=0.0, le=1.0, example=0.8)
    rationale: Optional[str] = Field(None, example="Both address access control policies")

class CoverageResponse(BaseModel):
    """Framework coverage response."""
    source_framework: str
    target_framework: str
    source_total_controls: int
    source_mapped_controls: int
    source_coverage_pct: float
    target_total_controls: int
    target_mapped_controls: int
    target_coverage_pct: float
    total_mappings: int


# Analytics Models
class AnalyticsResponse(BaseModel):
    """Generic analytics response."""
    status: str = "success"
    data: Dict
    
class ErrorResponse(BaseModel):
    """Error response model."""
    error: str
    detail: Optional[str] = None
