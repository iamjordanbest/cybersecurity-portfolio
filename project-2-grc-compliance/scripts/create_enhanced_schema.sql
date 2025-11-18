-- Enhanced GRC Analytics Platform Database Schema
-- Includes real threat intelligence integration

-- ============================================================================
-- Core NIST 800-53 Controls (from OSCAL)
-- ============================================================================

CREATE TABLE IF NOT EXISTS nist_controls (
    control_id VARCHAR(20) PRIMARY KEY,
    control_family VARCHAR(50) NOT NULL,
    control_name VARCHAR(255) NOT NULL,
    control_description TEXT,
    baseline_low BOOLEAN DEFAULT FALSE,
    baseline_moderate BOOLEAN DEFAULT FALSE,
    baseline_high BOOLEAN DEFAULT FALSE,
    control_enhancements TEXT[],
    related_controls VARCHAR(20)[],
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
    known_ransomware_use BOOLEAN DEFAULT FALSE,
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
    cwe_ids VARCHAR(20)[],
    cpe_names TEXT[],
    references TEXT[],
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
    platforms VARCHAR(100)[],
    detection TEXT,
    mitigation_ids VARCHAR(20)[],
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- CVE to NIST Control Mapping
-- ============================================================================

CREATE TABLE IF NOT EXISTS cve_control_mapping (
    id SERIAL PRIMARY KEY,
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
    id SERIAL PRIMARY KEY,
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
    assessment_id SERIAL PRIMARY KEY,
    control_id VARCHAR(20) NOT NULL,
    assessment_date DATE NOT NULL,
    compliance_status VARCHAR(20) NOT NULL, -- 'compliant', 'partial', 'non_compliant', 'not_assessed'
    implementation_status VARCHAR(20), -- 'implemented', 'planned', 'alternative'
    risk_rating VARCHAR(20), -- 'critical', 'high', 'medium', 'low'
    assessor VARCHAR(255),
    evidence_provided BOOLEAN DEFAULT FALSE,
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
    id SERIAL PRIMARY KEY,
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
    action_id SERIAL PRIMARY KEY,
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
    log_id SERIAL PRIMARY KEY,
    table_name VARCHAR(100) NOT NULL,
    record_id VARCHAR(100),
    action VARCHAR(20), -- 'INSERT', 'UPDATE', 'DELETE'
    changed_by VARCHAR(255),
    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    old_values JSONB,
    new_values JSONB
);

-- ============================================================================
-- Indexes for Performance
-- ============================================================================

-- CISA KEV indexes
CREATE INDEX idx_kev_vendor ON cisa_kev(vendor_project);
CREATE INDEX idx_kev_product ON cisa_kev(product);
CREATE INDEX idx_kev_date_added ON cisa_kev(date_added);
CREATE INDEX idx_kev_due_date ON cisa_kev(due_date);
CREATE INDEX idx_kev_ransomware ON cisa_kev(known_ransomware_use);

-- NIST Controls indexes
CREATE INDEX idx_controls_family ON nist_controls(control_family);
CREATE INDEX idx_controls_baseline_low ON nist_controls(baseline_low);
CREATE INDEX idx_controls_baseline_mod ON nist_controls(baseline_moderate);
CREATE INDEX idx_controls_baseline_high ON nist_controls(baseline_high);

-- NVD indexes
CREATE INDEX idx_nvd_published ON nvd_vulnerabilities(published_date);
CREATE INDEX idx_nvd_cvss_v3 ON nvd_vulnerabilities(cvss_v3_score);
CREATE INDEX idx_nvd_severity ON nvd_vulnerabilities(cvss_v3_severity);

-- MITRE ATT&CK indexes
CREATE INDEX idx_attack_tactic ON mitre_attack_techniques(tactic);

-- Mapping indexes
CREATE INDEX idx_cve_mapping_cve ON cve_control_mapping(cve_id);
CREATE INDEX idx_cve_mapping_control ON cve_control_mapping(control_id);
CREATE INDEX idx_attack_mapping_tech ON attack_control_mapping(technique_id);
CREATE INDEX idx_attack_mapping_control ON attack_control_mapping(control_id);

-- Assessment indexes
CREATE INDEX idx_assessment_control ON compliance_assessments(control_id);
CREATE INDEX idx_assessment_date ON compliance_assessments(assessment_date);
CREATE INDEX idx_assessment_status ON compliance_assessments(compliance_status);
CREATE INDEX idx_assessment_risk ON compliance_assessments(risk_rating);

-- Risk score indexes
CREATE INDEX idx_risk_control ON control_risk_scores(control_id);
CREATE INDEX idx_risk_calculation_date ON control_risk_scores(calculation_date);
CREATE INDEX idx_risk_priority ON control_risk_scores(priority_score);

-- Remediation indexes
CREATE INDEX idx_remediation_control ON remediation_actions(control_id);
CREATE INDEX idx_remediation_cve ON remediation_actions(cve_id);
CREATE INDEX idx_remediation_status ON remediation_actions(status);
CREATE INDEX idx_remediation_priority ON remediation_actions(priority);

-- ============================================================================
-- Materialized Views for Performance
-- ============================================================================

-- Control summary with threat intelligence
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_control_threat_summary AS
SELECT 
    nc.control_id,
    nc.control_name,
    nc.control_family,
    COUNT(DISTINCT ccm.cve_id) as total_kev_cves,
    COUNT(DISTINCT CASE WHEN ck.due_date < CURRENT_DATE THEN ccm.cve_id END) as overdue_kev_cves,
    COUNT(DISTINCT CASE WHEN ck.known_ransomware_use THEN ccm.cve_id END) as ransomware_kev_cves,
    COUNT(DISTINCT acm.technique_id) as attack_techniques,
    AVG(crs.priority_score) as avg_priority_score
FROM nist_controls nc
LEFT JOIN cve_control_mapping ccm ON nc.control_id = ccm.control_id
LEFT JOIN cisa_kev ck ON ccm.cve_id = ck.cve_id
LEFT JOIN attack_control_mapping acm ON nc.control_id = acm.control_id
LEFT JOIN control_risk_scores crs ON nc.control_id = crs.control_id
GROUP BY nc.control_id, nc.control_name, nc.control_family;

CREATE INDEX idx_mv_control_threat_family ON mv_control_threat_summary(control_family);
CREATE INDEX idx_mv_control_threat_priority ON mv_control_threat_summary(avg_priority_score);

-- Top vulnerable vendors
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_vendor_risk_summary AS
SELECT 
    vendor_project,
    COUNT(*) as total_kev_cves,
    COUNT(CASE WHEN known_ransomware_use THEN 1 END) as ransomware_cves,
    COUNT(CASE WHEN due_date < CURRENT_DATE THEN 1 END) as overdue_cves,
    MIN(date_added) as first_kev_date,
    MAX(date_added) as latest_kev_date
FROM cisa_kev
GROUP BY vendor_project
ORDER BY total_kev_cves DESC;

-- ============================================================================
-- Functions for automatic timestamp updates
-- ============================================================================

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply triggers to tables with updated_at
CREATE TRIGGER update_nist_controls_updated_at BEFORE UPDATE ON nist_controls
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_cisa_kev_updated_at BEFORE UPDATE ON cisa_kev
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_nvd_vulnerabilities_updated_at BEFORE UPDATE ON nvd_vulnerabilities
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_compliance_assessments_updated_at BEFORE UPDATE ON compliance_assessments
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_remediation_actions_updated_at BEFORE UPDATE ON remediation_actions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- Initial Data Comments
-- ============================================================================

COMMENT ON TABLE nist_controls IS 'NIST 800-53 Rev 5 controls from OSCAL catalog';
COMMENT ON TABLE cisa_kev IS 'CISA Known Exploited Vulnerabilities catalog';
COMMENT ON TABLE nvd_vulnerabilities IS 'NIST National Vulnerability Database CVEs';
COMMENT ON TABLE mitre_attack_techniques IS 'MITRE ATT&CK Framework techniques';
COMMENT ON TABLE cve_control_mapping IS 'Maps CVEs to protective NIST controls';
COMMENT ON TABLE attack_control_mapping IS 'Maps ATT&CK techniques to defensive controls';
COMMENT ON TABLE control_risk_scores IS 'Risk scores enhanced with threat intelligence';

-- ============================================================================
-- Sample Query Examples
-- ============================================================================

/*
-- Find top 10 controls protecting against most KEV CVEs
SELECT control_id, control_name, total_kev_cves, overdue_kev_cves
FROM mv_control_threat_summary
ORDER BY total_kev_cves DESC
LIMIT 10;

-- Find critical overdue remediations
SELECT ra.*, nc.control_name, ck.vulnerability_name
FROM remediation_actions ra
JOIN nist_controls nc ON ra.control_id = nc.control_id
LEFT JOIN cisa_kev ck ON ra.cve_id = ck.cve_id
WHERE ra.status != 'completed' 
  AND ra.due_date < CURRENT_DATE
  AND ra.priority = 'critical'
ORDER BY ra.due_date;

-- Vendor risk profile
SELECT * FROM mv_vendor_risk_summary
WHERE total_kev_cves >= 10
ORDER BY overdue_cves DESC, ransomware_cves DESC;
*/
