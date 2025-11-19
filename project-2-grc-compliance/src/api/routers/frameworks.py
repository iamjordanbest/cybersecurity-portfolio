"""
Frameworks API Router

Endpoints for managing and querying compliance frameworks.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from src.api.dependencies import get_database_connection
from src.api.models import FrameworkResponse

router = APIRouter()


@router.get("/", response_model=List[FrameworkResponse])
def list_frameworks(db = Depends(get_database_connection)):
    """Get list of all available frameworks."""
    cursor = db.cursor()
    cursor.execute("""
        SELECT 
            f.framework_id,
            f.framework_code,
            f.framework_name,
            f.framework_version,
            f.is_active,
            COUNT(fc.fc_id) as control_count
        FROM frameworks f
        LEFT JOIN framework_controls fc ON f.framework_id = fc.framework_id
        WHERE f.is_active = 1
        GROUP BY f.framework_id
        ORDER BY f.framework_code
    """)
    
    frameworks = []
    for row in cursor.fetchall():
        frameworks.append({
            "framework_id": row[0],
            "framework_code": row[1],
            "framework_name": row[2],
            "framework_version": row[3],
            "is_active": row[4],
            "control_count": row[5]
        })
    
    return frameworks


@router.get("/{framework_code}", response_model=FrameworkResponse)
def get_framework(framework_code: str, db = Depends(get_database_connection)):
    """Get details of a specific framework."""
    cursor = db.cursor()
    cursor.execute("""
        SELECT 
            f.framework_id,
            f.framework_code,
            f.framework_name,
            f.framework_version,
            f.is_active,
            COUNT(fc.fc_id) as control_count
        FROM frameworks f
        LEFT JOIN framework_controls fc ON f.framework_id = fc.framework_id
        WHERE f.framework_code = ? AND f.is_active = 1
        GROUP BY f.framework_id
    """, (framework_code,))
    
    row = cursor.fetchone()
    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Framework '{framework_code}' not found"
        )
    
    return {
        "framework_id": row[0],
        "framework_code": row[1],
        "framework_name": row[2],
        "framework_version": row[3],
        "is_active": row[4],
        "control_count": row[5]
    }


@router.get("/{framework_code}/stats")
def get_framework_stats(framework_code: str, db = Depends(get_database_connection)):
    """Get statistics for a framework."""
    cursor = db.cursor()
    
    # Verify framework exists
    cursor.execute(
        "SELECT framework_id FROM frameworks WHERE framework_code = ? AND is_active = 1",
        (framework_code,)
    )
    fw = cursor.fetchone()
    if not fw:
        raise HTTPException(status_code=404, detail="Framework not found")
    
    fw_id = fw[0]
    
    # Get control count by priority
    cursor.execute("""
        SELECT priority_level, COUNT(*) as cnt
        FROM framework_controls
        WHERE framework_id = ?
        GROUP BY priority_level
    """, (fw_id,))
    
    priority_dist = {row[0]: row[1] for row in cursor.fetchall()}
    
    # Get total controls
    cursor.execute("SELECT COUNT(*) FROM framework_controls WHERE framework_id = ?", (fw_id,))
    total_controls = cursor.fetchone()[0]
    
    return {
        "framework_code": framework_code,
        "total_controls": total_controls,
        "priority_distribution": priority_dist
    }
