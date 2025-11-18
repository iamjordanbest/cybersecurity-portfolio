# 📋 GRC Analytics & Compliance Dashboard

**Project Status:** 🚧 In Development  
**Timeline:** November 3-30, 2024  
**Tech Stack:** Python, Pandas, SQLite, Streamlit, Plotly

---

## 🎯 Project Overview

A production-ready GRC (Governance, Risk, and Compliance) analytics platform that:
- Ingests compliance control data (NIST 800-53 based)
- Calculates risk scores with configurable weighting
- Performs trend analysis over time (velocity, projections)
- Generates ROI calculations for remediation efforts
- Produces executive-ready reports and operational tickets

**Key Differentiators:**
- 📊 **Trend Analysis:** Track compliance velocity and predict future state
- 💰 **ROI Calculator:** Quantify financial impact of compliance gaps
- 🎯 **Risk-Based Prioritization:** Data-driven remediation planning
- 📈 **Executive Dashboards:** Board-ready visualizations and reports

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    DATA INGESTION LAYER                      │
│  Compliance Export → Validator → Parser → Normalizer        │
│  (CSV/JSON)          (Schema)    (ETL)     (SQLite)         │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                   DATA STORAGE LAYER                         │
│  SQLite Database:                                            │
│    - controls (current state)                                │
│    - nist_controls (reference catalog)                       │
│    - audit_history (time series)                             │
│    - risk_scores (calculated metrics)                        │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                  ANALYTICS ENGINE LAYER                      │
│  - Risk Scoring Engine (multi-factor)                        │
│  - Trend Analyzer (velocity, projections)                    │
│  - ROI Calculator (cost/benefit analysis)                    │
│  - Remediation Prioritizer (what-if scenarios)               │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│              VISUALIZATION & REPORTING LAYER                 │
│  Streamlit Dashboard + PDF Reports + CSV Exports             │
└─────────────────────────────────────────────────────────────┘
```

---

## 📊 Data Model

### Controls Table
Primary table tracking current control implementation status.

| Field | Type | Description |
|-------|------|-------------|
| `control_id` | string (PK) | Unique control identifier |
| `control_name` | string | Control title |
| `control_description` | text | Detailed description |
| `status` | enum | pass, warn, fail, not_tested, not_applicable |
| `owner` | string | Responsible person/team |
| `last_test_date` | date | Most recent audit/test |
| `next_test_due` | date | Scheduled next review |
| `evidence` | text/url | Supporting documentation |
| `control_weight` | float (1-10) | Inherent control importance |
| `nist_control_id` | string (FK) | Maps to NIST 800-53 control |
| `nist_family` | string | Control family (e.g., "AC") |
| `test_frequency` | enum | monthly, quarterly, annual |
| `automated` | boolean | Is control automated? |
| `remediation_cost` | enum | low, medium, high |
| `business_impact` | enum | critical, high, medium, low |
| `created_at` | timestamp | Record creation time |
| `updated_at` | timestamp | Last modification time |

### NIST Controls Reference Table
NIST 800-53 Rev 5 control catalog.

| Field | Type | Description |
|-------|------|-------------|
| `nist_control_id` | string (PK) | NIST control ID (e.g., AC-2) |
| `family` | string | Full family name |
| `family_code` | string | Family abbreviation (AC, AU, etc.) |
| `control_name` | string | Official control name |
| `control_description` | text | NIST definition |
| `baseline` | enum | low, moderate, high |
| `control_type` | enum | preventive, detective, corrective |

### Audit History Table
Historical tracking for trend analysis.

| Field | Type | Description |
|-------|------|-------------|
| `audit_id` | string (PK) | Unique audit record ID |
| `control_id` | string (FK) | Links to controls table |
| `test_date` | date | Audit/test date |
| `status` | enum | Result at that time |
| `auditor` | string | Person who conducted test |
| `notes` | text | Audit observations |
| `evidence_url` | string | Link to evidence |

---

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- pip (Python package manager)

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/project-2-grc-compliance.git
cd project-2-grc-compliance

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Generate sample data
python scripts/generate_mock_data.py

# Run the dashboard
streamlit run src/dashboard/app.py
```

### Docker Deployment

```bash
# Build the container
docker build -t grc-compliance-dashboard .

# Run the container
docker run -p 8501:8501 grc-compliance-dashboard
```

Access the dashboard at: http://localhost:8501

---

## 📈 Key Features

### 1. Risk Scoring Engine
Multi-factor risk calculation:

```python
risk_score = (
    control_weight × 
    status_multiplier × 
    staleness_factor × 
    business_impact_weight
)
```

**Status Multipliers:**
- fail: 3.0 (highest risk)
- not_tested: 2.0 (unknown state)
- warn: 1.5 (partial implementation)
- pass: 0.1 (low residual risk)

**Staleness Factor:** `1 + (days_overdue / 365)`

### 2. Trend Analysis
- **Compliance Velocity:** Controls fixed per month
- **Trajectory Projection:** Predict future compliance state
- **Aging Analysis:** Identify stagnant controls
- **Family Trending:** Track specific control families

### 3. ROI Calculator
Quantifies financial impact:
- **Risk Exposure:** Estimated cost of control failures
- **Remediation Cost:** Effort to fix gaps
- **Net ROI:** Return on compliance investment
- **Breach Probability:** Risk-adjusted loss expectancy

### 4. Executive Reporting
- PDF executive summary for board presentations
- Operational CSV exports for ticket creation
- Real-time dashboard with drill-down capabilities
- What-if scenario modeling

---

## 📁 Project Structure

```
project-2-grc-compliance/
├── README.md                           # This file
├── requirements.txt                    # Python dependencies
├── .gitignore                          # Git ignore rules
├── Dockerfile                          # Container definition
├── config/
│   ├── scoring.yaml                    # Risk scoring configuration
│   ├── remediation_templates.yaml     # Remediation action templates
│   └── roi_parameters.yaml             # ROI calculation parameters
├── data/
│   ├── raw/                            # Original compliance exports
│   ├── processed/                      # Normalized data
│   └── nist_reference/                 # NIST 800-53 catalog
├── src/
│   ├── __init__.py
│   ├── ingestion/
│   │   ├── __init__.py
│   │   ├── validator.py                # Schema validation
│   │   ├── parser.py                   # Data parsing
│   │   └── normalizer.py               # Data normalization
│   ├── analytics/
│   │   ├── __init__.py
│   │   ├── risk_scorer.py              # Risk calculation engine
│   │   ├── trend_analyzer.py           # Trend analysis
│   │   └── roi_calculator.py           # ROI computations
│   ├── dashboard/
│   │   ├── __init__.py
│   │   └── app.py                      # Streamlit dashboard
│   ├── reports/
│   │   ├── __init__.py
│   │   ├── pdf_generator.py            # Executive reports
│   │   └── csv_exporter.py             # Operational exports
│   └── utils/
│       ├── __init__.py
│       ├── db_manager.py               # SQLite operations
│       └── config_loader.py            # Configuration management
├── tests/
│   ├── unit/                           # Unit tests
│   └── integration/                    # Integration tests
├── scripts/
│   └── generate_mock_data.py           # Mock data generator
├── docs/
│   ├── ARCHITECTURE.md                 # Technical architecture
│   ├── SCORING_METHODOLOGY.md          # Risk scoring details
│   └── DATA_MODEL.md                   # Database schema
└── outputs/
    ├── reports/                        # Generated PDF reports
    └── exports/                        # CSV exports
```

---

## 🎯 Usage Examples

### Generate Mock Data
```bash
python scripts/generate_mock_data.py --controls 200 --months 6
```

### Run Risk Analysis
```python
from src.analytics.risk_scorer import RiskScorer

scorer = RiskScorer(config_path="config/scoring.yaml")
scores = scorer.calculate_all_risks()
top_10 = scorer.get_top_risks(n=10)
```

### Export Executive Report
```bash
python -m src.reports.pdf_generator --output outputs/reports/executive_summary.pdf
```

### Calculate ROI
```python
from src.analytics.roi_calculator import ROICalculator

roi = ROICalculator()
analysis = roi.calculate_remediation_roi(control_ids=['AC-2', 'AC-3', 'AU-2'])
print(f"Net ROI: ${analysis['net_roi']:,.2f}")
```

---

## 📊 Dashboard Features

### Overview Panel
- Overall compliance score (0-100)
- Total controls by status
- High-risk control count
- Compliance trend (6-month view)

### Risk Analysis Panel
- Top 10 riskiest controls
- Risk distribution by NIST family
- Risk heat map
- Overdue controls by owner

### Trend Analysis Panel
- Compliance velocity chart
- Projected compliance trajectory
- Control aging analysis
- Family-specific trends

### ROI Calculator Panel
- Risk exposure calculation
- Remediation cost estimation
- What-if scenario modeling
- Prioritized action plan

---

## 🧪 Testing

```bash
# Run all tests
pytest tests/

# Run unit tests only
pytest tests/unit/

# Run with coverage
pytest --cov=src tests/
```

---

## 📝 NIST 800-53 Control Families Covered

**Priority Tier 1** (85% of audit focus):
- **AC** - Access Control (26 controls)
- **AU** - Audit and Accountability (16 controls)
- **IA** - Identification and Authentication (12 controls)
- **SC** - System and Communications Protection (52 controls)
- **SI** - System and Information Integrity (23 controls)

**Priority Tier 2** (High business value):
- **CM** - Configuration Management (14 controls)
- **CP** - Contingency Planning (13 controls)
- **IR** - Incident Response (10 controls)
- **RA** - Risk Assessment (10 controls)

**Total Coverage:** 10 families, ~175 controls

---

## 🎓 Key Metrics & KPIs

### Compliance Metrics
- **Overall Compliance Score:** Weighted average of all control scores
- **Pass Rate:** Percentage of controls in "pass" status
- **Critical Failures:** Count of failed high-impact controls
- **Overdue Controls:** Controls past next_test_due date

### Risk Metrics
- **Aggregate Risk Score:** Sum of all control risk scores
- **Average Risk per Family:** Risk distributed by NIST family
- **Risk Trend:** Change in risk score over time

### Performance Metrics
- **Compliance Velocity:** Controls remediated per month
- **Mean Time to Remediate (MTTR):** Average days to fix failed controls
- **Control Coverage:** Percentage of NIST controls implemented

### Business Metrics
- **Risk Exposure:** Estimated potential cost of failures
- **Remediation ROI:** Return on investment for fixing controls
- **Audit Readiness:** Percentage ready for external audit

---

## 🔮 Roadmap

### Week 1 (Nov 3-9): ✅ Data Foundation
- [x] Project structure setup
- [x] Data model design
- [ ] NIST reference catalog import
- [ ] Mock data generator
- [ ] SQLite database schema

### Week 2 (Nov 10-16): Analytics Engine
- [ ] Risk scoring implementation
- [ ] Trend analyzer
- [ ] ROI calculator
- [ ] Streamlit dashboard (v1)

### Week 3 (Nov 17-23): Reporting & Polish
- [ ] PDF report generator
- [ ] CSV export functionality
- [ ] What-if scenario modeling
- [ ] Dashboard enhancements

### Week 4 (Nov 24-30): Documentation & Demo
- [ ] Complete documentation
- [ ] Demo video recording
- [ ] Docker containerization
- [ ] GitHub publication

---

## 🤝 Contributing

This is a portfolio project, but feedback and suggestions are welcome!

---

## 📄 License

MIT License - See LICENSE file for details

---

## 👤 Author

**Jordan Best**  
Cybersecurity Portfolio Project  
[GitHub](https://github.com/yourusername) | [LinkedIn](https://linkedin.com/in/yourprofile)

---

**Last Updated:** December 2024  
**Project Status:** Week 1 - Data Foundation Phase
