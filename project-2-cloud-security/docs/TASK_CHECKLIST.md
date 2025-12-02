# CSPM Project: 4-Week Task Breakdown

## Week 1: AWS + Terraform Foundation (6-8 hours)
- [x] Create AWS free tier account <!-- id: 1 -->
- [/] Enable root MFA, create IAM admin user <!-- id: 2 -->
- [x] Install AWS CLI + Terraform <!-- id: 3 -->
- [x] Write Terraform configs (IAM, CloudTrail, S3, VPC) <!-- id: 4 -->
- [x] Deploy infrastructure: `terraform apply` <!-- id: 5 -->
- [x] Verify 7-10 resources in AWS Console <!-- id: 6 -->

## Week 2: Python Auditors (8-10 hours)
- [x] Create project structure + venv <!-- id: 7 -->
- [x] Build base_auditor.py framework <!-- id: 8 -->
- [x] Implement iam_auditor.py (4 controls) <!-- id: 9 -->
- [x] Implement logging_auditor.py (5 controls) <!-- id: 10 -->
- [x] Implement storage_auditor.py (4 controls) <!-- id: 11 -->
- [x] Implement network_auditor.py (3 controls) <!-- id: 12 -->
- [x] Implement monitoring_auditor.py (4 controls) <!-- id: 13 -->
- [ ] Write pytest tests (>80% coverage) <!-- id: 14 -->

## Week 3: Data & Evidence (4-6 hours)
- [x] Design SQLite schema (4 tables) <!-- id: 15 -->
- [x] Create migration script <!-- id: 16 -->
- [x] Populate controls table (20 CIS controls) <!-- id: 17 -->
- [x] Run audits: `python cli.py audit --all` <!-- id: 18 -->
- [ ] Collect evidence (screenshots, API outputs) <!-- id: 19 -->
- [ ] Store evidence with SHA-256 hashes <!-- id: 20 -->
- [x] Insert assessments into database <!-- id: 21 -->

## Week 4: Tableau + Documentation (6-8 hours)
- [x] Create tableau_export.py script <!-- id: 22 -->
- [x] Generate 3 CSVs for Tableau <!-- id: 23 -->
- [ ] Build Dashboard 1: Compliance Scorecard <!-- id: 24 -->
- [ ] Build Dashboard 2: Control Details <!-- id: 25 -->
- [ ] Build Dashboard 3: Findings & Remediation <!-- id: 26 -->
- [ ] Build Dashboard 4: Infrastructure Map <!-- id: 27 -->
- [ ] Publish to Tableau Public <!-- id: 28 -->
- [ ] Write README.md with architecture diagram <!-- id: 29 -->
- [ ] Create ARCHITECTURE.md technical details <!-- id: 30 -->
- [ ] Add badges and polish documentation <!-- id: 31 -->
- [ ] (Optional) Record 2-minute demo video <!-- id: 32 -->

## Final Checklist
- [ ] All 20 controls assessed (17 pass, 3 fail intentionally) <!-- id: 33 -->
- [ ] 15+ evidence artifacts collected <!-- id: 34 -->
- [ ] 4 Tableau dashboards live on public.tableau.com <!-- id: 35 -->
- [ ] GitHub repo with professional README <!-- id: 36 -->
- [ ] Can demo live in <5 minutes <!-- id: 37 -->
- [ ] Total cost: $0.00 verified <!-- id: 38 -->
