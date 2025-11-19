"""
Controls API Router

Endpoints for querying and managing framework controls.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from src.api.dependencies import get_database_connection, verify_framework_exists
from src.api.models import ControlResponse

router = APIRouter()


@router.get("/{framework_code}", response_model=List[ControlResponse])
def list_controls(
    framework_code: str,
    category: Optional[str] = None,
    priority: Optional[str] = None,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db = Depends(get_database_connection)
):
    """Get list of controls for a framework."""
    cursor = db.cursor()
    
    # Build query
    query = """
        SELECT 
            f.framework_code,
            fc.control_identifier,
            fc.control_name,
            fc.control_description,
            fc.control_category,
            fc.priority_level
        FROM framework_controls fc
        JOIN frameworks f ON fc.framework_id = f.framework_id
        WHERE f.framework_code = ? AND f.is_active = 1
    """
    params = [framework_code]
    
    if category:
        query += " AND fc.control_category = ?"
        params.append(category)
    
    if priority:
        query += " AND fc.priority_level = ?"
        params.append(priority)
    
    query += " ORDER BY fc.control_identifier LIMIT ? OFFSET ?"
    params.extend([limit, offset])
    
    cursor.execute(query, params)
    
    controls = []
    for row in cursor.fetchall():
        controls.append({
            "framework_code": row[0],
            "control_identifier": row[1],
            "control_name": row[2],
            "control_description": row[3],
            "control_category": row[4],
            "priority_level": row[5]
        })
    
    return controls


@router.get("/{framework_code}/{control_id}", response_model=ControlResponse)
def get_control(framework_code: str, control_id: str, db = Depends(get_database_connection)):
    """Get details of a specific control."""
    cursor = db.cursor()
    cursor.execute("""
        SELECT 
            f.framework_code,
            fc.control_identifier,
            fc.control_name,
            fc.control_description,
            fc.control_category,
            fc.priority_level
        FROM framework_controls fc
        JOIN frameworks f ON fc.framework_id = f.framework_id
        WHERE f.framework_code = ? AND fc.control_identifier = ?
    """, (framework_code, control_id))
    
    row = cursor.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Control not found")
    
    return {
        "framework_code": row[0],
        "control_identifier": row[1],
        "control_name": row[2],
        "control_description": row[3],
        "control_category": row[4],
        "priority_level": row[5]
    }
