"""
Mappings API Router

Endpoints for cross-framework control mappings.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from src.api.dependencies import get_framework_mapper
from src.api.models import ControlMapping, MappingCreate, CoverageResponse
from src.analytics.framework_mapper import FrameworkMapper

router = APIRouter()


@router.get("/{framework_code}/{control_id}")
def get_control_mappings(
    framework_code: str,
    control_id: str,
    mapper: FrameworkMapper = Depends(get_framework_mapper)
):
    """Get all mappings for a specific control."""
    with mapper:
        mappings = mapper.get_mappings_for_control(framework_code, control_id)
        return {"control": f"{framework_code}:{control_id}", "mappings": mappings}


@router.post("/", status_code=status.HTTP_201_CREATED)
def create_mapping(
    mapping: MappingCreate,
    mapper: FrameworkMapper = Depends(get_framework_mapper)
):
    """Create a new control mapping."""
    with mapper:
        success = mapper.add_mapping(
            source_framework=mapping.source_framework,
            source_control=mapping.source_control,
            target_framework=mapping.target_framework,
            target_control=mapping.target_control,
            mapping_type=mapping.mapping_type,
            mapping_strength=mapping.mapping_strength,
            rationale=mapping.rationale
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to create mapping"
            )
        
        return {"status": "created", "mapping": mapping.dict()}


@router.get("/coverage/{source_framework}/{target_framework}", response_model=CoverageResponse)
def get_framework_coverage(
    source_framework: str,
    target_framework: str,
    mapper: FrameworkMapper = Depends(get_framework_mapper)
):
    """Get coverage between two frameworks."""
    with mapper:
        coverage = mapper.get_framework_coverage(source_framework, target_framework)
        return coverage


@router.get("/gaps/{source_framework}/{target_framework}")
def get_mapping_gaps(
    source_framework: str,
    target_framework: str,
    mapper: FrameworkMapper = Depends(get_framework_mapper)
):
    """Get unmapped controls (gaps) between frameworks."""
    with mapper:
        gaps = mapper.find_gaps(source_framework, target_framework)
        return {
            "source_framework": source_framework,
            "target_framework": target_framework,
            "total_gaps": len(gaps),
            "gaps": gaps[:50]  # Limit to first 50
        }


@router.get("/statistics")
def get_mapping_statistics(mapper: FrameworkMapper = Depends(get_framework_mapper)):
    """Get overall mapping statistics."""
    with mapper:
        stats = mapper.get_mapping_statistics()
        return stats
