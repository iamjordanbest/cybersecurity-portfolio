# Risk Scoring Methodology

## Overview

This document describes the mathematical models and business logic used to calculate risk scores, compliance scores, and ROI metrics in the GRC Analytics platform.

---

## 1. Individual Control Risk Score

### Formula

```
risk_score = control_weight × status_multiplier × staleness_factor × business_impact_weight × control_type_factor × automation_factor
```

### Components

#### 1.1 Control Weight (1.0 - 10.0)
Represents the inherent importance of the control to the organization's security posture.

| Weight | Interpretation | Example Controls |
|--------|----------------|------------------|
| 9.0-10.0 | Critical | MFA, Encryption, Access Control |
| 7.0-8.9 | High | Audit Logging, Incident Response |
| 5.0-6.9 | Medium | Configuration Management, Training |
| 3.0-4.9 | Low-Medium | Documentation, Labeling |
| 1.0-2.9 | Low | Supporting processes |

**Assignment Criteria:**
- Controls protecting sensitive data: 8.0+
- Controls in compliance requirements: 7.0+
- Controls for business-critical systems: 8.0+
- Supporting/administrative controls: 3.0-5.0

#### 1.2 Status Multiplier

| Status | Multiplier | Rationale |
|--------|-----------|-----------|
| `fail` | 3.0 | Maximum risk - control is broken |
| `not_tested` | 2.0 | High risk - unknown state |
| `warn` | 1.5 | Moderate risk - partial implementation |
| `pass` | 0.1 | Low residual risk - control working |
| `not_applicable` | 0.0 | No risk - control doesn't apply |

**Example:**
- Control with weight 8.0 that fails: 8.0 × 3.0 = 24.0 risk contribution
- Same control passing: 8.0 × 0.1 = 0.8 risk contribution

#### 1.3 Staleness Factor

Accounts for how long a control has been overdue for testing.

```python
days_overdue = max(0, current_date - next_test_due)
staleness_factor = min(
    1.0 + (days_overdue × daily_penalty),
    max_staleness_factor
)
```

**Parameters:**
- `daily_penalty = 0.00274` (~1.0 increase per year)
- `max_staleness_factor = 3.0` (cap at 3x risk)

**Examples:**
| Days Overdue | Staleness Factor | Interpretation |
|--------------|------------------|----------------|
| 0 | 1.0 | On time - no penalty |
| 30 | 1.08 | 1 month overdue - 8% increase |
| 90 | 1.25 | 3 months overdue - 25% increase |
| 180 | 1.49 | 6 months overdue - 49% increase |
| 365 | 2.00 | 1 year overdue - 100% increase |
| 730+ | 3.00 | 2+ years - capped at 3x |

#### 1.4 Business Impact Weight

| Impact Level | Weight | Use Case |
|--------------|--------|----------|
| `critical` | 2.0 | Controls protecting critical business functions |
| `high` | 1.5 | Controls protecting important operations |
| `medium` | 1.0 | Standard business operations |
| `low` | 0.5 | Supporting/non-critical functions |

#### 1.5 Control Type Factor

Based on NIST control classifications:

| Type | Factor | Rationale |
|------|--------|-----------|
| `preventive` | 1.2 | Highest priority - stops incidents before they occur |
| `detective` | 1.0 | Standard - identifies incidents |
| `corrective` | 0.8 | Lower priority - fixes issues after detection |

#### 1.6 Automation Factor

| Automation Status | Factor | Rationale |
|-------------------|--------|-----------|
| `manual` | 1.0 | Standard risk - human error possible |
| `automated` | 0.8 | 20% risk reduction - consistent execution |

### Complete Example Calculation

**Control: Multi-Factor Authentication (MFA)**
- `control_weight` = 9.0 (critical security control)
- `status` = fail → `status_multiplier` = 3.0
- `days_overdue` = 60 → `staleness_factor` = 1.16
- `business_impact` = critical → `business_impact_weight` = 2.0
- `control_type` = preventive → `control_type_factor` = 1.2
- `automated` = true → `automation_factor` = 0.8

```
risk_score = 9.0 × 3.0 × 1.16 × 2.0 × 1.2 × 0.8
risk_score = 60.0
```

**Interpretation:** Score of 60.0 is very high risk and should be prioritized for immediate remediation.

---

## 2. Aggregate Risk Scores

### 2.1 NIST Family Risk Score

Sum of all control risk scores within a family:

```
family_risk_score = Σ(control_risk_score) for all controls in family
```

**Example: Access Control (AC) Family**
- AC-1 (Policy): 2.5
- AC-2 (Account Mgmt): 45.0 (failed)
- AC-3 (Access Enforcement): 3.0
- AC-17 (Remote Access): 25.0 (failed)
- ...
- **Total AC Family Risk: 120.5**

### 2.2 Overall Organizational Risk Score

```
total_risk_score = Σ(control_risk_score) for all active controls
```

Where "active" means `status != 'not_applicable'`

---

## 3. Compliance Score Calculation

### 3.1 Overall Compliance Score (0-100)

```python
# Calculate maximum possible risk
max_possible_risk = sum(control_weight × max_status_multiplier × max_staleness × max_impact × max_control_type × max_automation)

# Calculate actual risk
actual_risk = sum(individual_risk_scores)

# Compliance score (inverse of risk)
compliance_score = 100 - (actual_risk / max_possible_risk × 100)
```

**Simplified Version (Pass Rate Method):**
```python
total_controls = count(controls where status != 'not_applicable')
passing_controls = count(controls where status == 'pass')
compliance_score = (passing_controls / total_controls) × 100
```

### 3.2 Compliance Score Thresholds

| Score Range | Rating | Description |
|-------------|--------|-------------|
| 95-100 | Excellent | Audit-ready, minimal risk |
| 85-94 | Good | Strong compliance posture |
| 75-84 | Acceptable | Moderate gaps exist |
| 60-74 | Needs Improvement | Significant gaps |
| 0-59 | Poor | Critical compliance issues |

### 3.3 Family-Level Compliance

```python
family_compliance = (
    count(passing_controls_in_family) / 
    count(total_controls_in_family)
) × 100
```

---

## 4. Trend Analysis

### 4.1 Compliance Velocity

Rate of improvement or degradation in compliance score:

```python
# Get compliance scores from last N months
scores = [score_month_1, score_month_2, ..., score_month_n]
dates = [date_1, date_2, ..., date_n]

# Calculate linear regression slope
velocity = linear_regression_slope(dates, scores)
```

**Interpretation:**
- `velocity > 0`: Improving (e.g., +2.5 points/month)
- `velocity = 0`: Stable
- `velocity < 0`: Degrading (e.g., -1.2 points/month)

### 4.2 Trajectory Projection

Predict future compliance score:

```python
current_score = 75
velocity = 2.5  # points per month
months_ahead = 3

projected_score = min(100, current_score + (velocity × months_ahead))
# projected_score = 82.5
```

### 4.3 Control Remediation Velocity

Controls fixed per time period:

```python
# Count status changes from fail/warn → pass
remediated_count = count(
    controls where 
        status_previous IN ('fail', 'warn') AND 
        status_current = 'pass'
    within time_period
)

velocity = remediated_count / months_in_period
# Example: 15 controls fixed over 3 months = 5 controls/month
```

### 4.4 Time to Full Compliance (Estimate)

```python
current_compliance = 75
target_compliance = 95
velocity = 2.5  # points per month

months_to_target = (target_compliance - current_compliance) / velocity
# months_to_target = (95 - 75) / 2.5 = 8 months
```

---

## 5. ROI Calculation

### 5.1 Risk Exposure (Before Remediation)

```python
# Calculate breach probability
base_probability = 0.27  # 27% industry average
family_multipliers = {
    'AC': 2.5,
    'IA': 2.0,
    'SC': 2.2,
    # ... other families
}

# Aggregate multiplier based on failed controls
breach_probability = base_probability
for family, multiplier in family_multipliers.items():
    if has_failed_controls(family):
        breach_probability *= multiplier

# Expected breach cost
expected_breach_cost = 4_450_000  # Industry average
industry_multiplier = 1.0  # Adjust by industry

# Risk Adjusted Loss Expectancy (RALE)
risk_exposure = breach_probability × expected_breach_cost × industry_multiplier
```

**Example:**
- Organization with failed AC and IA controls
- `breach_probability = 0.27 × 2.5 × 2.0 = 1.35` (capped at 1.0 = 100%)
- `expected_breach_cost = $4,450,000`
- **Risk Exposure = $4,450,000**

### 5.2 Remediation Cost

```python
remediation_costs = {
    'low': 20 hours × $150/hour = $3,000,
    'medium': 80 hours × $150/hour = $12,000,
    'high': 200 hours × $150/hour = $30,000
}

total_remediation_cost = sum(
    remediation_costs[control.remediation_cost] 
    for control in failed_controls
)
```

**Example:**
- 5 low-cost fixes: 5 × $3,000 = $15,000
- 3 medium-cost fixes: 3 × $12,000 = $36,000
- 1 high-cost fix: 1 × $30,000 = $30,000
- **Total: $81,000**

### 5.3 Risk Reduction Value

```python
# Probability after remediation
breach_probability_after = base_probability × 0.4  # 60% reduction
risk_exposure_after = breach_probability_after × expected_breach_cost

# Risk reduction value
risk_reduction_value = risk_exposure_before - risk_exposure_after
```

**Example:**
- Risk before: $4,450,000
- Risk after: $480,600 (60% reduction)
- **Risk Reduction Value: $3,969,400**

### 5.4 Net ROI Calculation

```python
net_benefit = risk_reduction_value - total_remediation_cost
roi_percentage = (net_benefit / total_remediation_cost) × 100

# With time value of money (3-year analysis)
discount_rate = 0.05  # 5% annual
analysis_period = 3  # years

annual_benefit = risk_reduction_value / analysis_period
npv = sum(
    annual_benefit / (1 + discount_rate) ** year 
    for year in range(1, analysis_period + 1)
) - total_remediation_cost
```

**Example:**
- Risk reduction value: $3,969,400
- Remediation cost: $81,000
- Net benefit: $3,888,400
- **ROI: 4,800%**
- **NPV (3-year): $3,537,000**

### 5.5 Payback Period

```python
# Time to recover remediation investment
monthly_risk_reduction = risk_reduction_value / 12
payback_months = total_remediation_cost / monthly_risk_reduction
```

**Example:**
- Monthly risk reduction: $3,969,400 / 12 = $330,783
- Total remediation cost: $81,000
- **Payback Period: 0.24 months (~7 days)**

---

## 6. Prioritization Scoring

### 6.1 Remediation Priority Score

Determines which controls to fix first:

```python
priority_score = (
    risk_score × 
    (1 / remediation_cost_factor) × 
    business_impact_weight
)

remediation_cost_factors = {
    'low': 1.0,
    'medium': 2.5,
    'high': 5.0
}
```

**Interpretation:** Higher priority score = fix first

**Example Comparison:**

| Control | Risk Score | Remediation Cost | Business Impact | Priority Score | Rank |
|---------|-----------|------------------|-----------------|----------------|------|
| AC-2 | 60.0 | low (1.0) | critical (2.0) | 120.0 | 1 |
| IA-2 | 55.0 | medium (2.5) | critical (2.0) | 44.0 | 2 |
| SC-7 | 50.0 | high (5.0) | high (1.5) | 15.0 | 3 |
| CM-6 | 30.0 | low (1.0) | medium (1.0) | 30.0 | 4 |

**Recommendation: Fix AC-2 first** (highest priority score, low cost, critical impact)

### 6.2 Quick Wins Analysis

Identifies high-impact, low-effort fixes:

```python
quick_wins = controls where (
    risk_score > 40 AND
    remediation_cost == 'low' AND
    business_impact IN ('critical', 'high')
)

sorted by priority_score DESC
```

---

## 7. Scenario Modeling (What-If Analysis)

### 7.1 Impact of Fixing Specific Controls

```python
# Current state
current_risk_score = 450.0
current_compliance_score = 72

# Proposed remediation
controls_to_fix = ['AC-2', 'AC-3', 'IA-2']
risk_reduction = sum(control.risk_score for control in controls_to_fix)

# Projected state
projected_risk_score = current_risk_score - risk_reduction
projected_compliance_score = calculate_compliance(projected_risk_score)
improvement = projected_compliance_score - current_compliance_score
```

**Example Output:**
```
If you fix controls AC-2, AC-3, and IA-2:
- Current compliance: 72%
- Projected compliance: 85% (+13 percentage points)
- Investment required: $48,000
- Time to implement: 6 weeks
- ROI: 3,200%
```

### 7.2 Resource Allocation Scenarios

**Scenario A: Fix Top 5 Critical Controls**
- Investment: $100,000
- Compliance improvement: 72% → 88%
- Time: 8 weeks

**Scenario B: Fix All Low-Cost Controls**
- Investment: $45,000
- Compliance improvement: 72% → 81%
- Time: 4 weeks

**Scenario C: Fix All Access Control (AC) Family**
- Investment: $150,000
- Compliance improvement: 72% → 90%
- Time: 12 weeks

---

## 8. Validation and Calibration

### 8.1 Score Validation

Periodic checks to ensure scores align with business reality:

1. **Sanity Checks:**
   - No control should have risk_score > 100
   - Compliance score should be between 0-100
   - Passing controls should have low risk scores (<5.0)

2. **Calibration Reviews:**
   - Quarterly review of control weights with security team
   - Adjust weights based on incident data
   - Update business impact ratings based on business changes

3. **Comparative Analysis:**
   - Compare scores to industry benchmarks
   - Validate against external audit findings
   - Cross-reference with actual security incidents

### 8.2 Model Limitations

**Assumptions:**
- Control effectiveness is binary or categorized (pass/warn/fail)
- All controls are independent (no interdependencies modeled)
- Linear relationship between control failures and breach probability
- Industry average breach costs apply to organization

**Not Modeled:**
- Control interdependencies (e.g., AC-3 depends on AC-2)
- Compensating controls
- Defense-in-depth layers
- Threat landscape changes
- Zero-day vulnerabilities

---

## 9. Configuration Parameters

All scoring parameters are configurable via `config/scoring.yaml` and `config/roi_parameters.yaml`.

### Key Tunable Parameters

| Parameter | Default | Tuning Guidance |
|-----------|---------|-----------------|
| `status_multipliers` | fail=3.0, warn=1.5 | Increase for more risk-averse scoring |
| `daily_penalty` | 0.00274 | Increase to penalize overdue controls more |
| `max_staleness_factor` | 3.0 | Cap prevents extreme staleness penalties |
| `business_impact_weights` | critical=2.0 | Adjust based on business criticality |
| `hourly_rate` | $150 | Use actual contractor/staff rates |
| `base_probability` | 0.27 | Update with latest industry data |
| `expected_breach_cost` | $4.45M | Adjust for organization size/industry |

---

## 10. Reporting Formulas

### 10.1 Executive Summary Metrics

```python
metrics = {
    'overall_compliance_score': compliance_score,
    'total_controls': count(active_controls),
    'passing_controls': count(controls where status='pass'),
    'failing_controls': count(controls where status='fail'),
    'critical_failures': count(controls where status='fail' AND business_impact='critical'),
    'overdue_controls': count(controls where next_test_due < today),
    'average_risk_per_control': total_risk_score / count(controls),
    'top_risky_family': family with highest aggregate risk score,
    'compliance_velocity': monthly rate of improvement,
    'time_to_95_percent': months to reach 95% compliance at current velocity
}
```

### 10.2 Family-Level Metrics

```python
for family in nist_families:
    metrics[family] = {
        'total_controls': count(controls in family),
        'pass_rate': percent passing,
        'aggregate_risk': sum of risk scores,
        'top_risk_control': highest risk control,
        'priority_fixes': controls with priority_score > threshold
    }
```

---

**Document Version:** 1.0  
**Last Updated:** 2024-11-03  
**Model Version:** scoring_v1.0  
**Maintainer:** Jordan Best

**References:**
- NIST SP 800-53 Rev 5
- IBM Cost of Data Breach Report 2023
- Ponemon Institute Cost Studies
- FAIR (Factor Analysis of Information Risk) Framework
