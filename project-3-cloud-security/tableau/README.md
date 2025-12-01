# Tableau Export Directory

This directory contains CSV exports generated from the CSPM Auditor database for Tableau visualization.

## 📁 Directory Purpose

**Generated SQL-to-CSV data exports** for business intelligence and compliance reporting.

## 🔄 Data Generation

Run the export script to generate CSV files:

```bash
python scripts/enhanced_tableau_export.py
```

## 📊 Output Files

The script generates 4 CSV files:

| File | Description | Rows | Granularity |
|------|-------------|------|-------------|
| `compliance_summary_enhanced.csv` | Assessment-level metrics | ~42 | One per assessment run |
| `control_details_enhanced.csv` | Control-level results | ~504 | One per control per assessment |
| `compliance_trends_enhanced.csv` | Daily aggregated trends | ~31 | One per day |
| `findings_detail.csv` | Individual findings | Varies | One per finding |

## 🎨 Tableau Usage

1. **Connect** to `compliance_summary_enhanced.csv`
2. **Join** `control_details_enhanced.csv` on `assessment_id`
3. **Separate source** for `compliance_trends_enhanced.csv`
4. **Optional** `findings_detail.csv` for drill-down

See [TABLEAU_DATA_CONNECTIONS_VISUAL.md](TABLEAU_DATA_CONNECTIONS_VISUAL.md) for detailed connection guide.

## 🚨 Important Notes

- **Generated files are gitignored** - CSVs/JSON are created on-demand
- **Commit only the README** - Do not commit generated data files
- **Re-run export script** after new audit runs to refresh data

## 📋 File Descriptions

### compliance_summary_enhanced.csv
- **Purpose**: High-level assessment metrics over time
- **Key Fields**: `assessment_id`, `timestamp`, `score`, `rating`, `passed_controls`, `failed_controls`

### control_details_enhanced.csv  
- **Purpose**: Individual control compliance status across all assessments
- **Key Fields**: `assessment_id`, `control_id`, `category`, `status`, `compliance_status`, `severity_score`, `primary_remediation`

### compliance_trends_enhanced.csv
- **Purpose**: Daily trend analysis with movement indicators
- **Key Fields**: `date`, `avg_score`, `trend_direction`, `year_month`, `day_of_week`

### findings_detail.csv
- **Purpose**: Granular findings with remediation steps
- **Key Fields**: `control_id`, `finding_severity`, `description`, `remediation`, `resource_id`
