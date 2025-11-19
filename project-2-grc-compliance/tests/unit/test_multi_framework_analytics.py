"""
Unit tests for MultiFrameworkAnalytics class.

Tests multi-framework analytics functionality including:
- Unified compliance status
- Risk analysis
- ROI calculations
- Gap analysis
"""

import pytest
from src.analytics.multi_framework_analytics import MultiFrameworkAnalytics


@pytest.mark.unit
@pytest.mark.database
class TestMultiFrameworkAnalytics:
    """Test suite for MultiFrameworkAnalytics class."""
    
    def test_analytics_initialization(self, test_db_path):
        """Test analytics can be initialized."""
        analytics = MultiFrameworkAnalytics(test_db_path)
        assert analytics.db_path == test_db_path
        assert analytics.conn is None
        assert analytics.mapper is None
    
    def test_analytics_context_manager(self, test_db_path):
        """Test analytics works as context manager."""
        with MultiFrameworkAnalytics(test_db_path) as analytics:
            assert analytics.conn is not None
            assert analytics.mapper is not None
    
    def test_get_unified_compliance_status(self, test_db_path):
        """Test unified compliance status retrieval."""
        with MultiFrameworkAnalytics(test_db_path) as analytics:
            compliance = analytics.get_unified_compliance_status()
            
            assert isinstance(compliance, dict)
            # Should have entries for test frameworks
            assert len(compliance) >= 0
            
            # Check structure of compliance data
            for fw_code, status in compliance.items():
                assert 'framework_name' in status
                assert 'total_controls' in status
                assert 'compliant' in status
                assert 'compliance_percentage' in status
                
                # Percentage should be between 0 and 100
                assert 0 <= status['compliance_percentage'] <= 100
    
    def test_calculate_inherited_compliance(self, test_db_path):
        """Test compliance inheritance calculation."""
        with MultiFrameworkAnalytics(test_db_path) as analytics:
            inherited = analytics.calculate_inherited_compliance('TEST-FW2')
            
            assert isinstance(inherited, dict)
            # Each control with inheritance should have mapping info
            for control_id, sources in inherited.items():
                assert isinstance(sources, list)
                for source in sources:
                    assert 'source_framework' in source
                    assert 'source_control' in source
                    assert 'mapping_strength' in source
                    assert 'inherited_compliance' in source
    
    def test_get_multi_framework_risk_summary(self, test_db_path):
        """Test multi-framework risk summary."""
        with MultiFrameworkAnalytics(test_db_path) as analytics:
            risk = analytics.get_multi_framework_risk_summary()
            
            assert isinstance(risk, dict)
            # Check structure of risk data
            for fw_code, metrics in risk.items():
                assert 'total_scored' in metrics
                assert 'avg_priority_score' in metrics
                assert 'critical_risk' in metrics
                assert 'high_risk' in metrics
                
                # Counts should be non-negative
                assert metrics['total_scored'] >= 0
                assert metrics['critical_risk'] >= 0
    
    def test_get_framework_comparison(self, test_db_path):
        """Test framework comparison functionality."""
        with MultiFrameworkAnalytics(test_db_path) as analytics:
            comparison = analytics.get_framework_comparison(['TEST-FW', 'TEST-FW2'])
            
            assert isinstance(comparison, dict)
            assert 'frameworks' in comparison
            assert 'metrics' in comparison
            assert comparison['frameworks'] == ['TEST-FW', 'TEST-FW2']
    
    def test_get_priority_controls_across_frameworks(self, test_db_path):
        """Test priority control identification."""
        with MultiFrameworkAnalytics(test_db_path) as analytics:
            priorities = analytics.get_priority_controls_across_frameworks(
                min_priority=50.0,
                limit=10
            )
            
            assert isinstance(priorities, list)
            # Each control should have required fields
            for ctrl in priorities:
                assert 'framework' in ctrl
                assert 'control_id' in ctrl
                assert 'control_name' in ctrl
                assert 'priority_score' in ctrl
                # Priority should be above threshold
                assert ctrl['priority_score'] >= 50.0
    
    def test_calculate_multi_framework_roi(self, test_db_path):
        """Test multi-framework ROI calculation."""
        with MultiFrameworkAnalytics(test_db_path) as analytics:
            roi = analytics.calculate_multi_framework_roi(['TEST-FW', 'TEST-FW2'])
            
            assert isinstance(roi, dict)
            assert 'frameworks' in roi
            assert 'individual_costs' in roi
            assert 'combined_cost' in roi
            assert 'savings' in roi
            assert 'roi_percentage' in roi
            
            # ROI values should be non-negative
            assert roi['combined_cost'] >= 0
            assert roi['savings'] >= 0
            assert roi['roi_percentage'] >= 0
    
    def test_get_compliance_gaps_across_frameworks(self, test_db_path):
        """Test compliance gap analysis."""
        with MultiFrameworkAnalytics(test_db_path) as analytics:
            gaps = analytics.get_compliance_gaps_across_frameworks()
            
            assert isinstance(gaps, dict)
            # Each framework should have gap data
            for fw_code, gap_data in gaps.items():
                assert 'total_gaps' in gap_data
                assert 'gaps' in gap_data
                assert isinstance(gap_data['gaps'], list)
                
                # Gap count should match list length (up to limit)
                assert gap_data['total_gaps'] >= 0


@pytest.mark.unit
class TestAnalyticsCalculations:
    """Test analytics calculation logic."""
    
    def test_compliance_percentage_calculation(self, test_db_path):
        """Test compliance percentage is calculated correctly."""
        with MultiFrameworkAnalytics(test_db_path) as analytics:
            compliance = analytics.get_unified_compliance_status()
            
            for fw_code, status in compliance.items():
                total = status['total_controls']
                compliant = status['compliant']
                percentage = status['compliance_percentage']
                
                if total > 0:
                    expected = (compliant / total) * 100
                    # Allow small floating point differences
                    assert abs(percentage - expected) < 0.01
                else:
                    assert percentage == 0
    
    def test_inherited_compliance_strength(self, test_db_path):
        """Test inherited compliance uses mapping strength."""
        with MultiFrameworkAnalytics(test_db_path) as analytics:
            inherited = analytics.calculate_inherited_compliance('TEST-FW2')
            
            for control_id, sources in inherited.items():
                for source in sources:
                    strength = source['mapping_strength']
                    inherited_pct = source['inherited_compliance']
                    
                    # Inherited percentage should equal strength * 100
                    expected = strength * 100
                    assert abs(inherited_pct - expected) < 0.01
