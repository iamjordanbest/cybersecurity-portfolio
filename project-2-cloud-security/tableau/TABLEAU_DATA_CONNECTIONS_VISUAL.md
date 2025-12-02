# 📊 Tableau Data Connection Visual Guide - Step 1

## 🔗 DATA MODEL DIAGRAM

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    TABLEAU DATA CONNECTION STRATEGY                      │
└─────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────┐
│  📁 CSV FILE 1: compliance_summary_enhanced.csv (PRIMARY)                │
│  ─────────────────────────────────────────────────────────────────────── │
│  Granularity: One row per ASSESSMENT                                     │
│  Row Count: ~42 assessments                                              │
│  ─────────────────────────────────────────────────────────────────────── │
│  Key Fields:                                                              │
│   • assessment_id       (PK - Join Key)                                   │
│   • timestamp          (Date/Time)                                        │
│   • assessment_date    (Date - for trends join)                           │
│   • score              (0-100)                                            │
│   • rating             (Excellent/Good/Fair/Poor/Critical)                │
│   • total_controls     (12)                                               │
│   • passed_controls    (varies)                                           │
│   • failed_controls    (varies)                                           │
│   • account_id         (AWS Account)                                      │
└──────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ LEFT JOIN
                                    │ ON: assessment_id = assessment_id
                                    ▼
┌──────────────────────────────────────────────────────────────────────────┐
│  📁 CSV FILE 2: control_details_enhanced.csv (DETAIL TABLE)              │
│  ─────────────────────────────────────────────────────────────────────── │
│  Granularity: One row per CONTROL per ASSESSMENT                         │
│  Row Count: ~504 rows (12 controls × 42 assessments)                     │
│  ─────────────────────────────────────────────────────────────────────── │
│  Key Fields:                                                              │
│   • assessment_id       (FK - Join to Summary)                            │
│   • control_id          (CIS-1.4, CIS-2.1, etc.)                          │
│   • category            (IAM, Logging, Storage, Networking, Monitoring)   │
│   • title               (Control description)                             │
│   • status              (PASS / FAIL)                                     │
│   • compliance_status   (Compliant / Non-Compliant)                       │
│   • severity_score      (1-4: Low=1, Medium=2, High=3, Critical=4)        │
│   • primary_severity    (Critical / High / Medium / Low)                  │
│   • primary_description (Finding details)                                 │
│   • primary_remediation (Fix instructions)                                │
│   • finding_count       (Number of findings)                              │
│   • resource_ids        (AWS resource ARNs)                               │
└──────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ LEFT JOIN (Optional)
                                    │ ON: assessment_id = assessment_id
                                    │     AND control_id = control_id
                                    ▼
┌──────────────────────────────────────────────────────────────────────────┐
│  📁 CSV FILE 3: findings_detail.csv (DRILL-DOWN TABLE)                   │
│  ─────────────────────────────────────────────────────────────────────── │
│  Granularity: One row per INDIVIDUAL FINDING                              │
│  Row Count: Varies (only latest assessment's failed controls)             │
│  ─────────────────────────────────────────────────────────────────────── │
│  Key Fields:                                                              │
│   • assessment_id       (FK - Join to Summary/Details)                    │
│   • control_id          (FK - Join to Details)                            │
│   • finding_number      (1, 2, 3...)                                      │
│   • finding_severity    (Critical / High / Medium / Low)                  │
│   • description         (Specific issue)                                  │
│   • remediation         (How to fix)                                      │
│   • resource_id         (Specific AWS resource ARN)                       │
│   • category            (IAM, Logging, etc.)                              │
│   • control_title       (CIS control name)                                │
└──────────────────────────────────────────────────────────────────────────┘


             ┌────────────────────────────────────────────┐
             │  📁 CSV FILE 4: compliance_trends_enhanced │
             │  (SEPARATE DATA SOURCE - DO NOT JOIN!)    │
             ├────────────────────────────────────────────┤
             │  Granularity: One row per DATE             │
             │  Row Count: ~31 days                       │
             │  ──────────────────────────────────────────│
             │  • date (PK)                               │
             │  • avg_score                               │
             │  • trend_direction (Improving/Declining)   │
             │  • year_month                             │
             │  • day_of_week                            │
             └────────────────────────────────────────────┘
```

---

## ✅ RECOMMENDED APPROACH: PRIMARY JOIN + SEPARATE SOURCES

### **Option A: Single Connected Data Source (RECOMMENDED)**

```
Data Source: "CSPM_Compliance"

compliance_summary_enhanced.csv (LEFT)
    └─ LEFT JOIN ─> control_details_enhanced.csv
          ON: assessment_id = assessment_id
```

**Result**: 504 rows (every control for every assessment)

**Use For Dashboards:**
- ✅ Executive Summary (current score, KPIs, category breakdown)
- ✅ Technical Details (failed controls, remediation)
- ✅ Assessment history with control-level drill-down

---

### **Option B: Add Findings Detail (For Detailed Drill-Down)**

```
Data Source: "CSPM_Compliance_Detailed"

compliance_summary_enhanced.csv (LEFT)
    ├─ LEFT JOIN ─> control_details_enhanced.csv
    │     ON: assessment_id = assessment_id
    └─ LEFT JOIN ─> findings_detail.csv  
          ON: assessment_id = assessment_id 
          AND control_id = control_id
```

**Warning**: This creates MANY rows due to many-to-many relationship!
**Use Only When**: You need individual finding-level drill-down

---

### **Option C: Separate Data Source for Trends (RECOMMENDED)**

```
Data Source 1: "CSPM_Compliance" (from Option A)
Data Source 2: "CSPM_Trends" (compliance_trends_enhanced.csv - standalone)
```

**Use Data Source 2 For:**
- ✅ Daily trend line charts
- ✅ Month-over-month analysis
- ✅ Day-of-week patterns

**Why Separate?**
- Different granularity (date vs assessment_id)
- Cleaner data model
- Better performance

---

## 🎯 STEP-BY-STEP CONNECTION GUIDE

### **Step 1.1: Connect Primary Data Source**

1. **Open Tableau Public**
2. **Connect to Text File** → Select `compliance_summary_enhanced.csv`
3. **Add** (click "Add" under "Connections") → `control_details_enhanced.csv`
4. **Join Configuration:**
   - **Join Type**: ☑ Left Join
   - **Left Table**: compliance_summary_enhanced.csv
   - **Right Table**: control_details_enhanced.csv
   - **Join Clause**: `assessment_id = assessment_id`

5. **Verify Join Result:**
   - Should see ~504 rows
   - Each assessment_id appears 12 times (once per control)

---

### **Step 1.2: Add Findings Detail (Optional)**

6. **Add** → `findings_detail.csv`
7. **Join Configuration:**
   - **Join Type**: ☑ Left Join  
   - **Join Clause**: 
     - `assessment_id = assessment_id` AND
     - `control_id = control_id`

**Note**: Only add this if you need individual finding drill-down. It increases row count significantly!

---

### **Step 1.3: Create Separate Trends Data Source**

8. **Data** → **New Data Source**
9. **Connect to Text File** → Select `compliance_trends_enhanced.csv`
10. **DO NOT JOIN** - keep as standalone

**Use this source for:**
- Daily score trend charts
- Monthly aggregations  
- Weekly pattern heatmaps

---

## 📊 DASHBOARD USAGE GUIDE

### **Dashboard 1: Executive Summary**
**Data Sources**: 
- Primary: `CSPM_Compliance` (for current score, KPIs, category breakdown)
- Secondary: `CSPM_Trends` (for trend line)

**Visualizations:**
```
┌────────────────────┬─────────────────────┬────────────────────┐
│  Current Score KPI │  Total Controls KPI │ Passed Controls KPI│
│  (MAX(score))      │  (MAX(total_ctrls)) │ (MAX(passed_ctrls))│
│  Data: Compliance  │  Data: Compliance   │ Data: Compliance   │
└────────────────────┴─────────────────────┴────────────────────┘

┌────────────────────────────┬──────────────────────────────────┐
│  Score Gauge               │  30-Day Trend Line               │
│  (MAX(score))              │  (avg_score by date)             │
│  Data: Compliance          │  Data: Trends ⚠️                 │
└────────────────────────────┴──────────────────────────────────┘

┌────────────────────────────┬──────────────────────────────────┐
│  Category Donut            │  Rating Distribution             │
│  (category, compliance %)  │  (COUNT by rating)               │
│  Data: Compliance          │  Data: Compliance                │
└────────────────────────────┴──────────────────────────────────┘
```

---

### **Dashboard 2: Technical Details**
**Data Source**: `CSPM_Compliance` only

**Visualizations:**
```
┌──────────────────────────────────────────────────────────────┐
│  Failed Controls Table                                        │
│  Filter: compliance_status = "Non-Compliant"                  │
│  Columns: control_id, title, primary_severity, remediation   │
│  Sort: severity_score DESC                                    │
│  Data: Compliance                                             │
└──────────────────────────────────────────────────────────────┘

┌───────────────────────────┬──────────────────────────────────┐
│  Remediation Priority     │  Category Breakdown              │
│  (severity by control)    │  (Stacked bars: Pass/Fail)       │
│  Data: Compliance         │  Data: Compliance                │
└───────────────────────────┴──────────────────────────────────┘
```

---

### **Dashboard 3: Trend Analysis**
**Data Source**: `CSPM_Trends` only

**Visualizations:**
```
┌──────────────────────────────────────────────────────────────┐
│  Daily Score Movement                                         │
│  (avg_score by date with trend_direction color)              │
│  Data: Trends                                                 │
└──────────────────────────────────────────────────────────────┘

┌───────────────────────────┬──────────────────────────────────┐
│  Weekly Heatmap           │  Monthly Summary                 │
│  (score by week/day)      │  (AVG(avg_score) by year_month)  │
│  Data: Trends             │  Data: Trends                    │
└───────────────────────────┴──────────────────────────────────┘
```

---

## ⚠️ COMMON MISTAKES TO AVOID

### ❌ **WRONG: Joining Trends to Summary**
```
compliance_summary_enhanced 
  └─ LEFT JOIN ─> compliance_trends_enhanced
        ON: date(timestamp) = date
```

**Problem**: Creates incorrect granularity - one summary row multiplied by daily trend rows!

**Fix**: Use separate data sources and blend on dashboard

---

### ❌ **WRONG: Joining All 4 Files Together**
```
summary → control_details → findings_detail → trends
```

**Problem**: 
- Cartesian product creates thousands of duplicate rows
- Wrong aggregations
- Performance issues

**Fix**: Join only summary + control_details, keep others separate

---

## ✅ VALIDATION CHECKLIST

After connecting data, verify:

- [ ] Primary data source shows **504 rows** (42 assessments × 12 controls)
- [ ] `assessment_id` appears **12 times** for latest assessment
- [ ] `control_id` appears **42 times** for each control
- [ ] Trends data source shows **~31 rows** (one per date)
- [ ] No null values in join keys (assessment_id, control_id)
- [ ] Score values match source CSV (66.7%, 75%, etc.)
- [ ] Category breakdown shows 5 categories (IAM, Logging, Storage, Networking, Monitoring)

---

## 🎨 RECOMMENDED TABLEAU FIELDS SETUP

### **Create Calculated Fields:**

1. **Is Failed Control**
   ```
   [compliance_status] = "Non-Compliant"
   ```

2. **Compliance Percentage**
   ```
   SUM([passed_controls]) / SUM([total_controls])
   ```

3. **Severity Color**
   ```
   CASE [primary_severity]
     WHEN "Critical" THEN "#E53935"
     WHEN "High" THEN "#FF7043"
     WHEN "Medium" THEN "#FFA726"
     WHEN "Low" THEN "#66BB6A"
   END
   ```

4. **Latest Assessment Filter**
   ```
   [assessment_id] = { MAX([assessment_id]) }
   ```

---

## 🚀 QUICK START

**Fastest Path to Working Dashboard:**

1. **Connect**: `compliance_summary_enhanced.csv`
2. **Join**: `control_details_enhanced.csv` on `assessment_id`
3. **Create Sheet 1**: Current Score gauge (MAX(score))
4. **Create Sheet 2**: Category donut (category, CNT(control_id), colored by compliance_status)  
5. **Create Sheet 3**: Failed controls table (filter: Is Failed Control = TRUE)
6. **New Data Source**: `compliance_trends_enhanced.csv`
7. **Create Sheet 4**: Trend line (date, avg_score)
8. **Combine** in dashboard

**Time**: 5-7 minutes
**Result**: Functional compliance dashboard ready for customization!

---

✅ **Data model designed for Tableau best practices**
✅ **Optimized for performance (minimal joins)**
✅ **Clear separation of concerns (summary vs detail vs trends)**
✅ **Ready for executive and technical dashboards**
