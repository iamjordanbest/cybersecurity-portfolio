"""
Unit tests for FrameworkMapper class.

Tests the cross-framework mapping functionality including:
- Adding mappings
- Querying mappings
- Coverage calculations
- Gap analysis
"""

import pytest
from src.analytics.framework_mapper import FrameworkMapper


@pytest.mark.unit
@pytest.mark.database
class TestFrameworkMapper:
    """Test suite for FrameworkMapper class."""
    
    def test_mapper_initialization(self, test_db_path):
        """Test mapper can be initialized with database path."""
        mapper = FrameworkMapper(test_db_path)
        assert mapper.db_path == test_db_path
        assert mapper.conn is None  # Not connected yet
    
    def test_mapper_context_manager(self, test_db_path):
        """Test mapper works as context manager."""
        with FrameworkMapper(test_db_path) as mapper:
            assert mapper.conn is not None
        # Connection should be closed after context
        
    def test_add_mapping(self, test_db_path, sample_mapping_data):
        """Test adding a new mapping."""
        with FrameworkMapper(test_db_path) as mapper:
            result = mapper.add_mapping(
                source_framework=sample_mapping_data['source_framework'],
                source_control=sample_mapping_data['source_control'],
                target_framework=sample_mapping_data['target_framework'],
                target_control=sample_mapping_data['target_control'],
                mapping_type=sample_mapping_data['mapping_type'],
                mapping_strength=sample_mapping_data['mapping_strength'],
                rationale=sample_mapping_data['rationale']
            )
            assert result is True
    
    def test_add_mapping_invalid_framework(self, test_db_path):
        """Test adding mapping with invalid framework fails gracefully."""
        with FrameworkMapper(test_db_path) as mapper:
            result = mapper.add_mapping(
                source_framework='INVALID-FW',
                source_control='TEST-1',
                target_framework='TEST-FW2',
                target_control='TEST2-1',
                mapping_type='RELATED',
                mapping_strength=0.8
            )
            assert result is False
    
    def test_get_mappings_for_control(self, test_db_path):
        """Test retrieving mappings for a control."""
        with FrameworkMapper(test_db_path) as mapper:
            mappings = mapper.get_mappings_for_control('TEST-FW', 'TEST-1')
            assert isinstance(mappings, list)
            # Should have at least the test mapping
            assert len(mappings) >= 1
    
    def test_get_mappings_bidirectional(self, test_db_path):
        """Test bidirectional mapping queries."""
        with FrameworkMapper(test_db_path) as mapper:
            # Get outbound mappings
            outbound = mapper.get_mappings_for_control('TEST-FW', 'TEST-1', direction='source')
            
            # Get inbound mappings for target
            inbound = mapper.get_mappings_for_control('TEST-FW2', 'TEST2-1', direction='target')
            
            # Should find the TEST-1 -> TEST2-1 mapping in both
            assert len(outbound) > 0
            assert len(inbound) > 0
    
    def test_get_framework_coverage(self, test_db_path):
        """Test framework coverage calculation."""
        with FrameworkMapper(test_db_path) as mapper:
            coverage = mapper.get_framework_coverage('TEST-FW', 'TEST-FW2')
            
            assert 'source_total_controls' in coverage
            assert 'target_total_controls' in coverage
            assert 'source_coverage_pct' in coverage
            assert 'target_coverage_pct' in coverage
            assert 'total_mappings' in coverage
            
            # Coverage percentages should be between 0 and 100
            assert 0 <= coverage['source_coverage_pct'] <= 100
            assert 0 <= coverage['target_coverage_pct'] <= 100
    
    def test_find_gaps(self, test_db_path):
        """Test gap analysis functionality."""
        with FrameworkMapper(test_db_path) as mapper:
            gaps = mapper.find_gaps('TEST-FW', 'TEST-FW2')
            
            assert isinstance(gaps, list)
            # Each gap should have required fields
            for gap in gaps:
                assert 'control_id' in gap
                assert 'control_name' in gap
                assert 'priority' in gap
    
    def test_get_mapping_statistics(self, test_db_path):
        """Test mapping statistics retrieval."""
        with FrameworkMapper(test_db_path) as mapper:
            stats = mapper.get_mapping_statistics()
            
            assert 'total_mappings' in stats
            assert 'by_type' in stats
            assert 'by_framework_pair' in stats
            assert 'average_strength' in stats
            
            # Total mappings should be non-negative
            assert stats['total_mappings'] >= 0
            
            # Average strength should be between 0 and 1
            if stats['average_strength']:
                assert 0 <= stats['average_strength'] <= 1


@pytest.mark.unit
class TestMappingValidation:
    """Test mapping data validation."""
    
    def test_mapping_strength_valid_range(self, test_db_path):
        """Test mapping strength must be between 0 and 1."""
        with FrameworkMapper(test_db_path) as mapper:
            # Valid strength should work
            result = mapper.add_mapping(
                'TEST-FW', 'TEST-1', 'TEST-FW2', 'TEST2-1',
                'RELATED', 0.5
            )
            assert result is True
    
    def test_mapping_type_validation(self, test_db_path):
        """Test mapping types are properly stored."""
        valid_types = ['EXACT', 'PARTIAL', 'RELATED', 'COMPLEMENTARY']
        
        with FrameworkMapper(test_db_path) as mapper:
            for mapping_type in valid_types:
                result = mapper.add_mapping(
                    'TEST-FW', 'TEST-1', 'TEST-FW2', 'TEST2-1',
                    mapping_type, 0.8
                )
                # Should succeed for valid types
                assert result is True
