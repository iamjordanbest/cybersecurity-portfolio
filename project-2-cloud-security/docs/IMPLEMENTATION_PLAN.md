# Project 3: Cloud Security Posture Management (CSPM) Auditor

## 📋 Executive Summary

**Project Name:** AWS CIS Compliance Auditor  
**Tagline:** *"Automate CIS AWS Foundations Benchmark compliance using real cloud infrastructure"*  
**Type:** GRC + Cloud Security Portfolio Project  
**Cost:** $0 (AWS Free Tier + open-source tools)  
**Duration:** 4 weeks (20-30 hours total)  
**Authenticity:** 100% real infrastructure, evidence, and assessments

---

## 🎯 Why This Project Wins

### Problem with Current Project
- 99,288 synthetic assessments = obvious fake data
- Cannot demonstrate live during interview
- No real evidence artifacts

### Solution: CSPM on Real AWS Account
- **Real infrastructure** - Your actual AWS free tier account
- **Real assessments** - CIS AWS Foundations Benchmark controls
- **Real evidence** - Screenshots, API outputs, Terraform state
- **Live demo ready** - Can show interviewer in 5 minutes

### Employer Value Proposition
✅ **Cloud security skills** (AWS is 32% of cloud market)  
✅ **Compliance automation** (CIS Benchmark is industry standard)  
✅ **Infrastructure as Code** (Terraform = #1 IaC tool)  
✅ **Python automation** (boto3 = official AWS SDK)  
✅ **GRC methodology** (assess → score → remediate → validate)

---

## 🏗️ **COMPLETE ARCHITECTURE** (All Layers)

```
┌─────────────────────────────────────────────────────────────────┐
│                     LAYER 1: CLOUD INFRASTRUCTURE               │
│                          (AWS Free Tier)                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │   IAM        │  │  CloudTrail  │  │   S3 Bucket  │         │
│  │              │  │              │  │              │         │
│  │ • Root MFA   │  │ • Enabled    │  │ • Versioning │         │
│  │ • Password   │  │ • Encrypted  │  │ • Encryption │         │
│  │   Policy     │  │ • Multi-     │  │ • Access     │         │
│  │ • Access     │  │   Region     │  │   Logging    │         │
│  │   Keys       │  │              │  │              │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
│                                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │   VPC        │  │     KMS      │  │   Config     │         │
│  │              │  │              │  │              │         │
│  │ • Flow Logs  │  │ • Key        │  │ • Rules      │         │
│  │ • Security   │  │   Rotation   │  │ • Recording  │         │
│  │   Groups     │  │ • Encryption │  │ • Snapshots  │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│              LAYER 2: INFRASTRUCTURE AS CODE                    │
│                      (Terraform)                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  terraform/                                                     │
│  ├── main.tf              # Provider config, backend           │
│  ├── iam.tf               # IAM password policy, MFA           │
│  ├── cloudtrail.tf        # Trail config, S3 bucket            │
│  ├── s3.tf                # Compliance bucket with controls    │
│  ├── vpc.tf               # VPC with flow logs                 │
│  ├── kms.tf               # Encryption keys                    │
│  ├── config.tf            # AWS Config rules                   │
│  ├── variables.tf         # Input variables                    │
│  └── outputs.tf           # ARNs, IDs for auditors             │
│                                                                 │
│  State Management:                                              │
│  • Local: terraform.tfstate (for portfolio)                    │
│  • Production: S3 + DynamoDB (documented as upgrade path)      │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│               LAYER 3: COMPLIANCE AUDITORS                      │
│                    (Python + boto3)                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  auditors/                                                      │
│  ├── base_auditor.py      # Abstract base class                │
│  │   • AWS session management                                  │
│  │   • Evidence collection framework                           │
│  │   • Scoring logic (pass/fail/exception)                     │
│  │                                                              │
│  ├── iam_auditor.py       # IAM compliance checks              │
│  │   • CIS 1.4: Root MFA enabled                               │
│  │   • CIS 1.12: Password policy (14+ chars)                   │
│  │   • CIS 1.16: IAM policies attached to groups               │
│  │   • CIS 1.20: Access key rotation < 90 days                 │
│  │                                                              │
│  ├── logging_auditor.py   # CloudTrail & logging               │
│  │   • CIS 2.1: CloudTrail enabled all regions                 │
│  │   • CIS 2.2: Log file validation enabled                    │
│  │   • CIS 2.3: S3 bucket logging for CloudTrail               │
│  │   • CIS 2.7: CloudTrail logs encrypted                      │
│  │                                                              │
│  ├── storage_auditor.py   # S3 compliance                      │
│  │   • CIS 2.1.1: S3 bucket encryption                         │
│  │   • CIS 2.1.2: S3 versioning enabled                        │
│  │   • CIS 2.1.3: S3 MFA delete enabled                        │
│  │   • CIS 2.1.4: S3 public access blocked                     │
│  │                                                              │
│  ├── network_auditor.py   # VPC security                       │
│  │   • CIS 4.1: VPC flow logs enabled                          │
│  │   • CIS 4.2: Default security group restricts traffic       │
│  │   • CIS 4.3: No overly permissive rules (0.0.0.0/0)         │
│  │                                                              │
│  └── monitoring_auditor.py # AWS Config                        │
│      • CIS 2.5: AWS Config enabled all regions                 │
│      • CIS 3.x: CloudWatch alarms configured                   │
│                                                                 │
│  models/                                                        │
│  ├── control.py           # Control dataclass                  │
│  ├── finding.py           # Finding/violation model            │
│  └── evidence.py          # Evidence artifact model            │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                LAYER 4: DATA PERSISTENCE                        │
│                   (SQLite Database)                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  data/compliance.db                                             │
│                                                                 │
│  Tables:                                                        │
│  ┌─────────────────────────────────────────────┐               │
│  │ controls                                    │               │
│  │─────────────────────────────────────────────│               │
│  │ control_id (PK)     | VARCHAR | CIS-1.4    │               │
│  │ framework           | VARCHAR | CIS AWS    │               │
│  │ title               | TEXT    | Root MFA   │               │
│  │ description         | TEXT    | ...        │               │
│  │ severity            | VARCHAR | Critical   │               │
│  │ category            | VARCHAR | Identity   │               │
│  └─────────────────────────────────────────────┘               │
│                                                                 │
│  ┌─────────────────────────────────────────────┐               │
│  │ assessments                                 │               │
│  │─────────────────────────────────────────────│               │
│  │ id (PK)             | INTEGER | 1          │               │
│  │ control_id (FK)     | VARCHAR | CIS-1.4    │               │
│  │ assessment_date     | DATE    | 2025-11-30 │               │
│  │ status              | VARCHAR | PASS       │               │
│  │ score               | FLOAT   | 100.0      │               │
│  │ evidence_path       | TEXT    | evidence/  │               │
│  │ notes               | TEXT    | MFA active │               │
│  │ assessor            | VARCHAR | [YourName] │               │
│  └─────────────────────────────────────────────┘               │
│                                                                 │
│  ┌─────────────────────────────────────────────┐               │
│  │ findings                                    │               │
│  │─────────────────────────────────────────────│               │
│  │ id (PK)             | INTEGER | 1          │               │
│  │ control_id (FK)     | VARCHAR | CIS-1.20   │               │
│  │ finding_date        | DATE    | 2025-11-30 │               │
│  │ severity            | VARCHAR | High       │               │
│  │ description         | TEXT    | Key > 90d  │               │
│  │ remediation         | TEXT    | Rotate key │               │
│  │ status              | VARCHAR | Open       │               │
│  │ due_date            | DATE    | 2025-12-14 │               │
│  └─────────────────────────────────────────────┘               │
│                                                                 │
│  ┌─────────────────────────────────────────────┐               │
│  │ evidence_artifacts                          │               │
│  │─────────────────────────────────────────────│               │
│  │ id (PK)             | INTEGER | 1          │               │
│  │ assessment_id (FK)  | INTEGER | 1          │               │
│  │ artifact_type       | VARCHAR | screenshot │               │
│  │ file_path           | TEXT    | ./evidence │               │
│  │ file_size           | INTEGER | 45623      │               │
│  │ hash_sha256         | TEXT    | abc123...  │               │
│  │ collected_date      | DATE    | 2025-11-30 │               │
│  └─────────────────────────────────────────────┘               │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│              LAYER 5: VISUALIZATION & REPORTING                 │
│                      (Tableau Public)                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Dashboard 1: Compliance Scorecard                              │
│  ┌─────────────────────────────────────────────┐               │
│  │  CIS AWS FOUNDATIONS BENCHMARK v1.5         │               │
│  │  Overall Compliance: 85% (17/20 controls)   │               │
│  │                                             │               │
│  │  ✅ PASS: 17    ❌ FAIL: 3    ⚠️ EXEMPT: 0  │               │
│  │                                             │               │
│  │  By Category:                               │               │
│  │  • Identity & Access: 80% (4/5)             │               │
│  │  • Logging & Monitoring: 100% (5/5)         │               │
│  │  • Storage: 75% (3/4)                       │               │
│  │  • Networking: 83% (5/6)                    │               │
│  │                                             │               │
│  │  Recent Changes:                            │               │
│  │  📈 +15% compliance (last 2 weeks)          │               │
│  └─────────────────────────────────────────────┘               │
│                                                                 │
│  Dashboard 2: Control Details (Drill-Down)                      │
│  ┌─────────────────────────────────────────────┐               │
│  │  Control: CIS-1.4 Root Account MFA          │               │
│  │  Status: ✅ PASS                             │               │
│  │  Last Assessed: 2025-11-30 15:42 UTC        │               │
│  │  Evidence: [View Screenshot] [API Output]   │               │
│  │                                             │               │
│  │  Compliance History:                        │               │
│  │  [Line chart showing pass/fail over time]   │               │
│  │                                             │               │
│  │  Business Impact:                           │               │
│  │  "Prevents unauthorized root access,        │               │
│  │   mitigates account takeover risk"          │               │
│  └─────────────────────────────────────────────┘               │
│                                                                 │
│  Dashboard 3: Findings & Remediation Queue                      │
│  ┌─────────────────────────────────────────────┐               │
│  │  Open Findings: 3                           │               │
│  │                                             │               │
│  │  High Priority (2):                         │               │
│  │  • CIS-1.20: Access key > 90 days           │               │
│  │    Remediation: Run `key_rotation.sh`       │               │
│  │    Due: 2025-12-14                          │               │
│  │                                             │               │
│  │  • CIS-2.1.3: S3 MFA delete disabled        │               │
│  │    Remediation: Apply terraform patch       │               │
│  │    Due: 2025-12-21                          │               │
│  │                                             │               │
│  │  Medium Priority (1):                       │               │
│  │  • CIS-4.3: Overly permissive SG rule       │               │
│  │    Remediation: Restrict to VPN IP          │               │
│  │    Due: 2026-01-15                          │               │
│  └─────────────────────────────────────────────┘               │
│                                                                 │
│  Dashboard 4: Infrastructure Map                                │
│  ┌─────────────────────────────────────────────┐               │
│  │  Terraform-Managed Resources: 12            │               │
│  │                                             │               │
│  │  [Visual network diagram]                   │               │
│  │  • VPC (compliant)                          │               │
│  │    └─ Subnet (compliant)                    │               │
│  │       └─ Security Group (1 finding)         │               │
│  │                                             │               │
│  │  • S3 Buckets (2)                           │               │
│  │    ├─ cloudtrail-logs (compliant)           │               │
│  │    └─ compliance-evidence (1 finding)       │               │
│  │                                             │               │
│  │  • IAM (compliant)                          │               │
│  │  • CloudTrail (compliant)                   │               │
│  │  • KMS (compliant)                          │               │
│  └─────────────────────────────────────────────┘               │
│                                                                 │
│  Export Format: .twbx (Tableau Packaged Workbook)              │
│  Publishing: Tableau Public (free, shareable link)             │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                  LAYER 6: ORCHESTRATION                         │
│                 (Python CLI & Automation)                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  cli.py (Main entry point)                                      │
│  ┌─────────────────────────────────────────────┐               │
│  │ $ python cli.py audit --all                 │               │
│  │ Running CIS AWS Compliance Audit...         │               │
│  │                                             │               │
│  │ [1/20] CIS-1.4 Root MFA............✅ PASS  │               │
│  │ [2/20] CIS-1.12 Password Policy....✅ PASS  │               │
│  │ [3/20] CIS-1.20 Access Key Age.....❌ FAIL  │               │
│  │   └─ Finding: Key 'AKIA...' is 127 days old │               │
│  │                                             │               │
│  │ Audit complete: 17/20 passed (85%)          │               │
│  │ Findings saved to compliance.db             │               │
│  │ Evidence collected in ./evidence/           │               │
│  └─────────────────────────────────────────────┘               │
│                                                                 │
│  Commands:                                                      │
│  • audit --all              Run all auditors                   │
│  • audit --control CIS-1.4  Audit specific control             │
│  • remediate --finding 42   Apply automated fix                │
│  • report --format tableau  Generate Tableau CSV               │
│  • drift-detect             Compare Terraform vs actual        │
│  • export-evidence          Package evidence artifacts         │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 💰 **COST BREAKDOWN** (100% Free)

| Component | Tool | Cost | Why Free |
|-----------|------|------|----------|
| **Cloud Infrastructure** | AWS Free Tier | $0 | 750 hours EC2 (not needed), CloudTrail, S3 (5GB), IAM unlimited |
| **Infrastructure as Code** | Terraform | $0 | Open-source (MPL 2.0 license) |
| **Python SDK** | boto3 | $0 | AWS official SDK, open-source |
| **Database** | SQLite | $0 | Public domain, embedded |
| **Visualization** | Tableau Public | $0 | Free tier with public dashboards |
| **Version Control** | Git + GitHub | $0 | Free for public repos |
| **CI/CD** | GitHub Actions | $0 | 2,000 minutes/month free |
| **IDE** | VS Code | $0 | Open-source |
| **Testing** | pytest | $0 | Open-source MIT license |

**Monthly Cost:** $0.00  
**One-time Cost:** $0.00  
**Total Project Cost:** $0.00

> **Note:** AWS Free Tier remains $0 as long as you:
> - Don't run EC2 instances (not needed for this project)
> - Keep S3 storage < 5GB (you'll use ~100MB)
> - Don't exceed API limits (you won't with manual audits)

---

## 📚 **TECHNOLOGY STACK** (Industry-Standard)

### Cloud Platform
- **AWS** - 32% market share, #1 employer demand
- **Free Tier** - 12 months (plenty for portfolio project)

### Infrastructure as Code
- **Terraform** - #1 IaC tool (36% usage in 2024)
- **HCL Language** - Declarative, readable, version-controlled

### Programming
- **Python 3.11** - #1 language for cloud automation
- **boto3** - Official AWS SDK (9M+ downloads/month)
- **Click** - CLI framework (simpler than argparse)

### Compliance Framework
- **CIS AWS Foundations Benchmark v1.5** - Industry standard
  - Used by: AWS Well-Architected, AWS Config conformance packs
  - Recognized by: SOC 2, ISO 27001, PCI-DSS auditors

### Data & Visualization
- **SQLite** - Embedded DB (used by Apple, Microsoft, Firefox)
- **Pandas** - Data analysis (#1 Python data library)
- **Tableau Public** - #1 BI tool in job postings

### Testing & Quality
- **pytest** - Industry standard Python testing
- **black** - Code formatter (opinionated, consistent)
- **mypy** - Type checking (production best practice)

---

## 🗓️ **4-WEEK IMPLEMENTATION ROADMAP**

### **Week 1: AWS Setup + Terraform Foundation** (6-8 hours)

#### Day 1-2: AWS Account Setup (2 hours)
- [ ] Create AWS free tier account
- [ ] Enable MFA on root account
- [ ] Create IAM admin user (not using root for daily tasks)
- [ ] Install AWS CLI v2
- [ ] Configure AWS profiles (`aws configure`)
- [ ] Test authentication: `aws sts get-caller-identity`

#### Day 3-4: Terraform Infrastructure (4-6 hours)
- [ ] Install Terraform 1.6+
- [ ] Create project structure:
  ```
  project-3-cloud-compliance/
  ├── terraform/
  │   ├── main.tf
  │   ├── iam.tf
  │   ├── cloudtrail.tf
  │   └── outputs.tf
  ├── auditors/
  ├── data/
  ├── evidence/
  └── README.md
  ```
- [ ] Write Terraform configs:
  - Provider setup (AWS region, credentials)
  - IAM password policy (CIS-1.12 compliant)
  - CloudTrail with encryption (CIS-2.1, 2.2, 2.7)
  - S3 bucket with versioning + encryption (CIS-2.1.x)
  - VPC with flow logs (CIS-4.1)
- [ ] Deploy: `terraform init && terraform apply`
- [ ] Verify in AWS Console

**Deliverable:** Working AWS infrastructure (7-10 resources)

---

### **Week 2: Python Auditors** (8-10 hours)

#### Day 5-6: Base Framework (3 hours)
- [ ] Create virtual environment: `python -m venv venv`
- [ ] Install dependencies:
  ```
  boto3==1.29.0
  pandas==2.1.0
  click==8.1.0
  pytest==7.4.0
  ```
- [ ] Build `base_auditor.py`:
  - AWS session management
  - Evidence collection methods
  - Control pass/fail logic
  - Database integration

#### Day 7-9: Implement 5 Auditors (5 hours)
- [ ] `iam_auditor.py` (4 controls)
  - CIS-1.4: Root MFA check
  - CIS-1.12: Password policy verification
  - CIS-1.16: IAM policy attachment check
  - CIS-1.20: Access key rotation < 90 days
  
- [ ] `logging_auditor.py` (5 controls)
  - CIS-2.1: CloudTrail enabled all regions
  - CIS-2.2: Log file validation
  - CIS-2.3: S3 bucket logging
  - CIS-2.7: CloudTrail encryption
  - CIS-2.5: AWS Config enabled
  
- [ ] `storage_auditor.py` (4 controls)
  - CIS-2.1.1: S3 encryption
  - CIS-2.1.2: S3 versioning
  - CIS-2.1.3: S3 MFA delete
  - CIS-2.1.4: Block public access
  
- [ ] `network_auditor.py` (3 controls)
  - CIS-4.1: VPC flow logs
  - CIS-4.2: Default SG restricts all
  - CIS-4.3: No 0.0.0.0/0 rules
  
- [ ] `monitoring_auditor.py` (4 controls)
  - CIS-3.1-3.4: CloudWatch alarms

#### Day 10: Testing (2 hours)
- [ ] Write pytest tests for each auditor
- [ ] Mock boto3 responses (don't hit real AWS in tests)
- [ ] Achieve >80% code coverage
- [ ] Run: `pytest tests/ --cov=auditors`

**Deliverable:** 20 automated compliance checks with tests

---

### **Week 3: Data & Evidence Collection** (4-6 hours)

#### Day 11-12: Database Schema (2 hours)
- [ ] Design SQLite schema (4 tables)
- [ ] Create migration script:
  ```python
  # migrations/001_initial_schema.sql
  CREATE TABLE controls (...);
  CREATE TABLE assessments (...);
  CREATE TABLE findings (...);
  CREATE TABLE evidence_artifacts (...);
  ```
- [ ] Populate `controls` table with 20 CIS controls
- [ ] Test insert/query functions

#### Day 13-14: Run Audits & Collect Evidence (2-4 hours)
- [ ] Execute all auditors: `python cli.py audit --all`
- [ ] Collect evidence for PASS controls:
  - Screenshot: IAM MFA settings
  - API output: `aws iam get-account-password-policy`
  - Terraform state: `terraform show`
  - CloudTrail log sample
  - S3 bucket policy JSON
- [ ] Store in `evidence/` with naming convention:
  ```
  evidence/
  ├── CIS-1.4_root_mfa_screenshot.png
  ├── CIS-1.12_password_policy.json
  ├── CIS-2.1_cloudtrail_api.txt
  └── ...
  ```
- [ ] Calculate SHA-256 hashes for integrity
- [ ] Insert into database

**Deliverable:** SQLite DB with 20 assessments + evidence artifacts

---

### **Week 4: Tableau Dashboard + Documentation** (6-8 hours)

#### Day 15-16: Export Data for Tableau (2 hours)
- [ ] Create export script: `tableau_export.py`
- [ ] Generate 3 CSVs:
  ```
  tableau_data/
  ├── compliance_scorecard.csv
  │   └─ control_id, status, score, category, severity
  ├── findings_detail.csv
  │   └─ finding_id, control_id, description, remediation, due_date
  └── evidence_log.csv
      └─ assessment_id, artifact_type, file_path, collected_date
  ```
- [ ] Validate CSVs load in Tableau Desktop (free trial)

#### Day 17-18: Build Tableau Dashboards (3-4 hours)
- [ ] Dashboard 1: Compliance Scorecard
  - KPI cards (17/20, 85%)
  - Category breakdown (pie/bar chart)
  - Pass/Fail timeline
  
- [ ] Dashboard 2: Control Details
  - Drill-down table with filters
  - Evidence links (use URLs to GitHub)
  - Compliance history line chart
  
- [ ] Dashboard 3: Findings & Remediation
  - Priority heatmap (severity x category)
  - Remediation queue table
  - Due date Gantt chart
  
- [ ] Dashboard 4: Infrastructure Map
  - AWS resource tree (using Tableau's hierarchy)
  - Color-code by compliance status
  - Terraform resource count

- [ ] Publish to Tableau Public
- [ ] Get shareable link: `https://public.tableau.com/app/profile/[yourname]/viz/...`

#### Day 19-20: Documentation & Polish (2 hours)
- [ ] Write comprehensive `README.md`:
  - Architecture diagram (ASCII or Mermaid)
  - Quick start guide (5 min setup)
  - CIS controls covered (table)
  - Evidence artifacts inventory
  - Interview talking points
  
- [ ] Create `ARCHITECTURE.md`:
  - Layer-by-layer breakdown
  - Technology choices justification
  - Production upgrade path
  
- [ ] Add `CONTRIBUTING.md` (shows open-source awareness)
- [ ] Add badges:
  ```markdown
  ![AWS](https://img.shields.io/badge/AWS-FF9900?logo=amazon-aws)
  ![Terraform](https://img.shields.io/badge/Terraform-7B42BC?logo=terraform)
  ![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python)
  ![CIS](https://img.shields.io/badge/CIS-Benchmark-green)
  ```
- [ ] Record 2-minute demo video (optional but powerful):
  - Show Tableau dashboard
  - Run `python cli.py audit --all` live
  - Show evidence artifacts
  - Explain one remediation

**Deliverable:** Production-ready portfolio project

---

## 📊 **20 CIS CONTROLS TO IMPLEMENT**

| ID | Control | Severity | Difficulty | Evidence Type |
|----|---------|----------|------------|---------------|
| **Identity & Access Management (IAM)** |
| 1.4 | Root account MFA enabled | Critical | Easy | Screenshot + API |
| 1.12 | Strong password policy (14+ chars) | High | Easy | API output |
| 1.16 | IAM policies attached to groups, not users | Medium | Medium | API + Terraform |
| 1.20 | Access keys rotated every 90 days | High | Medium | API script |
| 1.22 | IAM users unused for 90+ days disabled | Low | Medium | API + automation |
| **Logging & Monitoring** |
| 2.1 | CloudTrail enabled in all regions | Critical | Easy | API + Console |
| 2.2 | CloudTrail log file validation enabled | High | Easy | API output |
| 2.3 | CloudTrail logs integrated with CloudWatch | Medium | Medium | CloudWatch screenshot |
| 2.5 | AWS Config enabled in all regions | High | Medium | Console + API |
| 2.7 | CloudTrail logs encrypted at rest (KMS) | High | Medium | KMS key ARN proof |
| **Storage (S3)** |
| 2.1.1 | S3 buckets encrypted (SSE or KMS) | Critical | Easy | Bucket policy JSON |
| 2.1.2 | S3 bucket versioning enabled | Medium | Easy | API + console |
| 2.1.3 | S3 MFA delete enabled (high-value buckets) | High | Medium | API output |
| 2.1.4 | S3 Block Public Access enabled | Critical | Easy | API + console |
| **Monitoring (CloudWatch)** |
| 3.1 | Alarm for unauthorized API calls | High | Hard | CloudWatch alarm |
| 3.2 | Alarm for console login without MFA | High | Hard | CloudWatch + SNS |
| 3.3 | Alarm for root account usage | Critical | Hard | CloudWatch rule |
| 3.4 | Alarm for IAM policy changes | Medium | Hard | CloudWatch alarm |
| **Networking (VPC)** |
| 4.1 | VPC flow logs enabled | High | Easy | VPC console |
| 4.2 | Default security group restricts all traffic | Medium | Easy | SG rules API |

**Pass Rate Target:** 17/20 (85%) - intentionally leave 3 failing to show remediation workflow

---

## 🎓 **SKILLS YOU'LL GAIN**

### Cloud Security (Employer #1 Priority)
- AWS IAM best practices (MFA, least privilege, key rotation)
- CloudTrail forensics (who did what, when)
- S3 security (encryption, versioning, access control)
- VPC security (security groups, flow logs, network segmentation)
- KMS encryption (key management, envelope encryption)

### Compliance & GRC
- CIS Benchmark methodology (assess → score → remediate)
- Control framework mapping (CIS to NIST 800-53 crosswalk)
- Evidence collection and management
- Remediation prioritization (risk-based)
- Compliance reporting for executives

### Infrastructure as Code (IaC)
- Terraform fundamentals (HCL syntax, resources, state)
- AWS provider configuration
- Resource dependencies and dependencies
- State management (local vs remote)
- Idempotent infrastructure (apply multiple times = same result)

### Python Automation
- boto3 SDK (AWS API interaction)
- Object-oriented design (base classes, inheritance)
- CLI frameworks (Click for user-friendly commands)
- Error handling for cloud APIs (retries, rate limits)
- Logging and observability

### Testing & Quality
- pytest for cloud automation
- Mocking AWS services (don't rack up costs in tests)
- Code coverage metrics (>80% target)
- Type hints with mypy (production-grade Python)

### Data Visualization
- Tableau Public dashboards
- CSV data modeling for BI tools
- Executive-level reporting (KPIs, trend lines)
- Drill-down interactivity

---

## 🎤 **INTERVIEW TALKING POINTS**

### "Walk me through your cloud project"
> *"I built a Cloud Security Posture Management (CSPM) tool that automates CIS AWS Foundations Benchmark compliance. Using my real AWS free tier account, I deployed infrastructure with Terraform - CloudTrail for audit logs, encrypted S3 buckets, VPC with flow logs - then wrote Python auditors using boto3 to check 20 CIS controls. I achieved 85% compliance and documented 3 open findings with remediation plans. All evidence is real: screenshots, API outputs, Terraform state. I can show you the Tableau dashboard live or log into my AWS account right now."*

### "How do you handle compliance drift?"
> *"I wrote a drift detection script that compares Terraform's desired state against actual AWS resources using boto3. If someone manually disables CloudTrail, my auditor flags it as a finding within minutes. For continuous monitoring, I'd integrate AWS Config rules or set up a cron job to run audits daily. Evidence is version-controlled in Git so I have an audit trail of when drift occurred."*

### "What's your remediation process?"
> *"I prioritize findings by severity (CIS critical > high > medium) and implement fixes in Terraform first, not the console, so they're codified. For example, CIS-2.7 'CloudTrail encryption' was failing, so I added a KMS key resource in Terraform, applied it, re-ran the audit, and it passed. The finding went from 'Open' to 'Resolved' in my database with before/after evidence."*

### "How would you scale this to production?"
> *"Three upgrades: (1) Move Terraform state to S3 with DynamoDB locking for team collaboration, (2) Integrate with AWS Config for real-time compliance monitoring instead of manual audits, (3) Use AWS Security Hub which natively supports CIS Benchmark checks. My portfolio project proves I understand the fundamentals - production would add enterprise tooling on top of the same principles."*

### "Why CIS Benchmark specifically?"
> *"CIS is prescriptive, actionable, and widely adopted - AWS even provides pre-built Config conformance packs for it. It's also mapped to NIST 800-53, SOC 2, and ISO 27001, so auditors recognize it. Compared to the AWS Well-Architected Framework which is more guidance-based, CIS gives you specific pass/fail criteria like 'password must be 14+ characters' - perfect for automated auditing."*

---

## ✅ **SUCCESS CRITERIA**

### Technical Deliverables
- [ ] 12+ AWS resources deployed via Terraform
- [ ] 20 Python audit checks (5 auditor classes)
- [ ] SQLite database with 20+ assessment records
- [ ] 15+ evidence artifacts (screenshots, API outputs, configs)
- [ ] 4 Tableau dashboards published online
- [ ] 95%+ pytest code coverage
- [ ] GitHub repo with professional README

### Portfolio Impact
- [ ] Can demo live in 5 minutes (Tableau + AWS Console)
- [ ] Every claim is verifiable (no synthetic data)
- [ ] Shows cloud + GRC + Python expertise
- [ ] Unique (99% of candidates don't have this)

### Interview Readiness
- [ ] Can answer: "Show me your cloud project" with confidence
- [ ] Can log into AWS live and prove everything
- [ ] Can explain remediation for all 3 failures
- [ ] Can discuss production scaling strategy

---

## 🆚 **COMPARISON: Current Project vs CSPM**

| Aspect | Current GRC Project | CSPM Project |
|--------|---------------------|--------------|
| **Data Authenticity** | 99,288 synthetic assessments | 20 real AWS control checks |
| **Evidence** | None | 15+ screenshots, API outputs |
| **Live Demo** | ❌ Can't show real work | ✅ AWS Console + Tableau |
| **Interview Question** | "Is this fake data?" → Exposed | "Show me control AC-2" → Confident |
| **Skills Demonstrated** | Data analytics | Cloud security + GRC + IaC |
| **Employer Demand** | Medium (GRC analyst) | **High** (cloud security eng) |
| **Uniqueness** | Common (compliance dashboards) | **Rare** (real cloud compliance) |
| **Cost to Build** | $0 | $0 |
| **Time to Build** | Already 20+ hours invested | 30 hours (fresh start) |
| **Final Portfolio Score** | 6.5/10 (authenticity issues) | **9.5/10** (production-ready) |

---

## 🚀 **NEXT STEPS**

### If You Choose CSPM Project:

1. **Today (30 min):** Create AWS free tier account, enable MFA
2. **This Week:** Install Terraform, deploy first CloudTrail resource
3. **Week 2:** Write first Python auditor (iam_auditor.py)
4. **Week 3:** Collect evidence, build database
5. **Week 4:** Create Tableau dashboards, polish docs

### Quick Start Command Sequence:
```bash
# Day 1
aws configure
aws sts get-caller-identity

# Day 3
cd project-3-cloud-compliance/terraform
terraform init
terraform plan
terraform apply

# Day 7
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install boto3 pandas click pytest

# Day 14
python cli.py audit --all
# Expected: 17 PASS, 3 FAIL (intentional)

# Day 18
python tableau_export.py
# Upload CSVs to Tableau Public
```

---

## 📞 **DECISION TIME**

**Ask yourself:**
- Do you want a portfolio project you can demonstrate live with 100% confidence?
- Is 30 hours over 4 weeks manageable given your schedule?
- Do you want to learn AWS (in 64% of cloud security job postings)?

**My recommendation:** CSPM project is worth the fresh start. Current project's authenticity issues are not easily fixable without this level of rebuild anyway.

**Your call** - tell me if you want to proceed with CSPM, and I'll start generating the Terraform configs and Python starter code.
