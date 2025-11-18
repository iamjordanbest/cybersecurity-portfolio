# Week 1 Implementation Guide - GRC Analytics Platform

**Week:** November 3-9, 2024  
**Status:** Planning Complete → Development Phase  
**Focus:** Data Foundation & NIST Control Catalog

---

## 🎯 Week 1 Objectives

Build the data foundation that enables ROI calculation and trend analysis:

1. ✅ **Project Setup** (COMPLETE)
   - Directory structure
   - Configuration files
   - Documentation
   - Database schema

2. 🔄 **NIST Control Catalog** (IN PROGRESS)
   - Download NIST 800-53 Rev 5
   - Extract top 9 families (176 controls)
   - Create CSV reference file

3. 🔄 **Mock Data Generator** (IN PROGRESS)
   - Generate 200 realistic controls
   - Create 6 months of audit history
   - Apply realistic distributions and correlations

4. 🔄 **Database Initialization** (PENDING)
   - Create SQLite database
   - Populate with NIST reference
   - Import mock data
   - Validate data quality

---

## 📅 Daily Breakdown

### Day 1-2 (Nov 3-4): Setup & Research ✅ COMPLETE
**Time Spent:** 4 hours  
**Status:** ✅ Done

**Completed:**
- [x] Created project directory structure (20+ folders)
- [x] Wrote comprehensive README (400+ lines)
- [x] Designed database schema (4 tables, 5 views)
- [x] Created configuration files (scoring, ROI, remediation templates)
- [x] Wrote 5 technical documents (19,000+ words total)
- [x] Defined data strategy (NIST + mock data)
- [x] Designed risk scoring formula (6 factors)
- [x] Designed ROI calculation methodology

**Deliverables:**
- README.md
- ARCHITECTURE.md
- DATA_MODEL.md
- SCORING_METHODOLOGY.md
- DATA_SOURCES.md
- PROJECT_STATUS.md
- scoring.yaml
- roi_parameters.yaml
- remediation_templates.yaml
- create_database_schema.sql
- Dockerfile

---

### Day 3-4 (Nov 5-6): NIST Catalog & Data Model
**Estimated Time:** 6 hours  
**Status:** 🔄 Next Priority

#### Task 3.1: Download NIST 800-53 Rev 5 Control Catalog
**Effort:** 1 hour

**Steps:**
```bash
# Option 1: Download official NIST catalog
# URL: https://csrc.nist.gov/Projects/risk-management/sp800-53-controls/downloads
# Format: JSON (OSCAL) or XLSX

# Option 2: Use the curated list from DATA_SOURCES.md
# We've identified 176 controls across 9 families
```

**Extract Priority Controls:**

**Tier 1 Families (129 controls):**
- AC - Access Control: 26 controls
- AU - Audit and Accountability: 16 controls
- IA - Identification and Authentication: 12 controls
- SC - System and Communications Protection: 52 controls
- SI - System and Information Integrity: 23 controls

**Tier 2 Families (47 controls):**
- CM - Configuration Management: 14 controls
- CP - Contingency Planning: 13 controls
- IR - Incident Response: 10 controls
- RA - Risk Assessment: 10 controls

**Deliverable:**
- `data/nist_reference/nist_controls_catalog.csv`

**CSV Format:**
```csv
nist_control_id,family,family_code,control_name,control_description,baseline,control_type
AC-1,Access Control,AC,Policy and Procedures,"Develop and maintain access control policy",low,preventive
AC-2,Access Control,AC,Account Management,"Manage system accounts throughout lifecycle",low,preventive
...
```

#### Task 3.2: Create Mock Data Generator Script
**Effort:** 5 hours

**File:** `scripts/generate_mock_data.py`

**Requirements:**
1. Generate 200 control implementation records
2. Apply realistic distributions:
   - Status: 65% pass, 15% warn, 12% fail, 6% not_tested, 2% N/A
   - Weights: Normal distribution around 5.0-7.0
   - Business impact: 20% critical, 30% high, 35% medium, 15% low
3. Generate 6 months of audit history (~1,200 records)
4. Apply realistic patterns:
   - Correlated failures within families
   - Owner workload modeling
   - Control aging effects
   - Automation success rates
5. Export to CSV and SQLite

**Script Structure:**
```python
#!/usr/bin/env python3
"""
GRC Mock Data Generator
Generates realistic compliance control data for portfolio demonstration
"""

import pandas as pd
import numpy as np
import sqlite3
import uuid
from datetime import datetime, timedelta
from typing import List, Dict
import argparse

class MockDataGenerator:
    def __init__(self, num_controls=200, history_months=6, seed=42):
        """Initialize generator with parameters"""
        
    def generate_nist_catalog(self) -> pd.DataFrame:
        """Load or generate NIST control catalog"""
        
    def generate_controls(self) -> pd.DataFrame:
        """Generate control implementation records"""
        
    def generate_audit_history(self, controls: pd.DataFrame) -> pd.DataFrame:
        """Generate historical audit records"""
        
    def apply_realistic_distributions(self, df: pd.DataFrame) -> pd.DataFrame:
        """Apply industry-based distributions"""
        
    def apply_correlation_patterns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Apply correlated failures within families"""
        
    def export_to_sqlite(self, controls, history, nist_catalog):
        """Save to SQLite database"""
        
    def export_to_csv(self, controls, history, nist_catalog):
        """Export sample CSV files"""

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--controls", type=int, default=200)
    parser.add_argument("--months", type=int, default=6)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    
    generator = MockDataGenerator(args.controls, args.months, args.seed)
    generator.run()
```

**Deliverables:**
- `scripts/generate_mock_data.py` (working script)
- `data/raw/sample_controls.csv` (sample export)
- `data/raw/sample_audit_history.csv` (sample export)

---

### Day 5-6 (Nov 7-8): Database Initialization & Validation
**Estimated Time:** 4 hours  
**Status:** 🔄 Pending

#### Task 5.1: Initialize SQLite Database
**Effort:** 1 hour

**Steps:**
```bash
# Create database directory
mkdir -p data/processed

# Run schema creation
sqlite3 data/processed/grc.db < scripts/create_database_schema.sql

# Verify schema
sqlite3 data/processed/grc.db ".schema"

# Expected output:
# - 4 tables: nist_controls, controls, audit_history, risk_scores
# - 5 views: v_critical_failures, v_overdue_controls, etc.
# - 15+ indexes
```

**Verification Queries:**
```sql
-- Check table creation
SELECT name FROM sqlite_master WHERE type='table';

-- Check view creation
SELECT name FROM sqlite_master WHERE type='view';

-- Check indexes
SELECT name FROM sqlite_master WHERE type='index';
```

#### Task 5.2: Populate Database
**Effort:** 2 hours

**Steps:**
```bash
# Generate and load mock data
python scripts/generate_mock_data.py --controls 200 --months 6

# Verify data load
sqlite3 data/processed/grc.db "SELECT COUNT(*) FROM nist_controls;"  # Expected: 176
sqlite3 data/processed/grc.db "SELECT COUNT(*) FROM controls;"       # Expected: 200
sqlite3 data/processed/grc.db "SELECT COUNT(*) FROM audit_history;"  # Expected: ~1200
```

#### Task 5.3: Data Quality Validation
**Effort:** 1 hour

**Create Validation Script:** `scripts/validate_data.py`

**Checks:**
```python
def validate_data_quality():
    """Run comprehensive data quality checks"""
    
    checks = [
        check_required_fields(),      # No NULLs in required columns
        check_foreign_keys(),          # All FK references exist
        check_enum_values(),           # Valid status values
        check_data_ranges(),           # Weights 1-10, etc.
        check_date_logic(),            # next_test_due >= last_test_date
        check_distributions(),         # Status ~65% pass
        check_trend_patterns(),        # Logical status transitions
        check_control_weights(),       # Realistic weight distribution
    ]
    
    return all(checks)
```

**Deliverables:**
- `data/processed/grc.db` (populated database)
- `scripts/validate_data.py` (validation script)
- `outputs/data_quality_report.txt` (validation results)

---

### Day 7 (Nov 9): Documentation & Week 1 Wrap
**Estimated Time:** 2 hours  
**Status:** 🔄 Pending

#### Task 7.1: Update Documentation
**Effort:** 1 hour

**Updates Needed:**
- [x] Update PROJECT_STATUS.md with Week 1 progress
- [ ] Document data generation process
- [ ] Add data quality metrics to DATA_SOURCES.md
- [ ] Create data dictionary (field descriptions)
- [ ] Screenshot database schema

#### Task 7.2: Week 1 Demo & Testing
**Effort:** 1 hour

**Quick Tests:**
```sql
-- Test query: Failed controls
SELECT control_id, control_name, owner, nist_family 
FROM controls 
WHERE status = 'fail' 
ORDER BY control_weight DESC 
LIMIT 10;

-- Test query: Compliance by family
SELECT * FROM v_family_compliance ORDER BY pass_rate;

-- Test query: Control trends
SELECT c.control_id, c.control_name, ah.test_date, ah.status
FROM controls c
JOIN audit_history ah ON c.control_id = ah.control_id
WHERE c.control_id = 'CTRL-001'
ORDER BY ah.test_date;
```

#### Task 7.3: Git Commit & Tag
**Effort:** 15 minutes

```bash
# Stage all changes
git add project-2-grc-compliance/

# Commit with detailed message
git commit -m "feat(project-2): Complete Week 1 - Data Foundation

- Created project structure (20+ folders)
- Wrote 5 technical documents (19,000+ words)
- Designed database schema (4 tables, 5 views, 15 indexes)
- Generated NIST control catalog (176 controls)
- Created mock data generator (200 controls, 6 months history)
- Initialized SQLite database with realistic data
- Validated data quality (100% checks passed)

Next: Week 2 - Analytics engine implementation"

# Tag Week 1 milestone
git tag -a v0.1-week1 -m "Week 1 Complete: Data Foundation"

# Push to GitHub
git push origin main --tags
```

---

## 📊 Week 1 Success Metrics

### Technical Checklist
- [x] Project structure created (20+ folders)
- [x] Configuration files created (3 YAML files)
- [x] Database schema designed (4 tables, 5 views)
- [x] Documentation written (5 docs, 19,000+ words)
- [ ] NIST catalog imported (176 controls)
- [ ] Mock data generated (200 controls)
- [ ] 6 months audit history (1,200 records)
- [ ] Database populated and validated
- [ ] Data quality > 95%

### Data Quality Targets
- [ ] Status distribution: 65% pass (±5%)
- [ ] Control weight average: 5.5-6.5
- [ ] Family coverage: 9 families represented
- [ ] Trend patterns: 60% improving, 25% stable, 15% degrading/oscillating
- [ ] Overall compliance trajectory: 68% → 80% over 6 months
- [ ] Foreign key integrity: 100%
- [ ] No NULL values in required fields

### Time Tracking
- ✅ Days 1-2: 4 hours (setup, docs)
- 🔄 Days 3-4: 6 hours (NIST catalog, data generator)
- 🔄 Days 5-6: 4 hours (database, validation)
- 🔄 Day 7: 2 hours (docs, wrap-up)
- **Total Week 1:** 16 hours (within 10-20 hrs/week target)

---

## 🚀 Preparation for Week 2

### Week 2 Preview (Nov 10-16): Analytics Engine

**Major Components:**
1. **Risk Scoring Engine** (`src/analytics/risk_scorer.py`)
   - Implement 6-factor risk calculation
   - Family-level aggregation
   - Overall compliance score

2. **Trend Analyzer** (`src/analytics/trend_analyzer.py`)
   - Compliance velocity calculation
   - Future state projection
   - Control aging analysis

3. **ROI Calculator** (`src/analytics/roi_calculator.py`)
   - Breach probability modeling
   - Remediation cost calculation
   - NPV and payback period

4. **Streamlit Dashboard (v1)** (`src/dashboard/app.py`)
   - Overview panel
   - Risk analysis view
   - Basic charts

**Estimated Effort:** 15-18 hours

---

## 📚 Resources for Week 1

### NIST Resources
- **NIST SP 800-53 Rev 5 (PDF):**  
  https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-53r5.pdf

- **NIST OSCAL GitHub:**  
  https://github.com/usnistgov/oscal-content

- **NIST Control Catalog Spreadsheet:**  
  https://csrc.nist.gov/Projects/risk-management/sp800-53-controls/downloads

### Python Libraries Documentation
- **Pandas:** https://pandas.pydata.org/docs/
- **SQLite3:** https://docs.python.org/3/library/sqlite3.html
- **NumPy:** https://numpy.org/doc/
- **PyYAML:** https://pyyaml.org/wiki/PyYAMLDocumentation

### Data Generation Best Practices
- **Faker (for mock data):** https://faker.readthedocs.io/
- **NumPy random distributions:** https://numpy.org/doc/stable/reference/random/generator.html

---

## ⚠️ Common Issues & Solutions

### Issue 1: NIST Control Catalog Too Large
**Problem:** Full NIST catalog has 1000+ controls  
**Solution:** Focus on 9 families (176 controls) as documented in DATA_SOURCES.md

### Issue 2: Mock Data Seems Unrealistic
**Problem:** Random data doesn't look realistic  
**Solution:** Apply correlation patterns (e.g., AC-2 fails → AC-3 likely fails)

### Issue 3: Database Performance Slow
**Problem:** Queries taking too long  
**Solution:** Ensure indexes are created (run create_database_schema.sql)

### Issue 4: Trend Data Doesn't Make Sense
**Problem:** Status changes are illogical  
**Solution:** Use state machines for transitions (fail → warn → pass, not fail → pass)

---

## 🎯 Week 1 Definition of Done

**Criteria for completing Week 1:**

✅ **Infrastructure:**
- [x] All directories created
- [x] All config files created
- [x] Database schema defined
- [ ] Database initialized with data

✅ **Data:**
- [ ] NIST control catalog (176 controls)
- [ ] Control implementations (200 records)
- [ ] Audit history (1,200 records)
- [ ] Data quality validated (>95%)

✅ **Documentation:**
- [x] README.md complete
- [x] Technical architecture documented
- [x] Data model documented
- [x] Scoring methodology documented
- [ ] Data generation process documented

✅ **Verification:**
- [ ] All data quality checks pass
- [ ] Sample queries return expected results
- [ ] Database file size reasonable (<10 MB)
- [ ] Git commit with tag v0.1-week1

---

## 📞 Questions to Answer This Week

1. ✅ **Data Source:** Use Sprinter or mock data?  
   **Answer:** Mock data (full control, reproducible)

2. ✅ **NIST Coverage:** How many controls?  
   **Answer:** 176 controls across 9 families (95% coverage)

3. ✅ **Historical Data:** How many months?  
   **Answer:** 6 months (sufficient for trend analysis)

4. ✅ **Database:** SQLite or PostgreSQL?  
   **Answer:** SQLite (sufficient for portfolio scale)

5. 🔄 **Data Realism:** How to ensure realistic patterns?  
   **Answer:** Apply correlations, distributions, state machines

---

**Document Version:** 1.0  
**Last Updated:** 2024-11-03  
**Status:** In Progress  
**Next Update:** 2024-11-09 (End of Week 1)

---

**Ready to start? Run this command:**
```bash
cd project-2-grc-compliance
python scripts/generate_mock_data.py --controls 200 --months 6
```
