-- GRC Analytics Database Schema
-- SQLite Database Schema for Compliance Control Management
-- Version: 1.0
-- Created: 2024-11-03

-- =============================================================================
-- TABLE: nist_controls (Reference Table)
-- Description: NIST 800-53 Rev 5 control catalog
-- =============================================================================

CREATE TABLE IF NOT EXISTS nist_controls (
    nist_control_id TEXT PRIMARY KEY NOT NULL,
    family TEXT NOT NULL,
    family_code TEXT NOT NULL,
    control_name TEXT NOT NULL,
    control_description TEXT,
    baseline TEXT CHECK(baseline IN ('low', 'moderate', 'high')),
    control_type TEXT CHECK(control_type IN ('preventive', 'detective', 'corrective'))
);

-- =============================================================================
-- TABLE: controls (Main Control Registry)
-- Description: Current state of all compliance controls
-- =============================================================================

CREATE TABLE IF NOT EXISTS controls (
    control_id TEXT PRIMARY KEY NOT NULL,
    control_name TEXT NOT NULL,
    control_description TEXT,
    status TEXT NOT NULL CHECK(status IN ('pass', 'warn', 'fail', 'not_tested', 'not_applicable')),
    owner TEXT NOT NULL,
    last_test_date DATE,
    next_test_due DATE,
    evidence TEXT,
    control_weight REAL CHECK(control_weight >= 1.0 AND control_weight <= 10.0),
    nist_control_id TEXT,
    nist_family TEXT NOT NULL,
    test_frequency TEXT CHECK(test_frequency IN ('monthly', 'quarterly', 'annual')),
    automated INTEGER CHECK(automated IN (0, 1)),
    remediation_cost TEXT CHECK(remediation_cost IN ('low', 'medium', 'high')),
    business_impact TEXT CHECK(business_impact IN ('critical', 'high', 'medium', 'low')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (nist_control_id) REFERENCES nist_controls(nist_control_id)
);

-- =============================================================================
-- TABLE: audit_history (Time Series Data)
-- Description: Historical audit records for trend analysis
-- =============================================================================

CREATE TABLE IF NOT EXISTS audit_history (
    audit_id TEXT PRIMARY KEY NOT NULL,
    control_id TEXT NOT NULL,
    test_date DATE NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('pass', 'warn', 'fail', 'not_tested', 'not_applicable')),
    auditor TEXT NOT NULL,
    notes TEXT,
    evidence_url TEXT,
    FOREIGN KEY (control_id) REFERENCES controls(control_id)
);

-- =============================================================================
-- TABLE: risk_scores (Calculated Metrics)
-- Description: Stores calculated risk scores over time
-- =============================================================================

CREATE TABLE IF NOT EXISTS risk_scores (
    score_id TEXT PRIMARY KEY NOT NULL,
    control_id TEXT NOT NULL,
    risk_score REAL NOT NULL,
    compliance_score REAL,
    calculated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    factors TEXT,  -- JSON object with calculation factors
    FOREIGN KEY (control_id) REFERENCES controls(control_id)
);

-- =============================================================================
-- INDEXES: Performance optimization
-- =============================================================================

-- Controls table indexes
CREATE INDEX IF NOT EXISTS idx_controls_status ON controls(status);
CREATE INDEX IF NOT EXISTS idx_controls_nist_family ON controls(nist_family);
CREATE INDEX IF NOT EXISTS idx_controls_owner ON controls(owner);
CREATE INDEX IF NOT EXISTS idx_controls_nist_control_id ON controls(nist_control_id);
CREATE INDEX IF NOT EXISTS idx_controls_business_impact ON controls(business_impact);
CREATE INDEX IF NOT EXISTS idx_controls_next_test_due ON controls(next_test_due);

-- NIST controls table indexes
CREATE INDEX IF NOT EXISTS idx_nist_family_code ON nist_controls(family_code);
CREATE INDEX IF NOT EXISTS idx_nist_baseline ON nist_controls(baseline);
CREATE INDEX IF NOT EXISTS idx_nist_control_type ON nist_controls(control_type);

-- Audit history table indexes
CREATE INDEX IF NOT EXISTS idx_audit_control_id ON audit_history(control_id);
CREATE INDEX IF NOT EXISTS idx_audit_test_date ON audit_history(test_date);
CREATE INDEX IF NOT EXISTS idx_audit_control_date ON audit_history(control_id, test_date);
CREATE INDEX IF NOT EXISTS idx_audit_status ON audit_history(status);

-- Risk scores table indexes
CREATE INDEX IF NOT EXISTS idx_risk_control_id ON risk_scores(control_id);
CREATE INDEX IF NOT EXISTS idx_risk_calculated_date ON risk_scores(calculated_date);
CREATE INDEX IF NOT EXISTS idx_risk_score ON risk_scores(risk_score DESC);

-- =============================================================================
-- TRIGGERS: Automatic timestamp updates
-- =============================================================================

CREATE TRIGGER IF NOT EXISTS update_controls_timestamp 
AFTER UPDATE ON controls
BEGIN
    UPDATE controls SET updated_at = CURRENT_TIMESTAMP WHERE control_id = NEW.control_id;
END;

-- =============================================================================
-- VIEWS: Commonly used queries
-- =============================================================================

-- View: Failed controls with high business impact
CREATE VIEW IF NOT EXISTS v_critical_failures AS
SELECT 
    c.control_id,
    c.control_name,
    c.owner,
    c.nist_family,
    c.control_weight,
    c.business_impact,
    c.last_test_date,
    c.next_test_due,
    julianday('now') - julianday(c.next_test_due) as days_overdue
FROM controls c
WHERE c.status = 'fail' 
  AND c.business_impact IN ('critical', 'high')
ORDER BY c.control_weight DESC, days_overdue DESC;

-- View: Overdue controls
CREATE VIEW IF NOT EXISTS v_overdue_controls AS
SELECT 
    c.control_id,
    c.control_name,
    c.owner,
    c.nist_family,
    c.status,
    c.next_test_due,
    julianday('now') - julianday(c.next_test_due) as days_overdue
FROM controls c
WHERE c.next_test_due < date('now')
  AND c.status != 'not_applicable'
ORDER BY days_overdue DESC;

-- View: Family-level compliance summary
CREATE VIEW IF NOT EXISTS v_family_compliance AS
SELECT 
    nist_family,
    COUNT(*) as total_controls,
    SUM(CASE WHEN status = 'pass' THEN 1 ELSE 0 END) as passed,
    SUM(CASE WHEN status = 'warn' THEN 1 ELSE 0 END) as warnings,
    SUM(CASE WHEN status = 'fail' THEN 1 ELSE 0 END) as failed,
    SUM(CASE WHEN status = 'not_tested' THEN 1 ELSE 0 END) as not_tested,
    ROUND(100.0 * SUM(CASE WHEN status = 'pass' THEN 1 ELSE 0 END) / COUNT(*), 2) as pass_rate
FROM controls
WHERE status != 'not_applicable'
GROUP BY nist_family
ORDER BY pass_rate ASC;

-- View: Owner workload summary
CREATE VIEW IF NOT EXISTS v_owner_summary AS
SELECT 
    owner,
    COUNT(*) as total_controls,
    SUM(CASE WHEN status = 'fail' THEN 1 ELSE 0 END) as failed_controls,
    SUM(CASE WHEN next_test_due < date('now') THEN 1 ELSE 0 END) as overdue_controls,
    ROUND(100.0 * SUM(CASE WHEN status = 'pass' THEN 1 ELSE 0 END) / COUNT(*), 2) as pass_rate
FROM controls
WHERE status != 'not_applicable'
GROUP BY owner
ORDER BY failed_controls DESC, overdue_controls DESC;

-- View: Latest risk scores
CREATE VIEW IF NOT EXISTS v_latest_risk_scores AS
SELECT 
    rs.control_id,
    c.control_name,
    c.nist_family,
    c.owner,
    c.status,
    rs.risk_score,
    rs.compliance_score,
    rs.calculated_date
FROM risk_scores rs
JOIN controls c ON rs.control_id = c.control_id
WHERE rs.calculated_date = (
    SELECT MAX(calculated_date) 
    FROM risk_scores 
    WHERE control_id = rs.control_id
)
ORDER BY rs.risk_score DESC;

-- =============================================================================
-- SEED DATA: NIST Control Families Metadata
-- =============================================================================

-- This will be populated by the mock data generator
-- Placeholder for reference:
/*
INSERT INTO nist_controls (nist_control_id, family, family_code, control_name, baseline, control_type) VALUES
('AC-1', 'Access Control', 'AC', 'Policy and Procedures', 'low', 'preventive'),
('AC-2', 'Access Control', 'AC', 'Account Management', 'low', 'preventive'),
...
*/

-- =============================================================================
-- DATABASE MAINTENANCE FUNCTIONS
-- =============================================================================

-- Analyze database statistics (improves query performance)
-- Run periodically: ANALYZE;

-- Rebuild indexes (defragment)
-- Run monthly: REINDEX;

-- Vacuum database (reclaim space)
-- Run quarterly: VACUUM;

-- =============================================================================
-- VALIDATION QUERIES
-- =============================================================================

-- Check for controls with invalid foreign keys
-- SELECT c.control_id, c.nist_control_id 
-- FROM controls c 
-- LEFT JOIN nist_controls nc ON c.nist_control_id = nc.nist_control_id 
-- WHERE nc.nist_control_id IS NULL AND c.nist_control_id IS NOT NULL;

-- Check for controls with invalid date logic (next_test_due < last_test_date)
-- SELECT control_id, last_test_date, next_test_due 
-- FROM controls 
-- WHERE next_test_due < last_test_date;

-- Check for duplicate control IDs
-- SELECT control_id, COUNT(*) 
-- FROM controls 
-- GROUP BY control_id 
-- HAVING COUNT(*) > 1;

-- =============================================================================
-- SCHEMA VERSION TRACKING
-- =============================================================================

CREATE TABLE IF NOT EXISTS schema_version (
    version TEXT PRIMARY KEY,
    applied_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    description TEXT
);

INSERT OR IGNORE INTO schema_version (version, description) VALUES 
('1.0', 'Initial schema - controls, audit_history, risk_scores, nist_controls tables');

-- =============================================================================
-- END OF SCHEMA
-- =============================================================================

-- Schema created successfully
-- To initialize: sqlite3 data/processed/grc.db < scripts/create_database_schema.sql
