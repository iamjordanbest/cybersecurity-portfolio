"""
Pytest Configuration and Shared Fixtures

Provides shared fixtures for all tests including:
- Test database setup
- Mock data generators
- Common test utilities
"""

import pytest
import sqlite3
import tempfile
import shutil
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture(scope='session')
def test_data_dir():
    """Create temporary directory for test data."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)


@pytest.fixture(scope='session')
def test_db_path(test_data_dir):
    """Create a test database with sample data."""
    db_path = test_data_dir / 'test_grc.db'
    
    # Create database with test schema
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    # Create minimal schema for testing
    cursor.executescript('''
        -- Frameworks
        CREATE TABLE frameworks (
            framework_id INTEGER PRIMARY KEY,
            framework_code TEXT UNIQUE NOT NULL,
            framework_name TEXT NOT NULL,
            framework_version TEXT,
            is_active BOOLEAN DEFAULT 1
        );
        
        INSERT INTO frameworks (framework_code, framework_name, framework_version) VALUES
        ('TEST-FW', 'Test Framework', '1.0'),
        ('TEST-FW2', 'Test Framework 2', '1.0');
        
        -- Framework controls
        CREATE TABLE framework_controls (
            fc_id INTEGER PRIMARY KEY,
            framework_id INTEGER NOT NULL,
            control_identifier TEXT NOT NULL,
            control_name TEXT NOT NULL,
            control_description TEXT,
            control_category TEXT,
            priority_level TEXT,
            FOREIGN KEY (framework_id) REFERENCES frameworks(framework_id)
        );
        
        INSERT INTO framework_controls (framework_id, control_identifier, control_name, control_category, priority_level) VALUES
        (1, 'TEST-1', 'Test Control 1', 'Access Control', 'high'),
        (1, 'TEST-2', 'Test Control 2', 'Audit', 'medium'),
        (2, 'TEST2-1', 'Test Control 2-1', 'Access Control', 'high');
        
        -- Control mappings
        CREATE TABLE control_mappings (
            mapping_id INTEGER PRIMARY KEY,
            source_framework_id INTEGER NOT NULL,
            source_control_id TEXT NOT NULL,
            target_framework_id INTEGER NOT NULL,
            target_control_id TEXT NOT NULL,
            mapping_type TEXT,
            mapping_strength REAL,
            mapping_rationale TEXT,
            FOREIGN KEY (source_framework_id) REFERENCES frameworks(framework_id),
            FOREIGN KEY (target_framework_id) REFERENCES frameworks(framework_id)
        );
        
        INSERT INTO control_mappings (source_framework_id, source_control_id, target_framework_id, target_control_id, mapping_type, mapping_strength) VALUES
        (1, 'TEST-1', 2, 'TEST2-1', 'RELATED', 0.8);
        
        -- Compliance assessments
        CREATE TABLE mf_compliance_assessments (
            assessment_id INTEGER PRIMARY KEY,
            framework_id INTEGER NOT NULL,
            control_identifier TEXT NOT NULL,
            assessment_date DATE NOT NULL,
            compliance_status TEXT,
            risk_rating TEXT,
            FOREIGN KEY (framework_id) REFERENCES frameworks(framework_id)
        );
        
        INSERT INTO mf_compliance_assessments (framework_id, control_identifier, assessment_date, compliance_status, risk_rating) VALUES
        (1, 'TEST-1', '2024-01-01', 'compliant', 'low'),
        (1, 'TEST-2', '2024-01-01', 'non_compliant', 'high');
        
        -- Risk scores
        CREATE TABLE mf_control_risk_scores (
            risk_score_id INTEGER PRIMARY KEY,
            framework_id INTEGER NOT NULL,
            control_identifier TEXT NOT NULL,
            priority_score REAL,
            kev_cve_count INTEGER DEFAULT 0,
            attack_technique_count INTEGER DEFAULT 0,
            FOREIGN KEY (framework_id) REFERENCES frameworks(framework_id)
        );
        
        INSERT INTO mf_control_risk_scores (framework_id, control_identifier, priority_score, kev_cve_count) VALUES
        (1, 'TEST-1', 75.5, 5),
        (1, 'TEST-2', 50.0, 2);
    ''')
    
    conn.commit()
    conn.close()
    
    yield str(db_path)


@pytest.fixture
def sample_control_data():
    """Provide sample control data for tests."""
    return {
        'control_id': 'TEST-1',
        'control_name': 'Test Control',
        'control_description': 'Test control description',
        'priority_level': 'high',
        'compliance_status': 'compliant'
    }


@pytest.fixture
def sample_mapping_data():
    """Provide sample mapping data for tests."""
    return {
        'source_framework': 'TEST-FW',
        'source_control': 'TEST-1',
        'target_framework': 'TEST-FW2',
        'target_control': 'TEST2-1',
        'mapping_type': 'RELATED',
        'mapping_strength': 0.8,
        'rationale': 'Test mapping'
    }


@pytest.fixture
def sample_risk_data():
    """Provide sample risk score data for tests."""
    return {
        'control_id': 'TEST-1',
        'base_risk_score': 50.0,
        'threat_adjusted_score': 65.0,
        'priority_score': 75.5,
        'kev_cve_count': 5,
        'attack_technique_count': 10
    }
