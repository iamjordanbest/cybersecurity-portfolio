# GRC Analytics & Compliance Dashboard

**Project Status:** 🚧 In Development | **Tech Stack:** Python, Pandas, SQLite, Streamlit, Plotly

A production-ready GRC (Governance, Risk, and Compliance) analytics platform that ingests compliance control data (NIST 800-53 based), calculates risk scores, and generates executive-ready reports.

## 🎯 Key Features

- **Risk Scoring Engine**: Multi-factor risk calculation based on control weight, status, and business impact.
- **Trend Analysis**: Tracks compliance velocity and projects future states.
- **ROI Calculator**: Quantifies the financial impact of compliance gaps using RALE methodology.
- **Executive Dashboard**: Interactive Streamlit dashboard for real-time monitoring.

## 📁 Project Structure

```
project-2-grc-compliance/
├── config/                  # Configuration for scoring and ROI
├── data/                    # Data storage (raw and processed)
├── src/
│   ├── analytics/           # Risk scoring and trend analysis logic
│   ├── dashboard/           # Streamlit application
│   ├── ingestion/           # Data ingestion scripts for various frameworks
│   └── reports/             # Reporting generators
├── scripts/                 # Utility scripts (mock data, etc.)
├── tests/                   # Automated tests
└── README.md                # Project documentation
```

## 🚀 Getting Started

### Prerequisites

- Python 3.10+
- pip

### Installation

1.  **Clone the repository**
    ```bash
    git clone <repository-url>
    cd project-2-grc-compliance
    ```

2.  **Install dependencies**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Generate Mock Data**
    ```bash
    python scripts/generate_mock_compliance_data.py
    ```

### Usage

**Run the Dashboard**
```bash
streamlit run src/dashboard/app.py
```
Access the dashboard at `http://localhost:8501`.

## 📊 Dashboard Views

1.  **Executive Summary**: High-level KPIs and compliance overview.
2.  **Risk Analysis**: Detailed risk scoring with threat intelligence integration.
3.  **Compliance Trends**: Historical trends and future projections.
4.  **ROI Analysis**: Financial impact analysis and investment prioritization.

## 🧪 Testing

Run the automated test suite:

```bash
pytest tests/
```

## 📝 License

MIT License
