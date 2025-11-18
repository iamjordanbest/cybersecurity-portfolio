# GRC Analytics Platform - Quick Start Guide

## 🚀 Get Started in 5 Minutes

### Prerequisites
- Python 3.10 or higher
- Git (to clone the repository)

### Step 1: Install Dependencies

```bash
cd project-2-grc-compliance
pip install -r requirements.txt
```

### Step 2: Initialize Database (Already Done!)

The database has already been initialized and populated with:
- ✅ 1,196 NIST 800-53 Rev 5 controls
- ✅ 1,460 CISA Known Exploited Vulnerabilities
- ✅ 691 MITRE ATT&CK techniques
- ✅ 7,081 compliance assessments (6 months of data)
- ✅ 5,907 ATT&CK-to-control mappings
- ✅ 10,498 CVE-to-control mappings
- ✅ 1,196 risk scores
- ✅ 390 remediation actions

**Database location:** `data/processed/grc_analytics.db`

### Step 3: Launch the Dashboard

```bash
python run_dashboard.py
```

Or directly with Streamlit:

```bash
streamlit run src/dashboard/app.py
```

The dashboard will automatically open in your browser at `http://localhost:8501`

---

## 📊 Dashboard Features

### 1. Executive Summary
- Current compliance percentage and trend
- High-risk control count
- Remediation progress tracking
- Portfolio ROI metrics
- 6-month compliance trend visualization
- Risk distribution pie chart

### 2. Risk Analysis
- Comprehensive risk scoring with threat intelligence
- High-risk controls prioritization (Priority Score ≥ 50)
- KEV CVE and MITRE ATT&CK technique counts
- Control-level risk details

### 3. Compliance Trends
- Historical compliance tracking
- Compliance velocity calculation
- 3-month compliance projection
- Control family-level trends
- Remediation action tracking
- Time-to-95% compliance estimation

### 4. ROI Analysis
- Financial impact modeling
- Control-level ROI calculations
- Portfolio ROI analysis
- Investment recommendations
- Payback period calculations
- Top 10 controls by ROI

---

## 🧪 Test the Analytics Modules

Run the test script to verify all modules:

```bash
python scripts/test_analytics.py
```

This will test:
- ✅ Risk Scoring Engine
- ✅ Trend Analysis Module
- ✅ ROI Calculator

---

## 📈 Key Metrics (Current State)

Based on the loaded data:

- **Compliance Rate:** 67.4%
- **High-Risk Controls:** 12 critical
- **Compliance Velocity:** -0.72% per month (needs improvement)
- **Remediation Actions:** 390 total (298 in progress)
- **Top ROI Control:** RA-7 with 20,445% ROI
- **Portfolio Investment:** $2M for full remediation
- **Risk Reduction Value:** $350K annually

---

## 🔄 Regenerate Mock Data (Optional)

To regenerate mock compliance data with different parameters:

```bash
python scripts/generate_mock_compliance_data.py
```

This will create:
- 6 months of compliance assessments
- Risk scores for all controls
- Remediation actions for non-compliant controls

---

## 📂 Project Structure

```
project-2-grc-compliance/
├── data/
│   ├── processed/
│   │   └── grc_analytics.db          # Main SQLite database
│   └── raw/                           # Source data files
│       ├── cisa_kev/                  # CISA KEV catalog
│       ├── mitre_attack/              # MITRE ATT&CK data
│       └── nist_oscal/                # NIST controls
├── src/
│   ├── analytics/                     # Analytics modules
│   │   ├── risk_scoring.py           # Risk scoring engine
│   │   ├── trend_analysis.py         # Trend analyzer
│   │   └── roi_calculator.py         # ROI calculator
│   ├── dashboard/
│   │   └── app.py                    # Streamlit dashboard
│   ├── database/
│   │   ├── connection.py             # DB connection manager
│   │   └── models.py                 # Data models
│   └── ingestion/                    # Data ingestion scripts
├── scripts/
│   ├── initialize_database.py        # DB schema creation
│   ├── generate_mock_compliance_data.py
│   └── test_analytics.py            # Module tests
├── config/                            # Configuration files
│   ├── scoring.yaml                  # Risk scoring parameters
│   ├── roi_parameters.yaml           # ROI calculation settings
│   └── remediation_templates.yaml    # Remediation templates
└── docs/                              # Documentation
```

---

## 🔧 Advanced Usage

### Recalculate Risk Scores

```python
from src.analytics.risk_scoring import RiskScoringEngine

with RiskScoringEngine('data/processed/grc_analytics.db') as engine:
    results = engine.calculate_all_risk_scores(recalculate=True)
    print(f"Recalculated {results['scores_updated']} risk scores")
```

### Generate Custom Trend Report

```python
from src.analytics.trend_analysis import TrendAnalyzer

with TrendAnalyzer('data/processed/grc_analytics.db') as analyzer:
    report = analyzer.generate_trend_report()
    # Access report data
    print(f"Current compliance: {report['compliance_velocity']['current_compliance']:.2f}%")
```

### Calculate ROI for Specific Controls

```python
from src.analytics.roi_calculator import ROICalculator

with ROICalculator('data/processed/grc_analytics.db') as calculator:
    roi = calculator.calculate_control_roi('AC-2', industry='technology')
    print(f"ROI for AC-2: {roi['roi_percentage']:.2f}%")
```

---

## 📚 Additional Resources

- **Full Documentation:** See `docs/` directory
- **Architecture:** `docs/ARCHITECTURE.md`
- **Data Model:** `docs/DATA_MODEL.md`
- **Scoring Methodology:** `docs/SCORING_METHODOLOGY.md`

---

## 🆘 Troubleshooting

### Dashboard won't start
```bash
# Install missing dependencies
pip install streamlit plotly pandas pyyaml

# Verify installation
python -c "import streamlit; print(streamlit.__version__)"
```

### Database not found
```bash
# Reinitialize the database
python scripts/initialize_database.py

# Rerun ingestion
python src/ingestion/run_all_ingestion.py

# Regenerate mock data
python scripts/generate_mock_compliance_data.py
```

### Module import errors
```bash
# Make sure you're in the project root directory
cd project-2-grc-compliance

# Verify Python path
python -c "import sys; print(sys.path)"
```

---

## ✨ What's Next?

1. **Explore the Dashboard** - Navigate through all 4 views
2. **Analyze High-Risk Controls** - Focus on the 12 critical controls
3. **Review ROI Analysis** - Identify highest-value remediation investments
4. **Track Compliance Velocity** - Monitor improvement trends
5. **Export Reports** - Generate reports for stakeholders

---

**Built with:** Python, SQLite, Streamlit, Plotly, Pandas
**Data Sources:** NIST 800-53 Rev 5, CISA KEV, MITRE ATT&CK, NVD CVEs
