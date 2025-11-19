"""
Risk API Router

Endpoints for risk assessment and analysis.
"""

from fastapi import APIRouter, Depends, Query
from typing import List
from src.api.dependencies import get_analytics_engine
from src.api.models import RiskSummary, RiskScore
from src.analytics.multi_framework_analytics import MultiFrameworkAnalytics

router = APIRouter()


@router.get("/summary", response_model=List[RiskSummary])
def get_risk_summary(analytics: MultiFrameworkAnalytics = Depends(get_analytics_engine)):
    """Get risk summary across all frameworks."""
    with analytics:
        risk = analytics.get_multi_framework_risk_summary()
        
        results = []
        for fw_code, metrics in risk.items():
            results.append({
                "framework_code": fw_code,
                "total_scored": metrics['total_scored'],
                "avg_priority_score": metrics['avg_priority_score'],
                "critical_risk": metrics['critical_risk'],
                "high_risk": metrics['high_risk'],
                "medium_risk": metrics['medium_risk'],
                "low_risk": metrics['low_risk']
            })
        
        return results


@router.get("/priority-controls", response_model=List[RiskScore])
def get_priority_controls(
    min_priority: float = Query(50.0, ge=0, le=100),
    limit: int = Query(20, ge=1, le=100),
    analytics: MultiFrameworkAnalytics = Depends(get_analytics_engine)
):
    """Get highest priority controls across all frameworks."""
    with analytics:
        priorities = analytics.get_priority_controls_across_frameworks(
            min_priority=min_priority,
            limit=limit
        )
        
        results = []
        for ctrl in priorities:
            results.append({
                "control_id": f"{ctrl['framework']}:{ctrl['control_id']}",
                "priority_score": ctrl['priority_score'],
                "kev_cve_count": ctrl['kev_count'],
                "attack_technique_count": ctrl['attack_techniques'],
                "compliance_status": ctrl['compliance_status']
            })
        
        return results


@router.get("/{framework_code}/summary")
def get_framework_risk(framework_code: str, analytics: MultiFrameworkAnalytics = Depends(get_analytics_engine)):
    """Get risk summary for a specific framework."""
    with analytics:
        risk = analytics.get_multi_framework_risk_summary()
        
        if framework_code in risk:
            return risk[framework_code]
        
        return {
            "framework_code": framework_code,
            "total_scored": 0,
            "avg_priority_score": 0,
            "critical_risk": 0,
            "high_risk": 0,
            "medium_risk": 0,
            "low_risk": 0
        }

from pydantic import BaseModel
from src.analytics.risk_scorer import RiskScorer

class ControlInput(BaseModel):
    control_id: str
    status: str = "not_tested"
    control_weight: float = 1.0
    business_impact: str = "medium"

@router.post("/calculate")
def calculate_risk(control: ControlInput):
    """
    Calculate risk score for a specific control using the configurable RiskScorer.
    """
    scorer = RiskScorer()
    score = scorer.calculate_risk_score(control.dict())
    return {
        "control_id": control.control_id,
        "risk_score": score,
        "factors": {
            "weight": control.control_weight,
            "status": control.status,
            "impact": control.business_impact
        }
    }
