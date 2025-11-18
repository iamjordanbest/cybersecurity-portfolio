-- Enhanced GRC Analytics Platform Database Schema (SQLite Compatible)
-- Includes real threat intelligence integration

-- ============================================================================
-- Core NIST 800-53 Controls (from OSCAL)
-- ============================================================================

CREATE TABLE IF NOT EXISTS nist_controls (
    control_id VARCHAR(20) PRIMARY KEY,
    control_family VARCHAR(50) NOT NULL,
    control_name VARCHAR(255) NOT NULL,
    control_description TEXT,
    baseline_low BOOLEAN DEFAULT 0,
    baseline_moderate BOOLEAN DEFAULT 0,
    baseline_high BOOLEAN DEFAULT 0,
    control_enhancements TEXT,  -- JSON array stored as text
    related_controls TEXT,  -- JSON array stored as text
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- CISA Known Exploited Vulnerabilities
-- ============================================================================

CREATE TABLE IF NOT EXISTS cisa_kev (
    cve_id VARCHAR(20) PRIMARY KEY,
    vendor_project VARCHAR(255),
    product VARCHAR(255),
    vulnerability_name VARCHAR(500),
    short_description TEXT,
    required_action TEXT,
    known_ransomware_use BOOLEAN DEFAULT 0,
    date_added DATE NOT NULL,
    due_date DATE NOT NULL,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- NIST NVD Vulnerabilities
-- ============================================================================

CREATE TABLE IF NOT EXISTS nvd_vulnerabilities (
    cve_id VARCHAR(20) PRIMARY KEY,
    published_date TIMESTAMP,
    last_modified_date TIMESTAMP,
    description TEXT,
    cvss_v3_score DECIMAL(3,1),
    cvss_v3_severity VARCHAR(20),
    cvss_v2_score DECIMAL(3,1),
    cvss_v2_severity VARCHAR(20),
    cwe_ids TEXT,  -- JSON array stored as text
    cpe_names TEXT,  -- JSON array stored as text
    reference_urls TEXT,  -- JSON array stored as text (renamed from 'references' which is a reserved word)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- MITRE ATT&CK Techniques
-- ============================================================================

CREATE TABLE IF NOT EXISTS mitre_attack_techniques (
    technique_id VARCHAR(20) PRIMARY KEY,
    technique_name VARCHAR(255) NOT NULL,
    tactic VARCHAR(100),
    description TEXT,
    platforms TEXT,  -- JSON array stored as text
    detection TEXT,
    mitigation_ids TEXT,  -- JSON array stored as text
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- CVE to NIST Control Mapping
-- ============================================================================

CREATE TABLE IF NOT EXISTS cve_control_mapping (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cve_id VARCHAR(20) NOT NULL,
    control_id VARCHAR(20) NOT NULL,
    mapping_type VARCHAR(50), -- 'primary', 'secondary', 'related'
    confidence_score DECIMAL(3,2), -- 0.0 to 1.0
    mapping_source VARCHAR(100), -- 'automated', 'manual', 'ml_model'
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (cve_id) REFERENCES cisa_kev(cve_id) ON DELETE CASCADE,
    FOREIGN KEY (control_id) REFERENCES nist_controls(control_id) ON DELETE CASCADE,
    UNIQUE(cve_id, control_id)
);

-- ============================================================================
-- MITRE ATT&CK to NIST Control Mapping
-- ============================================================================

CREATE TABLE IF NOT EXISTS attack_control_mapping (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    technique_id VARCHAR(20) NOT NULL,
    control_id VARCHAR(20) NOT NULL,
    effectiveness VARCHAR(20), -- 'high', 'medium', 'low'
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (technique_id) REFERENCES mitre_attack_techniques(technique_id) ON DELETE CASCADE,
    FOREIGN KEY (control_id) REFERENCES nist_controls(control_id) ON DELETE CASCADE,
    UNIQUE(technique_id, control_id)
);

-- ============================================================================
-- Compliance Assessment Data (Your existing tables - enhanced)
-- ============================================================================

CREATE TABLE IF NOT EXISTS compliance_assessments (
    assessment_id INTEGER PRIMARY KEY AUTOINCREMENT,
    control_id VARCHAR(20) NOT NULL,
    assessment_date DATE NOT NULL,
    compliance_status VARCHAR(20) NOT NULL, -- 'compliant', 'partial', 'non_compliant', 'not_assessed'
    implementation_status VARCHAR(20), -- 'implemented', 'planned', 'alternative'
    risk_rating VARCHAR(20), -- 'critical', 'high', 'medium', 'low'
    assessor VARCHAR(255),
    evidence_provided BOOLEAN DEFAULT 0,
    remediation_plan TEXT,
    target_date DATE,
    actual_date DATE,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (control_id) REFERENCES nist_controls(control_id) ON DELETE CASCADE
);

-- ============================================================================
-- Control Risk Scores (Enhanced with threat intelligence)
-- ============================================================================

CREATE TABLE IF NOT EXISTS control_risk_scores (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    control_id VARCHAR(20) NOT NULL,
    calculation_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    base_risk_score DECIMAL(5,2), -- Base risk without threat intel
    threat_adjusted_score DECIMAL(5,2), -- Adjusted with KEV/ATT&CK data
    kev_cve_count INTEGER DEFAULT 0, -- Number of KEV CVEs this control protects against
    attack_technique_count INTEGER DEFAULT 0, -- Number of ATT&CK techniques mitigated
    overdue_kev_count INTEGER DEFAULT 0, -- KEV CVEs past due date
    ransomware_related_count INTEGER DEFAULT 0, -- KEV CVEs with known ransomware use
    priority_score DECIMAL(5,2), -- Final prioritization score
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (control_id) REFERENCES nist_controls(control_id) ON DELETE CASCADE
);

-- ============================================================================
-- Remediation Tracking
-- ============================================================================

CREATE TABLE IF NOT EXISTS remediation_actions (
    action_id INTEGER PRIMARY KEY AUTOINCREMENT,
    control_id VARCHAR(20) NOT NULL,
    cve_id VARCHAR(20),
    action_type VARCHAR(50), -- 'patch', 'config_change', 'compensating_control', etc.
    description TEXT NOT NULL,
    priority VARCHAR(20), -- 'critical', 'high', 'medium', 'low'
    assigned_to VARCHAR(255),
    status VARCHAR(20), -- 'open', 'in_progress', 'completed', 'deferred'
    due_date DATE,
    completed_date DATE,
    estimated_cost DECIMAL(10,2),
    actual_cost DECIMAL(10,2),
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (control_id) REFERENCES nist_controls(control_id) ON DELETE CASCADE,
    FOREIGN KEY (cve_id) REFERENCES cisa_kev(cve_id) ON DELETE SET NULL
);

-- ============================================================================
-- Audit Log
-- ============================================================================

CREATE TABLE IF NOT EXISTS audit_log (
    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
    table_name VARCHAR(100) NOT NULL,
    record_id VARCHAR(100),
    action VARCHAR(20), -- 'INSERT', 'UPDATE', 'DELETE'
    changed_by VARCHAR(255),
    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    old_values TEXT,  -- JSON stored as text
    new_values TEXT   -- JSON stored as text
);

-- ============================================================================
-- Indexes for Performance
-- ============================================================================

-- CISA KEV indexes
CREATE INDEX IF NOT EXISTS idx_kev_vendor ON cisa_kev(vendor_project);
CREATE INDEX IF NOT EXISTS idx_kev_product ON cisa_kev(product);
CREATE INDEX IF NOT EXISTS idx_kev_date_added ON cisa_kev(date_added);
CREATE INDEX IF NOT EXISTS idx_kev_due_date ON cisa_kev(due_date);
CREATE INDEX IF NOT EXISTS idx_kev_ransomware ON cisa_kev(known_ransomware_use);

-- NIST Controls indexes
CREATE INDEX IF NOT EXISTS idx_controls_family ON nist_controls(control_family);
CREATE INDEX IF NOT EXISTS idx_controls_baseline_low ON nist_controls(baseline_low);
CREATE INDEX IF NOT EXISTS idx_controls_baseline_mod ON nist_controls(baseline_moderate);
CREATE INDEX IF NOT EXISTS idx_controls_baseline_high ON nist_controls(baseline_high);

-- NVD indexes
CREATE INDEX IF NOT EXISTS idx_nvd_published ON nvd_vulnerabilities(published_date);
CREATE INDEX IF NOT EXISTS idx_nvd_cvss_v3 ON nvd_vulnerabilities(cvss_v3_score);
CREATE INDEX IF NOT EXISTS idx_nvd_severity ON nvd_vulnerabilities(cvss_v3_severity);

-- MITRE ATT&CK indexes
CREATE INDEX IF NOT EXISTS idx_attack_tactic ON mitre_attack_techniques(tactic);

-- Mapping indexes
CREATE INDEX IF NOT EXISTS idx_cve_mapping_cve ON cve_control_mapping(cve_id);
CREATE INDEX IF NOT EXISTS idx_cve_mapping_control ON cve_control_mapping(control_id);
CREATE INDEX IF NOT EXISTS idx_attack_mapping_tech ON attack_control_mapping(technique_id);
CREATE INDEX IF NOT EXISTS idx_attack_mapping_control ON attack_control_mapping(control_id);

-- Assessment indexes
CREATE INDEX IF NOT EXISTS idx_assessment_control ON compliance_assessments(control_id);
CREATE INDEX IF NOT EXISTS idx_assessment_date ON compliance_assessments(assessment_date);
CREATE INDEX IF NOT EXISTS idx_assessment_status ON compliance_assessments(compliance_status);
CREATE INDEX IF NOT EXISTS idx_assessment_risk ON compliance_assessments(risk_rating);

-- Risk score indexes
CREATE INDEX IF NOT EXISTS idx_risk_control ON control_risk_scores(control_id);
CREATE INDEX IF NOT EXISTS idx_risk_calculation_date ON control_risk_scores(calculation_date);
CREATE INDEX IF NOT EXISTS idx_risk_priority ON control_risk_scores(priority_score);

-- Remediation indexes
CREATE INDEX IF NOT EXISTS idx_remediation_control ON remediation_actions(control_id);
CREATE INDEX IF NOT EXISTS idx_remediation_cve ON remediation_actions(cve_id);
CREATE INDEX IF NOT EXISTS idx_remediation_status ON remediation_actions(status);
CREATE INDEX IF NOT EXISTS idx_remediation_priority ON remediation_actions(priority);

-- ============================================================================
-- Views for Performance and Convenience
-- ============================================================================

-- Control summary with threat intelligence
CREATE VIEW IF NOT EXISTS v_control_threat_summary AS
SELECT 
    nc.control_id,
    nc.control_name,
    nc.control_family,
    COUNT(DISTINCT ccm.cve_id) as total_kev_cves,
    COUNT(DISTINCT CASE WHEN ck.due_date < date('now') THEN ccm.cve_id END) as overdue_kev_cves,
    COUNT(DISTINCT CASE WHEN ck.known_ransomware_use = 1 THEN ccm.cve_id END) as ransomware_kev_cves,
    COUNT(DISTINCT acm.technique_id) as attack_techniques,
    AVG(crs.priority_score) as avg_priority_score
FROM nist_controls nc
LEFT JOIN cve_control_mapping ccm ON nc.control_id = ccm.control_id
LEFT JOIN cisa_kev ck ON ccm.cve_id = ck.cve_id
LEFT JOIN attack_control_mapping acm ON nc.control_id = acm.control_id
LEFT JOIN control_risk_scores crs ON nc.control_id = crs.control_id
GROUP BY nc.control_id, nc.control_name, nc.control_family;

-- Top vulnerable vendors
CREATE VIEW IF NOT EXISTS v_vendor_risk_summary AS
SELECT 
    vendor_project,
    COUNT(*) as total_kev_cves,
    SUM(CASE WHEN known_ransomware_use = 1 THEN 1 ELSE 0 END) as ransomware_cves,
    SUM(CASE WHEN due_date < date('now') THEN 1 ELSE 0 END) as overdue_cves,
    MIN(date_added) as first_kev_date,
    MAX(date_added) as latest_kev_date
FROM cisa_kev
GROUP BY vendor_project
ORDER BY total_kev_cves DESC;

-- Compliance status summary
CREATE VIEW IF NOT EXISTS v_compliance_summary AS
SELECT 
    nc.control_family,
    COUNT(DISTINCT nc.control_id) as total_controls,
    COUNT(DISTINCT ca.control_id) as assessed_controls,
    SUM(CASE WHEN ca.compliance_status = 'compliant' THEN 1 ELSE 0 END) as compliant_count,
    SUM(CASE WHEN ca.compliance_status = 'partial' THEN 1 ELSE 0 END) as partial_count,
    SUM(CASE WHEN ca.compliance_status = 'non_compliant' THEN 1 ELSE 0 END) as non_compliant_count,
    ROUND(100.0 * SUM(CASE WHEN ca.compliance_status = 'compliant' THEN 1 ELSE 0 END) / 
          NULLIF(COUNT(DISTINCT ca.control_id), 0), 2) as compliance_percentage
FROM nist_controls nc
LEFT JOIN compliance_assessments ca ON nc.control_id = ca.control_id
GROUP BY nc.control_family;

-- Critical remediations view
CREATE VIEW IF NOT EXISTS v_critical_remediations AS
SELECT 
    ra.action_id,
    ra.control_id,
    nc.control_name,
    nc.control_family,
    ra.cve_id,
    ck.vulnerability_name,
    ck.known_ransomware_use,
    ra.description,
    ra.priority,
    ra.status,
    ra.due_date,
    ra.assigned_to,
    julianday('now') - julianday(ra.due_date) as days_overdue
FROM remediation_actions ra
JOIN nist_controls nc ON ra.control_id = nc.control_id
LEFT JOIN cisa_kev ck ON ra.cve_id = ck.cve_id
WHERE ra.status != 'completed' 
  AND (ra.priority = 'critical' OR ra.priority = 'high')
ORDER BY ra.priority DESC, ra.due_date ASC;

-- ============================================================================
-- Triggers for automatic timestamp updates
-- ============================================================================

CREATE TRIGGER IF NOT EXISTS trg_nist_controls_updated_at
AFTER UPDATE ON nist_controls
FOR EACH ROW
BEGIN
    UPDATE nist_controls SET updated_at = CURRENT_TIMESTAMP WHERE control_id = NEW.control_id;
END;

CREATE TRIGGER IF NOT EXISTS trg_cisa_kev_updated_at
AFTER UPDATE ON cisa_kev
FOR EACH ROW
BEGIN
    UPDATE cisa_kev SET updated_at = CURRENT_TIMESTAMP WHERE cve_id = NEW.cve_id;
END;

CREATE TRIGGER IF NOT EXISTS trg_nvd_vulnerabilities_updated_at
AFTER UPDATE ON nvd_vulnerabilities
FOR EACH ROW
BEGIN
    UPDATE nvd_vulnerabilities SET updated_at = CURRENT_TIMESTAMP WHERE cve_id = NEW.cve_id;
END;

CREATE TRIGGER IF NOT EXISTS trg_compliance_assessments_updated_at
AFTER UPDATE ON compliance_assessments
FOR EACH ROW
BEGIN
    UPDATE compliance_assessments SET updated_at = CURRENT_TIMESTAMP WHERE assessment_id = NEW.assessment_id;
END;

CREATE TRIGGER IF NOT EXISTS trg_remediation_actions_updated_at
AFTER UPDATE ON remediation_actions
FOR EACH ROW
BEGIN
    UPDATE remediation_actions SET updated_at = CURRENT_TIMESTAMP WHERE action_id = NEW.action_id;
END;

-- ============================================================================
-- Sample Query Examples (Commented)
-- ============================================================================

/*
-- Find top 10 controls protecting against most KEV CVEs
SELECT control_id, control_name, total_kev_cves, overdue_kev_cves
FROM v_control_threat_summary
ORDER BY total_kev_cves DESC
LIMIT 10;

-- Find critical overdue remediations
SELECT * FROM v_critical_remediations
WHERE days_overdue > 0
ORDER BY days_overdue DESC, priority DESC;

-- Vendor risk profile
SELECT * FROM v_vendor_risk_summary
WHERE total_kev_cves >= 10
ORDER BY overdue_cves DESC, ransomware_cves DESC;

-- Compliance by family
SELECT * FROM v_compliance_summary
ORDER BY compliance_percentage ASC;
*/
