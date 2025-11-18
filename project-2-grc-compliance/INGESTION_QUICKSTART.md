# GRC Analytics Platform - Ingestion Quick Start Guide

This guide will help you quickly set up and run the data ingestion pipeline for the GRC Analytics Platform.

## 🚀 Quick Start (5 Minutes)

### Step 1: Create the Database

```bash
# Navigate to project directory
cd project-2-grc-compliance

# Create database with schema
sqlite3 grc_analytics.db < scripts/create_enhanced_schema.sql
```

**Verify database creation:**
```bash
sqlite3 grc_analytics.db "SELECT name FROM sqlite_master WHERE type='table';"
```

You should see tables like: `nist_controls`, `vulnerabilities`, `mitre_attack_techniques`, etc.

### Step 2: Run the Master Ingestion Script

```bash
# Run all ingestion scripts in the correct order
python src/ingestion/run_all_ingestion.py
```

**This will:**
1. ✓ Check for data files
2. ✓ Ingest NIST 800-53 controls (~1,500 controls)
3. ✓ Ingest CISA Known Exploited Vulnerabilities (~1,400 CVEs)
4. ✓ Ingest NVD CVEs (if available)
5. ✓ Ingest MITRE ATT&CK techniques (~600 techniques)
6. ✓ Auto-map CVEs to NIST controls (thousands of mappings)

**Expected Duration:** 2-5 minutes (depending on data volume)

---

## 📊 What Gets Ingested

### 1. NIST 800-53 Controls
- **Source:** OSCAL JSON catalog
- **Records:** ~1,500 controls and enhancements
- **Families:** 20 control families (AC, AT, AU, CA, CM, CP, IA, IR, MA, MP, PE, PL, PS, PT, RA, SA, SC, SI, SR, PM)

### 2. CISA Known Exploited Vulnerabilities
- **Source:** CISA KEV Catalog JSON
- **Records:** ~1,400 actively exploited CVEs
- **Data:** CVE IDs, vendors, products, CWEs, due dates, required actions

### 3. MITRE ATT&CK Techniques
- **Source:** Enterprise ATT&CK JSON
- **Records:** ~600 techniques across 14 tactics
- **Mappings:** Auto-mapped to NIST controls

### 4. CVE-to-Control Mappings
- **Source:** Automated analysis
- **Mappings:** Based on 80+ CWE patterns, severity levels, keywords
- **Confidence Scores:** 0.7-0.8 for automated mappings

---

## 🔍 Verify Ingestion Success

After running the scripts, verify the data:

```sql
-- Open database
sqlite3 grc_analytics.db

-- Check record counts
SELECT 'NIST Controls' as table_name, COUNT(*) as count FROM nist_controls
UNION ALL
SELECT 'Vulnerabilities', COUNT(*) FROM vulnerabilities
UNION ALL
SELECT 'MITRE Techniques', COUNT(*) FROM mitre_attack_techniques
UNION ALL
SELECT 'CVE-Control Mappings', COUNT(*) FROM vulnerability_control_mapping
UNION ALL
SELECT 'ATT&CK-Control Mappings', COUNT(*) FROM attack_control_mapping;
```

**Expected Results:**
```
NIST Controls:              1,000 - 1,500
Vulnerabilities:            1,400 - 50,000+
MITRE Techniques:           500 - 700
CVE-Control Mappings:       3,000 - 100,000+
ATT&CK-Control Mappings:    1,000 - 3,000
```

---

## 📁 Data File Locations

The scripts expect data files in these locations:

```
project-2-grc-compliance/
└── data/
    └── raw/
        ├── cisa_kev/
        │   └── known_exploited_vulnerabilities.json  ✓ Available
        │
        ├── nist_nvd/
        │   └── nvd_recent_cves.json                  (Optional)
        │
        ├── nist_oscal/
        │   └── oscal-content/
        │       └── nist.gov/
        │           └── SP800-53/
        │               └── rev5/
        │                   └── json/
        │                       └── NIST_SP-800-53_rev5_catalog.json  ✓ Available
        │
        └── mitre_attack/
            └── cti/
                └── enterprise-attack/
                    └── enterprise-attack.json        ✓ Available
```

---

## 🔄 Running Individual Scripts

If you prefer to run scripts individually or need to re-run specific components:

### 1. NIST Controls (Required First)
```bash
python src/ingestion/ingest_nist_controls.py
```

### 2. CISA KEV
```bash
python src/ingestion/ingest_cisa_kev.py
```

### 3. NVD CVEs (Optional)
```bash
python src/ingestion/ingest_nvd_cves.py
```

### 4. MITRE ATT&CK
```bash
python src/ingestion/ingest_mitre_attack.py
```

### 5. Auto-Mapping
```bash
python src/ingestion/automap_cve_to_controls.py
```

---

## 📈 Sample Output

### Successful Run
```
======================================================================
GRC ANALYTICS PLATFORM - MASTER INGESTION ORCHESTRATOR
======================================================================
Start Time: 2025-01-18 10:30:00

----------------------------------------------------------------------
Database Check:
----------------------------------------------------------------------
✓ Database exists: grc_analytics.db

----------------------------------------------------------------------
Data Files Check:
----------------------------------------------------------------------
cisa_kev: ✓ Available
nvd_cves: ✗ Not found
nist_controls: ✓ Available
mitre_attack: ✓ Available

======================================================================
STARTING INGESTION SEQUENCE
======================================================================

======================================================================
Running: NIST 800-53 Controls
======================================================================
Processing 20 control families...
Successfully ingested 1,234 controls
✓ NIST 800-53 Controls completed successfully

======================================================================
Running: CISA KEV (Known Exploited Vulnerabilities)
======================================================================
Processing 1,460 vulnerabilities...
Successfully ingested 1,460 vulnerabilities
✓ CISA KEV completed successfully

======================================================================
Running: MITRE ATT&CK
======================================================================
Processing 621 MITRE ATT&CK techniques...
Successfully ingested 621 techniques
Successfully created 2,847 technique-to-control mappings
✓ MITRE ATT&CK completed successfully

======================================================================
Running: CVE to Controls Auto-Mapping
======================================================================
Processing 1,460 CVEs for auto-mapping...
Successfully processed 1,460 CVEs and created 4,892 mappings
✓ CVE to Controls Auto-Mapping completed successfully

======================================================================
INGESTION SUMMARY
======================================================================
End Time: 2025-01-18 10:33:45
Duration: 0:03:45

✓ NIST 800-53 Controls: SUCCESS
✓ CISA KEV: SUCCESS
⊘ NVD CVEs: SKIPPED (Data file not available)
✓ MITRE ATT&CK: SUCCESS
✓ CVE to Controls Auto-Mapping: SUCCESS

Total Steps: 5
Successful: 4
Failed: 0
Skipped: 1

✓ All ingestion steps completed successfully!
======================================================================
```

---

## 🎯 CVE Auto-Mapping Examples

The auto-mapping script intelligently maps CVEs to controls based on:

### CWE-Based Mapping
```
CVE-2024-1234 (CWE-79: XSS)
  ↓
Mapped to: SI-10 (Input Validation), SI-15 (Output Encoding)
```

### Severity-Based Mapping
```
CVE-2024-5678 (CRITICAL Severity)
  ↓
Mapped to: IR-4 (Incident Handling), IR-5 (Incident Monitoring),
           RA-5 (Vulnerability Scanning), SI-2 (Flaw Remediation)
```

### Keyword-Based Mapping
```
CVE-2024-9012 (Description contains "authentication bypass")
  ↓
Mapped to: IA-2 (Identification & Authentication),
           IA-5 (Authenticator Management), AC-7 (Unsuccessful Logon Attempts)
```

### Exploited CVE Mapping
```
CVE-2024-3456 (In CISA KEV - Actively Exploited)
  ↓
Additional controls: IR-4 (Incident Handling), IR-6 (Incident Reporting),
                     SI-4 (System Monitoring), SI-5 (Security Alerts)
```

---

## 🛠️ Troubleshooting

### Issue: "Database not found"
**Solution:**
```bash
sqlite3 grc_analytics.db < scripts/create_enhanced_schema.sql
```

### Issue: "Data file not found"
**Solution:** The file either doesn't exist or is in the wrong location. Check paths in the Data File Locations section above.

### Issue: "No mappings created"
**Solution:**
1. Ensure NIST controls are ingested first
2. Verify CVEs are in the database
3. Run the mapping script again

### Issue: Script hangs or takes too long
**Solution:**
- For large NVD datasets (50K+ CVEs), expect 5-10 minutes
- Check console output for progress indicators
- Consider processing in batches for very large datasets

---

## 📊 Generated Reports

### CVE Mapping Report
**Location:** `outputs/reports/cve_control_mapping_report.json`

**Contents:**
```json
{
  "statistics": {
    "total_cves_mapped": 1460,
    "total_controls_mapped": 87,
    "total_mappings": 4892
  },
  "top_mapped_controls": [
    {
      "control_id": "SI-2",
      "title": "Flaw Remediation",
      "mapping_count": 1460
    },
    {
      "control_id": "RA-5",
      "title": "Vulnerability Scanning",
      "mapping_count": 1460
    }
  ],
  "high_risk_controls": [
    {
      "control_id": "SI-10",
      "title": "Information Input Validation",
      "critical_cves": 45,
      "high_cves": 123
    }
  ]
}
```

---

## 🔄 Update Schedule

Recommended frequencies for running ingestion scripts:

| Data Source | Frequency | Command |
|-------------|-----------|---------|
| NIST Controls | Annually | `python src/ingestion/ingest_nist_controls.py` |
| CISA KEV | Weekly | `python src/ingestion/ingest_cisa_kev.py` |
| NVD CVEs | Weekly/Monthly | `python src/ingestion/ingest_nvd_cves.py` |
| MITRE ATT&CK | Quarterly | `python src/ingestion/ingest_mitre_attack.py` |
| Auto-Mapping | After CVE updates | `python src/ingestion/automap_cve_to_controls.py` |
| **All Sources** | As needed | `python src/ingestion/run_all_ingestion.py` |

---

## 🎓 Next Steps

After successful ingestion:

1. **Explore the Data:**
   ```bash
   sqlite3 grc_analytics.db
   .tables
   SELECT * FROM nist_controls LIMIT 5;
   ```

2. **Run Analytics Scripts** (coming soon):
   - Control effectiveness scoring
   - Vulnerability risk analysis
   - Compliance gap assessment

3. **Launch the Dashboard** (coming soon):
   ```bash
   streamlit run src/dashboard/app.py
   ```

4. **Generate Reports** (coming soon):
   - Executive summaries
   - Control implementation status
   - Vulnerability remediation priorities

---

## 📚 Additional Resources

- **Detailed Documentation:** `src/ingestion/README.md`
- **Database Schema:** `scripts/create_enhanced_schema.sql`
- **Project Guide:** `PROJECT_GUIDE.md`
- **Architecture:** `docs/ARCHITECTURE.md`

---

## ✅ Success Checklist

- [ ] Database created with schema
- [ ] NIST controls ingested (~1,500 records)
- [ ] CISA KEV ingested (~1,400 CVEs)
- [ ] MITRE ATT&CK ingested (~600 techniques)
- [ ] CVE-to-control mappings created (thousands)
- [ ] Mapping report generated
- [ ] Database verified with SQL queries

---

## 🤝 Support

If you encounter issues:
1. Check the troubleshooting section above
2. Review console logs for specific errors
3. Verify data file formats and locations
4. Ensure Python 3.9+ is installed
5. Check that all required packages are installed (`pip install -r requirements.txt`)

---

**Congratulations! Your GRC Analytics Platform database is now populated and ready for analysis!** 🎉
