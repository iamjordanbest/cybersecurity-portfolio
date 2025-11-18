-- Multi-Framework Support Schema Extensions
-- Phase 2: Add support for ISO 27001, CIS Controls, PCI-DSS, SOC 2
-- Compatible with existing NIST 800-53 implementation

-- ============================================================================
-- FRAMEWORKS TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS frameworks (
    framework_id INTEGER PRIMARY KEY AUTOINCREMENT,
    framework_code TEXT UNIQUE NOT NULL,
    framework_name TEXT NOT NULL,
    framework_version TEXT,
    framework_description TEXT,
    published_date DATE,
    source_url TEXT,
    is_active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert supported frameworks
INSERT OR IGNORE INTO frameworks (framework_code, framework_name, framework_version, framework_description, published_date, source_url) VALUES
('NIST-800-53', 'NIST Special Publication 800-53', 'Revision 5', 'Security and Privacy Controls for Information Systems and Organizations', '2020-09-23', 'https://csrc.nist.gov/publications/detail/sp/800-53/rev-5/final'),
('ISO-27001', 'ISO/IEC 27001', '2013', 'Information Security Management System Requirements', '2013-10-01', 'https://www.iso.org/standard/54534.html'),
('CIS', 'CIS Critical Security Controls', 'Version 8', 'CIS Controls - A prioritized set of Safeguards', '2021-05-18', 'https://www.cisecurity.org/controls'),
('PCI-DSS', 'Payment Card Industry Data Security Standard', 'Version 4.0', 'Requirements and Testing Procedures', '2022-03-31', 'https://www.pcisecuritystandards.org/'),
('SOC2', 'SOC 2 Trust Services Criteria', '2017', 'AICPA Trust Services Criteria', '2017-01-01', 'https://www.aicpa.org/');

-- ============================================================================
-- FRAMEWORK CONTROLS TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS framework_controls (
    fc_id INTEGER PRIMARY KEY AUTOINCREMENT,
    framework_id INTEGER NOT NULL,
    control_identifier TEXT NOT NULL,
    control_name TEXT NOT NULL,
    control_description TEXT,
    control_objective TEXT,
    control_category TEXT,
    control_domain TEXT,
    implementation_guidance TEXT,
    is_mandatory BOOLEAN DEFAULT 1,
    priority_level TEXT CHECK(priority_level IN ('critical', 'high', 'medium', 'low')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (framework_id) REFERENCES frameworks(framework_id) ON DELETE CASCADE,
    UNIQUE(framework_id, control_identifier)
);

-- ============================================================================
-- CONTROL MAPPINGS TABLE (Cross-Framework)
-- ============================================================================
CREATE TABLE IF NOT EXISTS control_mappings (
    mapping_id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_framework_id INTEGER NOT NULL,
    source_control_id TEXT NOT NULL,
    target_framework_id INTEGER NOT NULL,
    target_control_id TEXT NOT NULL,
    mapping_type TEXT CHECK(mapping_type IN ('EXACT', 'PARTIAL', 'RELATED', 'COMPLEMENTARY')) DEFAULT 'RELATED',
    mapping_strength REAL CHECK(mapping_strength >= 0 AND mapping_strength <= 1) DEFAULT 0.7,
    mapping_rationale TEXT,
    verified_by TEXT,
    verified_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (source_framework_id) REFERENCES frameworks(framework_id) ON DELETE CASCADE,
    FOREIGN KEY (target_framework_id) REFERENCES frameworks(framework_id) ON DELETE CASCADE,
    UNIQUE(source_framework_id, source_control_id, target_framework_id, target_control_id)
);

-- ============================================================================
-- FRAMEWORK PROFILES TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS framework_profiles (
    profile_id INTEGER PRIMARY KEY AUTOINCREMENT,
    framework_id INTEGER NOT NULL,
    profile_name TEXT NOT NULL,
    profile_code TEXT,
    profile_description TEXT,
    is_baseline BOOLEAN DEFAULT 0,
    is_active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (framework_id) REFERENCES frameworks(framework_id) ON DELETE CASCADE,
    UNIQUE(framework_id, profile_code)
);

-- ============================================================================
-- PROFILE CONTROLS TABLE (Which controls are in each profile)
-- ============================================================================
CREATE TABLE IF NOT EXISTS profile_controls (
    pc_id INTEGER PRIMARY KEY AUTOINCREMENT,
    profile_id INTEGER NOT NULL,
    control_identifier TEXT NOT NULL,
    is_required BOOLEAN DEFAULT 1,
    implementation_notes TEXT,
    FOREIGN KEY (profile_id) REFERENCES framework_profiles(profile_id) ON DELETE CASCADE
);

-- ============================================================================
-- MULTI-FRAMEWORK COMPLIANCE ASSESSMENTS
-- ============================================================================
CREATE TABLE IF NOT EXISTS mf_compliance_assessments (
    assessment_id INTEGER PRIMARY KEY AUTOINCREMENT,
    framework_id INTEGER NOT NULL,
    control_identifier TEXT NOT NULL,
    assessment_date DATE NOT NULL,
    compliance_status TEXT CHECK(compliance_status IN ('compliant', 'partially_compliant', 'non_compliant', 'not_applicable', 'not_assessed')) DEFAULT 'not_assessed',
    implementation_status TEXT CHECK(implementation_status IN ('implemented', 'partially_implemented', 'planned', 'not_planned')),
    effectiveness_rating INTEGER CHECK(effectiveness_rating >= 0 AND effectiveness_rating <= 5),
    risk_rating TEXT CHECK(risk_rating IN ('critical', 'high', 'medium', 'low')),
    assessor_name TEXT,
    assessment_notes TEXT,
    evidence_references TEXT,
    remediation_plan TEXT,
    target_completion_date DATE,
    actual_completion_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (framework_id) REFERENCES frameworks(framework_id) ON DELETE CASCADE
);

-- ============================================================================
-- MULTI-FRAMEWORK RISK SCORES
-- ============================================================================
CREATE TABLE IF NOT EXISTS mf_control_risk_scores (
    risk_score_id INTEGER PRIMARY KEY AUTOINCREMENT,
    framework_id INTEGER NOT NULL,
    control_identifier TEXT NOT NULL,
    calculation_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    base_risk_score REAL,
    threat_adjusted_score REAL,
    priority_score REAL,
    kev_cve_count INTEGER DEFAULT 0,
    attack_technique_count INTEGER DEFAULT 0,
    overdue_kev_count INTEGER DEFAULT 0,
    ransomware_related_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (framework_id) REFERENCES frameworks(framework_id) ON DELETE CASCADE
);

-- ============================================================================
-- FRAMEWORK METADATA TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS framework_metadata (
    metadata_id INTEGER PRIMARY KEY AUTOINCREMENT,
    framework_id INTEGER NOT NULL,
    metadata_key TEXT NOT NULL,
    metadata_value TEXT,
    metadata_type TEXT CHECK(metadata_type IN ('string', 'number', 'boolean', 'json', 'date')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (framework_id) REFERENCES frameworks(framework_id) ON DELETE CASCADE,
    UNIQUE(framework_id, metadata_key)
);

-- ============================================================================
-- INDEXES FOR PERFORMANCE
-- ============================================================================

-- Framework controls indexes
CREATE INDEX IF NOT EXISTS idx_framework_controls_framework 
ON framework_controls(framework_id);

CREATE INDEX IF NOT EXISTS idx_framework_controls_identifier 
ON framework_controls(control_identifier);

CREATE INDEX IF NOT EXISTS idx_framework_controls_category 
ON framework_controls(control_category);

CREATE INDEX IF NOT EXISTS idx_framework_controls_priority 
ON framework_controls(priority_level);

-- Control mappings indexes
CREATE INDEX IF NOT EXISTS idx_control_mappings_source 
ON control_mappings(source_framework_id, source_control_id);

CREATE INDEX IF NOT EXISTS idx_control_mappings_target 
ON control_mappings(target_framework_id, target_control_id);

CREATE INDEX IF NOT EXISTS idx_control_mappings_type 
ON control_mappings(mapping_type);

CREATE INDEX IF NOT EXISTS idx_control_mappings_strength 
ON control_mappings(mapping_strength);

-- Profile controls indexes
CREATE INDEX IF NOT EXISTS idx_profile_controls_profile 
ON profile_controls(profile_id);

CREATE INDEX IF NOT EXISTS idx_profile_controls_identifier 
ON profile_controls(control_identifier);

-- Multi-framework assessment indexes
CREATE INDEX IF NOT EXISTS idx_mf_assessments_framework 
ON mf_compliance_assessments(framework_id);

CREATE INDEX IF NOT EXISTS idx_mf_assessments_control 
ON mf_compliance_assessments(control_identifier);

CREATE INDEX IF NOT EXISTS idx_mf_assessments_date 
ON mf_compliance_assessments(assessment_date);

CREATE INDEX IF NOT EXISTS idx_mf_assessments_status 
ON mf_compliance_assessments(compliance_status);

CREATE INDEX IF NOT EXISTS idx_mf_assessments_risk 
ON mf_compliance_assessments(risk_rating);

-- Multi-framework risk scores indexes
CREATE INDEX IF NOT EXISTS idx_mf_risk_framework 
ON mf_control_risk_scores(framework_id);

CREATE INDEX IF NOT EXISTS idx_mf_risk_control 
ON mf_control_risk_scores(control_identifier);

CREATE INDEX IF NOT EXISTS idx_mf_risk_calculation_date 
ON mf_control_risk_scores(calculation_date);

CREATE INDEX IF NOT EXISTS idx_mf_risk_priority 
ON mf_control_risk_scores(priority_score);

-- Framework metadata indexes
CREATE INDEX IF NOT EXISTS idx_framework_metadata_framework 
ON framework_metadata(framework_id);

CREATE INDEX IF NOT EXISTS idx_framework_metadata_key 
ON framework_metadata(metadata_key);

-- ============================================================================
-- VIEWS FOR UNIFIED COMPLIANCE REPORTING
-- ============================================================================

-- Unified view of all controls across frameworks
CREATE VIEW IF NOT EXISTS v_all_framework_controls AS
SELECT 
    f.framework_code,
    f.framework_name,
    fc.control_identifier,
    fc.control_name,
    fc.control_description,
    fc.control_category,
    fc.control_domain,
    fc.priority_level,
    fc.is_mandatory
FROM framework_controls fc
JOIN frameworks f ON fc.framework_id = f.framework_id
WHERE f.is_active = 1;

-- Unified compliance status across all frameworks
CREATE VIEW IF NOT EXISTS v_unified_compliance_status AS
SELECT 
    f.framework_code,
    f.framework_name,
    mfa.control_identifier,
    fc.control_name,
    mfa.compliance_status,
    mfa.implementation_status,
    mfa.risk_rating,
    mfa.assessment_date,
    mfa.target_completion_date
FROM mf_compliance_assessments mfa
JOIN frameworks f ON mfa.framework_id = f.framework_id
JOIN framework_controls fc ON mfa.framework_id = fc.framework_id 
    AND mfa.control_identifier = fc.control_identifier
WHERE f.is_active = 1
AND mfa.assessment_id IN (
    SELECT assessment_id
    FROM mf_compliance_assessments mfa2
    WHERE mfa2.framework_id = mfa.framework_id
    AND mfa2.control_identifier = mfa.control_identifier
    ORDER BY mfa2.assessment_date DESC
    LIMIT 1
);

-- Control mapping relationships
CREATE VIEW IF NOT EXISTS v_control_mapping_relationships AS
SELECT 
    sf.framework_code as source_framework,
    cm.source_control_id,
    tf.framework_code as target_framework,
    cm.target_control_id,
    cm.mapping_type,
    cm.mapping_strength,
    cm.mapping_rationale
FROM control_mappings cm
JOIN frameworks sf ON cm.source_framework_id = sf.framework_id
JOIN frameworks tf ON cm.target_framework_id = tf.framework_id
WHERE sf.is_active = 1 AND tf.is_active = 1;

-- Framework compliance summary
CREATE VIEW IF NOT EXISTS v_framework_compliance_summary AS
SELECT 
    f.framework_code,
    f.framework_name,
    COUNT(DISTINCT fc.control_identifier) as total_controls,
    COUNT(DISTINCT CASE WHEN mfa.compliance_status = 'compliant' THEN fc.control_identifier END) as compliant_controls,
    COUNT(DISTINCT CASE WHEN mfa.compliance_status = 'partially_compliant' THEN fc.control_identifier END) as partial_controls,
    COUNT(DISTINCT CASE WHEN mfa.compliance_status = 'non_compliant' THEN fc.control_identifier END) as non_compliant_controls,
    COUNT(DISTINCT CASE WHEN mfa.compliance_status = 'not_assessed' THEN fc.control_identifier END) as not_assessed_controls,
    ROUND(
        CAST(COUNT(DISTINCT CASE WHEN mfa.compliance_status = 'compliant' THEN fc.control_identifier END) AS REAL) /
        CAST(COUNT(DISTINCT fc.control_identifier) AS REAL) * 100, 2
    ) as compliance_percentage
FROM frameworks f
JOIN framework_controls fc ON f.framework_id = fc.framework_id
LEFT JOIN mf_compliance_assessments mfa ON f.framework_id = mfa.framework_id 
    AND fc.control_identifier = mfa.control_identifier
    AND mfa.assessment_id IN (
        SELECT assessment_id
        FROM mf_compliance_assessments mfa2
        WHERE mfa2.framework_id = mfa.framework_id
        AND mfa2.control_identifier = mfa.control_identifier
        ORDER BY mfa2.assessment_date DESC
        LIMIT 1
    )
WHERE f.is_active = 1
GROUP BY f.framework_code, f.framework_name;

-- ============================================================================
-- MIGRATION SUPPORT - Link NIST controls to new structure
-- ============================================================================

-- Insert NIST controls into framework_controls (if not already there)
INSERT OR IGNORE INTO framework_controls (
    framework_id,
    control_identifier,
    control_name,
    control_description,
    control_category,
    control_domain,
    priority_level
)
SELECT 
    (SELECT framework_id FROM frameworks WHERE framework_code = 'NIST-800-53'),
    nc.control_id,
    nc.control_name,
    nc.control_description,
    nc.control_family,
    nc.control_family,
    CASE 
        WHEN nc.baseline_high = 1 THEN 'critical'
        WHEN nc.baseline_moderate = 1 THEN 'high'
        WHEN nc.baseline_low = 1 THEN 'medium'
        ELSE 'low'
    END
FROM nist_controls nc
WHERE NOT EXISTS (
    SELECT 1 FROM framework_controls fc
    WHERE fc.framework_id = (SELECT framework_id FROM frameworks WHERE framework_code = 'NIST-800-53')
    AND fc.control_identifier = nc.control_id
);

-- Migrate existing compliance assessments to multi-framework table
INSERT OR IGNORE INTO mf_compliance_assessments (
    framework_id,
    control_identifier,
    assessment_date,
    compliance_status,
    risk_rating,
    assessment_notes,
    target_completion_date
)
SELECT 
    (SELECT framework_id FROM frameworks WHERE framework_code = 'NIST-800-53'),
    ca.control_id,
    ca.assessment_date,
    ca.compliance_status,
    ca.risk_rating,
    ca.notes,
    ca.target_date
FROM compliance_assessments ca;

-- Migrate existing risk scores to multi-framework table
INSERT OR IGNORE INTO mf_control_risk_scores (
    framework_id,
    control_identifier,
    calculation_date,
    base_risk_score,
    threat_adjusted_score,
    priority_score,
    kev_cve_count,
    attack_technique_count,
    overdue_kev_count,
    ransomware_related_count
)
SELECT 
    (SELECT framework_id FROM frameworks WHERE framework_code = 'NIST-800-53'),
    crs.control_id,
    crs.calculation_date,
    crs.base_risk_score,
    crs.threat_adjusted_score,
    crs.priority_score,
    crs.kev_cve_count,
    crs.attack_technique_count,
    crs.overdue_kev_count,
    crs.ransomware_related_count
FROM control_risk_scores crs;

-- ============================================================================
-- SUMMARY STATS
-- ============================================================================
SELECT 'Schema creation complete. Summary:' as message;
SELECT 
    (SELECT COUNT(*) FROM frameworks) as total_frameworks,
    (SELECT COUNT(*) FROM framework_controls) as total_framework_controls,
    (SELECT COUNT(*) FROM control_mappings) as total_mappings,
    (SELECT COUNT(*) FROM mf_compliance_assessments) as total_assessments,
    (SELECT COUNT(*) FROM mf_control_risk_scores) as total_risk_scores;
