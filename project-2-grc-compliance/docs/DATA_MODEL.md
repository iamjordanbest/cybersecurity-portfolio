# GRC Analytics Data Model

## Overview

This document describes the complete data model for the GRC Analytics platform. The system uses SQLite as the database engine with three core tables and one reference table.

---

## Entity Relationship Diagram

```
┌─────────────────────────┐
│   nist_controls         │
│   (Reference Table)     │
├─────────────────────────┤
│ PK nist_control_id      │
│    family               │
│    family_code          │
│    control_name         │
│    control_description  │
│    baseline             │
│    control_type         │
└────────────┬────────────┘
             │
             │ 1:N
             │
┌────────────▼────────────┐         ┌─────────────────────────┐
│   controls              │         │   risk_scores           │
│   (Main Table)          │         │   (Calculated Metrics)  │
├─────────────────────────┤         ├─────────────────────────┤
│ PK control_id           │         │ PK score_id             │
│ FK nist_control_id      │◄────────┤ FK control_id           │
│    control_name         │         │    risk_score           │
│    control_description  │    1:N  │    compliance_score     │
│    status               │         │    calculated_date      │
│    owner                │         │    factors              │
│    last_test_date       │         └─────────────────────────┘
│    next_test_due        │
│    evidence             │
│    control_weight       │         ┌─────────────────────────┐
│    nist_family          │         │   audit_history         │
│    test_frequency       │         │   (Time Series)         │
│    automated            │         ├─────────────────────────┤
│    remediation_cost     │         │ PK audit_id             │
│    business_impact      │◄────────┤ FK control_id           │
│    created_at           │    1:N  │    test_date            │
│    updated_at           │         │    status               │
└─────────────────────────┘         │    auditor              │
                                    │    notes                │
                                    │    evidence_url         │
                                    └─────────────────────────┘
```

---

## Table Definitions

### 1. controls (Main Control Registry)

The primary table storing current state of all compliance controls.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `control_id` | TEXT | PRIMARY KEY, NOT NULL | Unique control identifier (e.g., "CTRL-001") |
| `control_name` | TEXT | NOT NULL | Human-readable control name |
| `control_description` | TEXT | | Detailed control description |
| `status` | TEXT | NOT NULL, CHECK | Current implementation status: `pass`, `warn`, `fail`, `not_tested`, `not_applicable` |
| `owner` | TEXT | NOT NULL | Person or team responsible for control |
| `last_test_date` | DATE | | Date of most recent audit/test |
| `next_test_due` | DATE | | Scheduled next review date |
| `evidence` | TEXT | | Link or description of supporting evidence |
| `control_weight` | REAL | CHECK (1.0 to 10.0) | Inherent importance of control (1=low, 10=critical) |
| `nist_control_id` | TEXT | FOREIGN KEY | References nist_controls.nist_control_id |
| `nist_family` | TEXT | NOT NULL | NIST family code (e.g., "AC", "AU") |
| `test_frequency` | TEXT | CHECK | `monthly`, `quarterly`, `annual` |
| `automated` | INTEGER | CHECK (0 or 1) | Boolean: 1=automated, 0=manual |
| `remediation_cost` | TEXT | CHECK | `low`, `medium`, `high` |
| `business_impact` | TEXT | CHECK | `critical`, `high`, `medium`, `low` |
| `created_at` | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Record creation timestamp |
| `updated_at` | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Last modification timestamp |

**Indexes:**
- `idx_controls_status` on `status`
- `idx_controls_nist_family` on `nist_family`
- `idx_controls_owner` on `owner`
- `idx_controls_nist_control_id` on `nist_control_id`

**Example Row:**
```sql
INSERT INTO controls VALUES (
    'CTRL-001',                      -- control_id
    'Multi-Factor Authentication',   -- control_name
    'Implement MFA for all users',   -- control_description
    'pass',                          -- status
    'John Smith',                    -- owner
    '2024-10-15',                    -- last_test_date
    '2025-01-15',                    -- next_test_due
    'https://docs.example.com/mfa',  -- evidence
    9.0,                             -- control_weight
    'IA-2',                          -- nist_control_id
    'IA',                            -- nist_family
    'quarterly',                     -- test_frequency
    1,                               -- automated
    'medium',                        -- remediation_cost
    'critical',                      -- business_impact
    '2024-01-01 00:00:00',          -- created_at
    '2024-10-15 10:30:00'           -- updated_at
);
```

---

### 2. nist_controls (Reference Catalog)

Reference table containing NIST 800-53 Rev 5 control catalog.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `nist_control_id` | TEXT | PRIMARY KEY, NOT NULL | NIST control ID (e.g., "AC-2", "AU-12") |
| `family` | TEXT | NOT NULL | Full family name (e.g., "Access Control") |
| `family_code` | TEXT | NOT NULL | Two-letter family code (e.g., "AC") |
| `control_name` | TEXT | NOT NULL | Official NIST control name |
| `control_description` | TEXT | | Full NIST control description |
| `baseline` | TEXT | CHECK | NIST baseline: `low`, `moderate`, `high` |
| `control_type` | TEXT | CHECK | `preventive`, `detective`, `corrective` |

**Indexes:**
- `idx_nist_family_code` on `family_code`
- `idx_nist_baseline` on `baseline`

**Example Row:**
```sql
INSERT INTO nist_controls VALUES (
    'AC-2',                                    -- nist_control_id
    'Access Control',                          -- family
    'AC',                                      -- family_code
    'Account Management',                      -- control_name
    'The organization manages information...', -- control_description
    'low',                                     -- baseline (appears in all baselines)
    'preventive'                               -- control_type
);
```

---

### 3. audit_history (Time Series Data)

Historical audit records for trend analysis.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `audit_id` | TEXT | PRIMARY KEY, NOT NULL | Unique audit record ID (UUID format) |
| `control_id` | TEXT | FOREIGN KEY, NOT NULL | References controls.control_id |
| `test_date` | DATE | NOT NULL | Date audit was performed |
| `status` | TEXT | NOT NULL, CHECK | Status at time of audit (same enum as controls.status) |
| `auditor` | TEXT | NOT NULL | Person who conducted the audit |
| `notes` | TEXT | | Audit findings and observations |
| `evidence_url` | TEXT | | Link to audit evidence |

**Indexes:**
- `idx_audit_control_id` on `control_id`
- `idx_audit_test_date` on `test_date`
- `idx_audit_control_date` on `(control_id, test_date)` (composite)

**Example Row:**
```sql
INSERT INTO audit_history VALUES (
    '550e8400-e29b-41d4-a716-446655440000',  -- audit_id (UUID)
    'CTRL-001',                               -- control_id
    '2024-10-15',                            -- test_date
    'pass',                                   -- status
    'Jane Auditor',                          -- auditor
    'MFA verified on all systems',           -- notes
    'https://docs.example.com/audit-001'     -- evidence_url
);
```

---

### 4. risk_scores (Calculated Metrics)

Stores calculated risk scores and compliance metrics over time.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `score_id` | TEXT | PRIMARY KEY, NOT NULL | Unique score calculation ID (UUID format) |
| `control_id` | TEXT | FOREIGN KEY, NOT NULL | References controls.control_id |
| `risk_score` | REAL | NOT NULL | Calculated risk score (0-100+) |
| `compliance_score` | REAL | | Individual control compliance score (0-100) |
| `calculated_date` | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | When score was calculated |
| `factors` | TEXT | | JSON object with calculation factors |

**Indexes:**
- `idx_risk_control_id` on `control_id`
- `idx_risk_calculated_date` on `calculated_date`
- `idx_risk_score` on `risk_score` DESC

**Example Row:**
```sql
INSERT INTO risk_scores VALUES (
    '650e8400-e29b-41d4-a716-446655440001',  -- score_id
    'CTRL-001',                               -- control_id
    2.7,                                      -- risk_score
    98.5,                                     -- compliance_score
    '2024-11-03 14:30:00',                   -- calculated_date
    '{"status_multiplier": 0.1, "staleness_factor": 1.0, "impact_weight": 2.0, "control_weight": 9.0}'  -- factors
);
```

---

## Data Types and Enumerations

### Status Enum
Valid values for `controls.status` and `audit_history.status`:
- `pass` - Control is fully implemented and functioning
- `warn` - Control is partially implemented or needs attention
- `fail` - Control has failed or is not functioning
- `not_tested` - Control has not been tested yet
- `not_applicable` - Control does not apply to this system

### Test Frequency Enum
Valid values for `controls.test_frequency`:
- `monthly` - Control tested every month
- `quarterly` - Control tested every 3 months
- `annual` - Control tested once per year

### Remediation Cost Enum
Valid values for `controls.remediation_cost`:
- `low` - Less than 40 hours effort (~1 week)
- `medium` - 40-160 hours effort (1-4 weeks)
- `high` - More than 160 hours effort (1+ months)

### Business Impact Enum
Valid values for `controls.business_impact`:
- `critical` - Failure could cause severe business disruption
- `high` - Failure could cause significant business impact
- `medium` - Failure could cause moderate business impact
- `low` - Failure would have minimal business impact

### NIST Baseline Enum
Valid values for `nist_controls.baseline`:
- `low` - Low impact systems
- `moderate` - Moderate impact systems (most common)
- `high` - High impact systems (federal, critical infrastructure)

### Control Type Enum
Valid values for `nist_controls.control_type`:
- `preventive` - Prevents security incidents from occurring
- `detective` - Detects security incidents when they occur
- `corrective` - Corrects issues after incidents occur

---

## Database Schema Creation Script

```sql
-- Create nist_controls reference table
CREATE TABLE IF NOT EXISTS nist_controls (
    nist_control_id TEXT PRIMARY KEY NOT NULL,
    family TEXT NOT NULL,
    family_code TEXT NOT NULL,
    control_name TEXT NOT NULL,
    control_description TEXT,
    baseline TEXT CHECK(baseline IN ('low', 'moderate', 'high')),
    control_type TEXT CHECK(control_type IN ('preventive', 'detective', 'corrective'))
);

-- Create controls main table
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

-- Create audit_history table
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

-- Create risk_scores table
CREATE TABLE IF NOT EXISTS risk_scores (
    score_id TEXT PRIMARY KEY NOT NULL,
    control_id TEXT NOT NULL,
    risk_score REAL NOT NULL,
    compliance_score REAL,
    calculated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    factors TEXT,
    FOREIGN KEY (control_id) REFERENCES controls(control_id)
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_controls_status ON controls(status);
CREATE INDEX IF NOT EXISTS idx_controls_nist_family ON controls(nist_family);
CREATE INDEX IF NOT EXISTS idx_controls_owner ON controls(owner);
CREATE INDEX IF NOT EXISTS idx_controls_nist_control_id ON controls(nist_control_id);

CREATE INDEX IF NOT EXISTS idx_nist_family_code ON nist_controls(family_code);
CREATE INDEX IF NOT EXISTS idx_nist_baseline ON nist_controls(baseline);

CREATE INDEX IF NOT EXISTS idx_audit_control_id ON audit_history(control_id);
CREATE INDEX IF NOT EXISTS idx_audit_test_date ON audit_history(test_date);
CREATE INDEX IF NOT EXISTS idx_audit_control_date ON audit_history(control_id, test_date);

CREATE INDEX IF NOT EXISTS idx_risk_control_id ON risk_scores(control_id);
CREATE INDEX IF NOT EXISTS idx_risk_calculated_date ON risk_scores(calculated_date);
CREATE INDEX IF NOT EXISTS idx_risk_score ON risk_scores(risk_score DESC);

-- Create trigger to update updated_at timestamp
CREATE TRIGGER IF NOT EXISTS update_controls_timestamp 
AFTER UPDATE ON controls
BEGIN
    UPDATE controls SET updated_at = CURRENT_TIMESTAMP WHERE control_id = NEW.control_id;
END;
```

---

## Data Relationships

### One-to-Many Relationships

1. **nist_controls → controls** (1:N)
   - One NIST control can map to multiple implementation controls
   - Example: NIST control "AC-2" (Account Management) might map to multiple specific implementation controls like "AD Account Management", "AWS IAM Account Management", etc.

2. **controls → audit_history** (1:N)
   - One control can have multiple historical audit records
   - Enables trend analysis over time

3. **controls → risk_scores** (1:N)
   - One control can have multiple risk score calculations
   - Tracks how risk changes over time

---

## Data Volume Estimates

### Expected Data Volumes (Production)

| Table | Typical Count | Growth Rate |
|-------|---------------|-------------|
| `nist_controls` | ~1,000 | Static (updated with NIST revisions) |
| `controls` | 150-500 | Grows with new systems/services |
| `audit_history` | 10,000-50,000/year | ~200-400/week |
| `risk_scores` | Similar to audit_history | Calculated daily or on-demand |

### Storage Requirements
- Small deployment (150 controls): ~10 MB
- Medium deployment (300 controls): ~50 MB
- Large deployment (500 controls): ~200 MB

SQLite handles these volumes efficiently without performance issues.

---

## Data Integrity Rules

### Constraints

1. **Status Validation**: Only valid enum values accepted
2. **Weight Range**: control_weight must be between 1.0 and 10.0
3. **Date Logic**: next_test_due should be >= last_test_date (enforced in application)
4. **Foreign Key**: nist_control_id must exist in nist_controls table
5. **Automated Boolean**: Only 0 or 1 values

### Business Rules (Application Layer)

1. **Overdue Detection**: Control is overdue if `next_test_due < CURRENT_DATE`
2. **Staleness Calculation**: Days since last_test_date affects risk score
3. **Status Transitions**: 
   - `not_tested` → `pass`, `warn`, or `fail` (after testing)
   - `fail` → `warn` → `pass` (remediation progress)
   - Any status → `not_applicable` (if context changes)

---

## Query Patterns

### Common Queries

#### 1. Get All Failed Controls
```sql
SELECT control_id, control_name, owner, nist_family
FROM controls
WHERE status = 'fail'
ORDER BY control_weight DESC;
```

#### 2. Get Controls Overdue for Testing
```sql
SELECT control_id, control_name, owner, next_test_due,
       julianday('now') - julianday(next_test_due) as days_overdue
FROM controls
WHERE next_test_due < date('now')
  AND status != 'not_applicable'
ORDER BY days_overdue DESC;
```

#### 3. Calculate Family-Level Compliance
```sql
SELECT 
    nist_family,
    COUNT(*) as total_controls,
    SUM(CASE WHEN status = 'pass' THEN 1 ELSE 0 END) as passed,
    ROUND(100.0 * SUM(CASE WHEN status = 'pass' THEN 1 ELSE 0 END) / COUNT(*), 2) as pass_rate
FROM controls
WHERE status != 'not_applicable'
GROUP BY nist_family
ORDER BY pass_rate ASC;
```

#### 4. Get Control Trend Data
```sql
SELECT 
    c.control_id,
    c.control_name,
    ah.test_date,
    ah.status
FROM controls c
JOIN audit_history ah ON c.control_id = ah.control_id
WHERE c.control_id = 'CTRL-001'
ORDER BY ah.test_date DESC
LIMIT 10;
```

#### 5. Top 10 Highest Risk Controls
```sql
SELECT 
    c.control_id,
    c.control_name,
    c.nist_family,
    c.owner,
    rs.risk_score
FROM controls c
JOIN risk_scores rs ON c.control_id = rs.control_id
WHERE rs.calculated_date = (
    SELECT MAX(calculated_date) 
    FROM risk_scores 
    WHERE control_id = c.control_id
)
ORDER BY rs.risk_score DESC
LIMIT 10;
```

---

## Migration Strategy

### Version Control
Database schema changes are tracked using migration scripts in `scripts/migrations/`.

### Migration File Naming
Format: `YYYYMMDD_HHMMSS_description.sql`

Example: `20241103_143000_add_control_weight_index.sql`

### Running Migrations
```bash
python scripts/run_migrations.py
```

---

## Backup and Recovery

### Backup Strategy
- **Full Backup**: Daily SQLite database file backup
- **Incremental**: Export audit_history changes to CSV
- **Retention**: 30 days of daily backups, 12 months of monthly backups

### Recovery Procedure
1. Stop application
2. Replace corrupted .db file with backup
3. Replay recent audit_history CSV if needed
4. Restart application
5. Verify data integrity

---

## Performance Optimization

### Indexing Strategy
All foreign keys and frequently queried columns are indexed.

### Query Optimization Tips
1. Use `EXPLAIN QUERY PLAN` to analyze slow queries
2. Avoid `SELECT *` in production code
3. Use `WHERE status != 'not_applicable'` to exclude inactive controls
4. Leverage composite index on `(control_id, test_date)` for trend queries

### Database Maintenance
```sql
-- Analyze database statistics (run weekly)
ANALYZE;

-- Rebuild indexes (run monthly)
REINDEX;

-- Clean up old risk_scores (retain last 3 months only)
DELETE FROM risk_scores 
WHERE calculated_date < date('now', '-3 months');
```

---

**Document Version:** 1.0  
**Last Updated:** 2024-11-03  
**Maintainer:** Jordan Best
