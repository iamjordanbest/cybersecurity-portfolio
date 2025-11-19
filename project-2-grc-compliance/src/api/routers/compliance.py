"""
Compliance API Router

Endpoints for compliance tracking and reporting.
"""

from fastapi import APIRouter, Depends
from typing import List
from src.api.dependencies import get_database_connection, get_analytics_engine
from src.api.models import ComplianceSummary
from src.analytics.multi_framework_analytics import MultiFrameworkAnalytics

router = APIRouter()


@router.get("/summary", response_model=List[ComplianceSummary])
def get_compliance_summary(analytics: MultiFrameworkAnalytics = Depends(get_analytics_engine)):
    """Get compliance summary across all frameworks."""
    with analytics:
        compliance = analytics.get_unified_compliance_status()
        
        results = []
        for fw_code, status in compliance.items():
            results.append({
                "framework_code": fw_code,
                "framework_name": status['framework_name'],
                "total_controls": status['total_controls'],
                "compliant": status['compliant'],
                "partial": status['partial'],
                "non_compliant": status['non_compliant'],
                "not_assessed": status['not_assessed'],
                "compliance_percentage": status['compliance_percentage']
            })
        
        return results


@router.get("/{framework_code}/status")
def get_framework_compliance(framework_code: str, db = Depends(get_database_connection)):
    """Get compliance status for a specific framework."""
    cursor = db.cursor()
    
    cursor.execute("""
        SELECT 
            COUNT(DISTINCT fc.control_identifier) as total,
            COUNT(DISTINCT CASE WHEN mfa.compliance_status = 'compliant' 
                THEN fc.control_identifier END) as compliant,
            COUNT(DISTINCT CASE WHEN mfa.compliance_status = 'partially_compliant' 
                THEN fc.control_identifier END) as partial,
            COUNT(DISTINCT CASE WHEN mfa.compliance_status = 'non_compliant' 
                THEN fc.control_identifier END) as non_compliant
        FROM framework_controls fc
        JOIN frameworks f ON fc.framework_id = f.framework_id
        LEFT JOIN mf_compliance_assessments mfa ON fc.framework_id = mfa.framework_id
            AND fc.control_identifier = mfa.control_identifier
        WHERE f.framework_code = ?
    """, (framework_code,))
    
    row = cursor.fetchone()
    total, compliant, partial, non_compliant = row[0], row[1], row[2], row[3]
    compliance_pct = (compliant / total * 100) if total > 0 else 0
    
    return {
        "framework_code": framework_code,
        "total_controls": total,
        "compliant": compliant,
        "partial": partial,
        "non_compliant": non_compliant,
        "not_assessed": total - compliant - partial - non_compliant,
        "compliance_percentage": round(compliance_pct, 2)
    }


@router.get("/{framework_code}/gaps")
def get_compliance_gaps(framework_code: str, analytics: MultiFrameworkAnalytics = Depends(get_analytics_engine)):
    """Get compliance gaps for a framework."""
    with analytics:
        gaps = analytics.get_compliance_gaps_across_frameworks()
        
        if framework_code in gaps:
            return gaps[framework_code]
        
        return {"total_gaps": 0, "gaps": []}
