# Data Ingestion Scripts

This directory contains scripts for ingesting data from various sources into the GRC Analytics Platform database.

## Overview

The ingestion pipeline consists of the following components:

1. **NIST 800-53 Controls** - Ingests security controls from OSCAL format
2. **CISA KEV** - Ingests known exploited vulnerabilities
3. **NVD CVEs** - Ingests Common Vulnerabilities and Exposures
4. **MITRE ATT&CK** - Ingests attack techniques and tactics
5. **Auto-Mapping** - Automatically maps CVEs to NIST controls

## Scripts

### 1. `ingest_nist_controls.py`

Ingests NIST 800-53 Rev 5 security controls from OSCAL JSON format.

**Source Data:**
- `data/raw/nist_oscal/oscal-content/nist.gov/SP800-53/rev5/json/NIST_SP-800-53_rev5_catalog.json`

**Database Tables:**
- `nist_controls`

**Usage:**
```bash
python src/ingestion/ingest_nist_controls.py
```

**Features:**
- Extracts control families, titles, and descriptions
- Handles control enhancements
- Updates existing records or inserts new ones
- Processes all 20+ control families

---

### 2. `ingest_cisa_kev.py`

Ingests the CISA Known Exploited Vulnerabilities catalog.

**Source Data:**
- `data/raw/cisa_kev/known_exploited_vulnerabilities.json`

**Database Tables:**
- `vulnerabilities`

**Usage:**
```bash
python src/ingestion/ingest_cisa_kev.py
```

**Features:**
- Imports actively exploited CVEs
- Includes vendor, product, and CWE information
- Marks vulnerabilities with `is_exploited = TRUE`
- Tracks due dates and required actions

---

### 3. `ingest_nvd_cves.py`

Ingests CVE data from the National Vulnerability Database.

**Source Data:**
- `data/raw/nist_nvd/nvd_recent_cves.json`

**Database Tables:**
- `vulnerabilities`

**Usage:**
```bash
python src/ingestion/ingest_nvd_cves.py
```

**Features:**
- Extracts CVSS v2 and v3 scores
- Parses CWE (weakness) information
- Extracts vendor/product from CPE data
- Cross-references with CISA KEV for exploitation status
- Handles large datasets efficiently

---

### 4. `ingest_mitre_attack.py`

Ingests MITRE ATT&CK framework techniques and creates mappings to NIST controls.

**Source Data:**
- `data/raw/mitre_attack/cti/enterprise-attack/enterprise-attack.json`

**Database Tables:**
- `mitre_attack_techniques`
- `attack_control_mapping`

**Usage:**
```bash
python src/ingestion/ingest_mitre_attack.py
```

**Features:**
- Imports ATT&CK techniques with tactics
- Auto-maps techniques to NIST controls
- Based on tactic-to-control-family relationships
- Pattern matching for specific technique types
- Skips deprecated/revoked techniques

**Mapping Logic:**
- Tactic-based mapping (e.g., credential-access → IA controls)
- Pattern matching (e.g., "brute force" → AC-7, IA-5)
- Confidence scoring for automated mappings

---

### 5. `automap_cve_to_controls.py`

Automatically maps CVEs to NIST 800-53 controls using intelligent heuristics.

**Source Data:**
- Existing `vulnerabilities` and `nist_controls` tables

**Database Tables:**
- `vulnerability_control_mapping`

**Usage:**
```bash
python src/ingestion/automap_cve_to_controls.py
```

**Features:**
- CWE-based mapping (80+ CWE to control mappings)
- Severity-based control recommendations
- Keyword analysis from CVE descriptions
- Special handling for exploited vulnerabilities
- Generates detailed mapping report

**Mapping Rules:**

#### CWE to Control Mapping
- **CWE-78** (OS Command Injection) → SI-10, CM-7, AC-6
- **CWE-79** (XSS) → SI-10, SI-15
- **CWE-89** (SQL Injection) → SI-10, AC-6
- **CWE-287** (Improper Authentication) → IA-2, IA-5, AC-7
- **CWE-798** (Hard-coded Credentials) → IA-5, SA-4
- And many more...

#### Severity-based Controls
- **CRITICAL**: IR-4, IR-5, RA-5, SI-2
- **HIGH**: IR-4, RA-5, SI-2
- **MEDIUM**: RA-5, SI-2
- **LOW**: RA-5

#### Exploited CVEs
- Additional controls: IR-4, IR-6, SI-4, SI-5

**Output:**
- JSON report: `outputs/reports/cve_control_mapping_report.json`
- Console summary with statistics

---

### 6. `run_all_ingestion.py`

Master orchestrator script that runs all ingestion scripts in the correct order.

**Usage:**
```bash
python src/ingestion/run_all_ingestion.py
```

**Execution Order:**
1. NIST Controls (required)
2. CISA KEV
3. NVD CVEs
4. MITRE ATT&CK
5. CVE Auto-Mapping

**Features:**
- Pre-flight checks for data files
- Database existence verification
- Sequential execution with error handling
- Detailed summary report
- Skips steps if data unavailable
- Aborts on required step failure

---

## Prerequisites

### 1. Database Setup

Create the database schema first:

```bash
# Using SQLite
sqlite3 grc_analytics.db < scripts/create_enhanced_schema.sql
```

Or run the SQL script directly in your database tool.

### 2. Data Files

Ensure the following data files are downloaded:

- **NIST OSCAL Catalog** (Required)
  - Path: `data/raw/nist_oscal/oscal-content/nist.gov/SP800-53/rev5/json/`
  - Source: https://github.com/usnistgov/oscal-content

- **CISA KEV** (Optional but recommended)
  - Path: `data/raw/cisa_kev/known_exploited_vulnerabilities.json`
  - Source: https://www.cisa.gov/known-exploited-vulnerabilities-catalog

- **MITRE ATT&CK** (Optional)
  - Path: `data/raw/mitre_attack/cti/enterprise-attack/enterprise-attack.json`
  - Source: https://github.com/mitre/cti

- **NVD CVEs** (Optional)
  - Path: `data/raw/nist_nvd/nvd_recent_cves.json`
  - Source: Use NVD API or download dumps

### 3. Python Dependencies

Install required packages:

```bash
pip install -r requirements.txt
```

Key dependencies:
- `sqlite3` (built-in)
- `json` (built-in)
- `pathlib` (built-in)

---

## Usage Examples

### Quick Start - Run Everything

```bash
# Run all ingestion scripts in order
python src/ingestion/run_all_ingestion.py
```

### Individual Scripts

```bash
# Step 1: Ingest NIST controls (required first)
python src/ingestion/ingest_nist_controls.py

# Step 2: Ingest CISA KEV
python src/ingestion/ingest_cisa_kev.py

# Step 3: Ingest NVD CVEs
python src/ingestion/ingest_nvd_cves.py

# Step 4: Ingest MITRE ATT&CK
python src/ingestion/ingest_mitre_attack.py

# Step 5: Auto-map CVEs to controls
python src/ingestion/automap_cve_to_controls.py
```

### Re-run Specific Components

```bash
# Update only CVE data
python src/ingestion/ingest_nvd_cves.py

# Regenerate CVE mappings
python src/ingestion/automap_cve_to_controls.py
```

---

## Output and Logs

### Console Output
All scripts provide detailed logging to the console:
- Progress indicators
- Record counts
- Error messages
- Summary statistics

### Database Records
Check ingestion results:

```sql
-- Count records by table
SELECT COUNT(*) FROM nist_controls;
SELECT COUNT(*) FROM vulnerabilities;
SELECT COUNT(*) FROM mitre_attack_techniques;
SELECT COUNT(*) FROM vulnerability_control_mapping;
SELECT COUNT(*) FROM attack_control_mapping;
```

### Reports
The auto-mapping script generates a JSON report:
- `outputs/reports/cve_control_mapping_report.json`

---

## Troubleshooting

### Database Not Found
```
Error: Database not found: grc_analytics.db
```
**Solution:** Create the database schema first:
```bash
sqlite3 grc_analytics.db < scripts/create_enhanced_schema.sql
```

### Data File Not Found
```
Error: File not found: data/raw/nist_oscal/...
```
**Solution:** Download the required data files (see Prerequisites section)

### Duplicate Key Errors
These are normal and indicate records already exist. The scripts handle this gracefully.

### No Mappings Created
If auto-mapping creates 0 mappings:
1. Ensure NIST controls are ingested first
2. Ensure CVEs are ingested
3. Check that both tables have records

---

## Data Refresh Schedule

Recommended refresh frequencies:

- **NIST Controls**: Annually (or when new revision released)
- **CISA KEV**: Weekly (actively maintained by CISA)
- **NVD CVEs**: Daily or weekly (high volume)
- **MITRE ATT&CK**: Quarterly (updated regularly)
- **Auto-Mapping**: After each CVE update

---

## Advanced Usage

### Custom Database Path

All scripts accept database path as parameter:

```python
# In the script
conn = get_db_connection('/path/to/custom/database.db')
```

### Limiting Records

For testing, modify scripts to limit records:

```python
# In automap_cve_to_controls.py
automap_cves(conn, limit=100)  # Process only 100 CVEs
```

### Custom Mapping Rules

Edit `CWE_TO_CONTROL_MAPPING` dictionary in `automap_cve_to_controls.py`:

```python
CWE_TO_CONTROL_MAPPING = {
    'CWE-XXX': ['CUSTOM-1', 'CUSTOM-2'],
    # Add your custom mappings
}
```

---

## Performance Notes

- **NIST Controls**: ~1,500 controls, takes 10-30 seconds
- **CISA KEV**: ~1,400 CVEs, takes 5-15 seconds
- **NVD CVEs**: Varies (can be 50K+), takes 1-10 minutes
- **MITRE ATT&CK**: ~600 techniques, takes 15-30 seconds
- **Auto-Mapping**: Depends on CVE count, ~100 CVEs/second

---

## Contributing

When adding new ingestion scripts:

1. Follow the existing structure and patterns
2. Include comprehensive logging
3. Handle errors gracefully
4. Update this README with documentation
5. Add to `run_all_ingestion.py` sequence

---

## Support

For issues or questions:
1. Check the troubleshooting section
2. Review console logs for specific error messages
3. Verify data file formats match expected structure
4. Ensure database schema is up to date

---

## Version History

- **v1.0** - Initial ingestion pipeline
  - NIST Controls ingestion
  - CISA KEV ingestion
  - NVD CVE ingestion
  - MITRE ATT&CK ingestion
  - CVE auto-mapping with 80+ CWE mappings
  - Master orchestrator script
