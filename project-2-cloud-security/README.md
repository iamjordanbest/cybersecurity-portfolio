# Cloud Security Posture Management (CSPM) Auditor

A production-ready AWS compliance auditor implementing **32 CIS AWS Foundations Benchmark v1.4.0** controls. This project demonstrates automated cloud security assessment with live AWS API integration and an interactive Streamlit dashboard.

## 🎯 Key Features

- **32 CIS Controls**: Comprehensive coverage across IAM (10), Storage (8), Logging (5), Monitoring (5), and Networking (4)
- **Live AWS Integration**: Real boto3 API calls validating actual cloud resources
- **Interactive Dashboard**: Streamlit web app with executive overview, compliance trends, and remediation queue
- **Evidence Collection**: Structured findings with specific AWS resource IDs and remediation steps
- **SQLite Storage**: Historical assessment tracking for trend analysis

## 📁 Project Structure

```
project-2-cloud-security/
├── auditors/
│   ├── base_auditor.py         # Abstract base class for auditors
│   ├── iam_auditor.py          # 10 IAM controls (CIS 1.x)
│   ├── storage_auditor.py      # 8 Storage controls (CIS 2.x)
│   ├── logging_auditor.py      # 5 Logging controls (CIS 2.x)
│   ├── monitoring_auditor.py   # 5 Monitoring controls (CIS 3.x)
│   └── network_auditor.py      # 4 Network controls (CIS 5.x)
├── dashboard/
│   ├── app.py                  # Streamlit dashboard
│   └── metrics_generator.py    # Data extraction logic
├── models/
│   └── compliance.py           # Data models (Control, Finding, etc.)
├── scripts/
│   └── init_db.py              # Database initialization
├── data/
│   └── cspm.db                 # SQLite database (gitignored)
├── docs/
│   ├── AWS_MANUAL_REMEDIATION_GUIDE.md  # Manual fix instructions
│   └── dashboard_screenshot.png
├── cli.py                      # Main CLI entry point
├── requirements.txt            # Python dependencies
└── README.md
```

## 🚀 Getting Started

### Prerequisites

- Python 3.9+
- AWS CLI configured with credentials
- pip

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd project-2-cloud-security
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Initialize database**
   ```bash
   python scripts/init_db.py
   ```

### Usage

#### 1. Run Security Audit

Execute all 32 CIS control checks against your AWS account:

```bash
python cli.py audit
```

This will:
- Connect to your AWS account via boto3
- Execute all auditor modules
- Save results to SQLite database
- Generate `report.json` with findings

#### 2. Launch the Dashboard

Start the interactive Streamlit dashboard:

```bash
python cli.py dashboard
```

The dashboard opens at `http://localhost:8502` with:
- **Executive Dashboard**: Compliance score, pass/fail breakdown, category performance
- **Compliance Trends**: Historical tracking over time
- **Remediation Queue**: Prioritized list of failed controls with severity
- **Control Explorer**: Searchable table of all 32 CIS controls

## 📊 CIS Controls Implemented (32 Total)

### Identity & Access Management (10)
| Control | Description | Severity |
|---------|-------------|----------|
| CIS-1.1 | Root Account MFA Enabled | Critical |
| CIS-1.2 | Root Account Access Keys | Critical |
| CIS-1.3 | Credentials Unused > 90 Days | High |
| CIS-1.5 | Comprehensive Password Policy | High |
| CIS-1.6 | Hardware MFA for Root | Critical |
| CIS-1.7 | Eliminate Root User Usage | Critical |
| CIS-1.8 | IAM User MFA Enabled | High |
| CIS-1.9 | Access Key Rotation (90 Days) | High |
| CIS-1.15 | IAM Policies Attached to Groups | Medium |
| CIS-1.17 | Support Role Created | Medium |

### Storage (8)
| Control | Description | Severity |
|---------|-------------|----------|
| CIS-2.1.1 | S3 Bucket Encryption | High |
| CIS-2.1.2 | S3 Bucket Versioning | Medium |
| CIS-2.1.5 | S3 Block Public Access | Critical |
| CIS-2.3 | S3 Access Logging | Medium |
| CIS-2.6 | S3 Public Read Disabled | Critical |
| CIS-2.8 | KMS Key Rotation | High |
| CIS-2.10 | S3 Object Logging | Medium |
| CIS-2.11 | Enforce SSL in S3 Policies | High |

### Logging (5)
| Control | Description | Severity |
|---------|-------------|----------|
| CIS-2.1 | CloudTrail Enabled in All Regions | Critical |
| CIS-2.2 | CloudTrail Log File Validation | Medium |
| CIS-2.4 | CloudWatch Logs Integration | High |
| CIS-2.5 | AWS Config Enabled | High |
| CIS-2.7 | CloudTrail Logs Encrypted with KMS | High |

### Monitoring (5)
| Control | Description | Severity |
|---------|-------------|----------|
| CIS-3.1 | Metric Filter: Unauthorized API Calls | Medium |
| CIS-3.2 | Metric Filter: Console Sign-in without MFA | Medium |
| CIS-3.4 | Metric Filter: IAM Policy Changes | Medium |
| CIS-3.5 | Metric Filter: CloudTrail Config Changes | Medium |
| CIS-3.9 | Metric Filter: AWS Config Changes | Medium |

### Networking (4)
| Control | Description | Severity |
|---------|-------------|----------|
| CIS-5.1 | No Unrestricted SSH/RDP Access | Critical |
| CIS-5.2 | No Unrestricted Egress | Medium |
| CIS-5.3 | Default Security Group Closed | High |
| CIS-2.9 | VPC Flow Logs Enabled | High |

## 🔍 Key Insights

**Security Domain Coverage:**
- IAM controls protect against identity-based attacks
- Storage controls secure S3 data at rest and in transit
- Logging ensures audit trail for forensics
- Monitoring provides real-time alerting on suspicious activity
- Networking controls prevent unauthorized access

**Evidence-Based Findings:**
- Each failed control includes specific AWS resource IDs
- Remediation steps provided for every finding
- Severity scoring for risk-based prioritization

## 🏆 Recruiter's Perspective: Why This Matters

This project demonstrates cloud security expertise and production-ready engineering:

### 1. Real-World Compliance
- **Industry Standard**: CIS AWS Foundations Benchmark v1.4.0 is recognized by SOC 2, ISO 27001, and PCI-DSS
- **Actionable Results**: Not just pass/fail, but specific resources and remediation steps

### 2. Technical Depth
- **Modular Architecture**: Abstract base class pattern for extensible auditors
- **Error Handling**: Graceful handling of missing AWS services and permissions
- **Data Pipeline**: SQLite storage enabling historical trend analysis

### 3. Business Value
- **Continuous Monitoring**: Replace manual audits with automated 24/7 checks
- **Risk Reduction**: Proactive identification of security gaps before incidents
- **Cost Savings**: Eliminates consultant dependencies for routine compliance

## 📚 Additional Documentation

- [AWS Manual Remediation Guide](docs/AWS_MANUAL_REMEDIATION_GUIDE.md) - Step-by-step console instructions for each control
