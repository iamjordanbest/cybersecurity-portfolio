# 🛡️ GRC Analytics Dashboard - Setup Guide

## Quick Start (3 Steps)

### Step 1: Ensure Dependencies are Installed
```bash
cd project-2-grc-compliance
pip install streamlit plotly pandas pyyaml
```

### Step 2: Launch the Dashboard
```bash
streamlit run src/dashboard/app.py
```

### Step 3: Open in Browser
The dashboard will automatically open at: **http://localhost:8501**

If it doesn't open automatically, manually navigate to that URL in your browser.

---

## 📋 Dashboard Features

### 🏠 Executive Summary
- **Real-time KPIs**: Compliance %, high-risk controls, remediation progress, ROI
- **6-Month Trend Chart**: Interactive line chart showing compliance over time
- **Risk Distribution**: Pie chart breaking down controls by risk level
- **Quick Insights**: At-a-glance view of organizational security posture

### ⚠️ Risk Analysis
- **Priority-Based Filtering**: View controls by risk threshold
- **Threat Intelligence**: KEV CVE and MITRE ATT&CK technique counts
- **Interactive Table**: Sortable, searchable control list
- **Color-Coded Priorities**: Visual indicators for critical/high/medium/low risk
- **Compliance Status**: Current state of each control

### 📈 Compliance Trends
- **Historical Analysis**: Month-over-month compliance tracking
- **Velocity Calculator**: Rate of compliance change
- **Projections**: 3-month compliance forecast
- **Family Breakdown**: Performance by control family
- **Stacked Bar Charts**: Visual representation of compliant/partial/non-compliant
- **Remediation Tracking**: Status of all remediation actions

### 💰 ROI Analysis
- **Portfolio Metrics**: Total investment and return calculations
- **Top 10 Controls**: Highest ROI investment opportunities
- **Financial Justification**: NPV, payback period, risk reduction value
- **Investment Recommendations**: Data-driven prioritization
- **Interactive Charts**: Visual ROI comparison

---

## 🖥️ System Requirements

### Minimum Requirements:
- **Python**: 3.9 or higher
- **RAM**: 2GB minimum, 4GB recommended
- **Storage**: 500MB for data and cache
- **Browser**: Chrome, Firefox, Safari, or Edge (latest versions)

### Required Python Packages:
```
streamlit>=1.50.0
plotly>=6.5.0
pandas>=2.0.0
pyyaml>=6.0
sqlite3 (built-in)
```

---

## 🚀 Launch Methods

### Method 1: Direct Streamlit Command (Recommended)
```bash
cd project-2-grc-compliance
streamlit run src/dashboard/app.py
```

### Method 2: Python Launcher Script
```bash
cd project-2-grc-compliance
python run_dashboard.py
```

### Method 3: Custom Port
```bash
streamlit run src/dashboard/app.py --server.port 8502
```

### Method 4: Network Access (Access from Other Devices)
```bash
streamlit run src/dashboard/app.py --server.address 0.0.0.0 --server.port 8501
```
Then access from any device on your network at: `http://[YOUR_IP]:8501`

---

## ⚙️ Configuration Options

### Change Default Port
```bash
streamlit run src/dashboard/app.py --server.port 9000
```

### Disable Auto-Open Browser
```bash
streamlit run src/dashboard/app.py --server.headless true
```

### Enable Debug Mode
```bash
streamlit run src/dashboard/app.py --logger.level debug
```

### Custom Theme
Create `.streamlit/config.toml` in the project directory:
```toml
[theme]
primaryColor = "#1f77b4"
backgroundColor = "#ffffff"
secondaryBackgroundColor = "#f0f2f6"
textColor = "#262730"
font = "sans serif"
```

---

## 🔍 Navigation Guide

### Sidebar Navigation
- **Select View**: Choose between 4 main dashboards
- **About Section**: Quick information about the platform
- **Last Updated**: Timestamp of current data load

### Dashboard Views

#### 1. Executive Summary
**Purpose**: High-level overview for leadership
**Key Metrics**:
- Current compliance percentage
- Number of high-risk controls
- Remediation completion rate
- Portfolio ROI

**Use Cases**:
- Board presentations
- Executive briefings
- Quarterly reviews
- Stakeholder updates

#### 2. Risk Analysis
**Purpose**: Detailed risk assessment and prioritization
**Key Features**:
- Sortable control list by priority score
- Threat intelligence integration
- Compliance status tracking
- Risk distribution visualization

**Use Cases**:
- Security team prioritization
- Vulnerability management
- Threat response planning
- Control remediation

#### 3. Compliance Trends
**Purpose**: Historical analysis and projections
**Key Features**:
- Month-over-month trends
- Compliance velocity
- Family-level analysis
- Remediation tracking

**Use Cases**:
- Compliance reporting
- Trend analysis
- Program maturity assessment
- Resource planning

#### 4. ROI Analysis
**Purpose**: Financial justification for security investments
**Key Features**:
- Cost-benefit analysis
- Payback period calculations
- Risk reduction value
- Investment recommendations

**Use Cases**:
- Budget requests
- Investment prioritization
- Business case development
- CFO presentations

---

## 🎯 Dashboard Interactions

### Filtering & Sorting
- **Tables**: Click column headers to sort
- **Risk Threshold**: Adjust in the code to filter by priority
- **Date Range**: Historical data automatically loaded

### Data Refresh
- **Auto-Refresh**: Dashboard loads latest data on start
- **Manual Refresh**: Press 'R' or click 'Rerun' in top-right
- **Cache Clear**: Use Streamlit menu → Clear Cache

### Exporting Data
Currently, exports are available through:
1. HTML reports (already generated)
2. Browser screenshot tools
3. Print to PDF from browser
4. Manual CSV export (can be added)

---

## 🐛 Troubleshooting

### Issue: "ModuleNotFoundError: No module named 'streamlit'"
**Solution**:
```bash
pip install streamlit plotly pandas pyyaml
```

### Issue: "Address already in use"
**Solution**: Another service is using port 8501
```bash
# Use a different port
streamlit run src/dashboard/app.py --server.port 8502

# Or kill the existing process
# Windows: netstat -ano | findstr :8501
# Then: taskkill /PID [PID] /F
```

### Issue: "Database not found"
**Solution**: Verify database exists
```bash
python scripts/initialize_database.py
python src/ingestion/run_all_ingestion.py
python scripts/generate_mock_compliance_data.py
```

### Issue: Dashboard loads but shows errors
**Solution**: Check database integrity
```bash
python scripts/test_analytics.py
```

### Issue: Slow performance
**Solution**: 
- Clear browser cache
- Close other tabs
- Restart Streamlit server
- Check database size (should be ~100MB)

### Issue: Charts not displaying
**Solution**:
```bash
pip install --upgrade plotly
# Clear browser cache
# Try different browser
```

---

## 🔄 Updating Data

### Refresh Compliance Data
```bash
python scripts/generate_mock_compliance_data.py
```

### Recalculate Risk Scores
```python
from src.analytics.risk_scoring import RiskScoringEngine

with RiskScoringEngine('data/processed/grc_analytics.db') as engine:
    engine.calculate_all_risk_scores(recalculate=True)
```

### Refresh Dashboard
After updating data:
1. Press 'R' in the dashboard
2. Or restart the Streamlit server

---

## 📸 Screenshots & Sharing

### Take Screenshots
Use browser built-in tools or:
- **Windows**: Windows Key + Shift + S
- **Mac**: Cmd + Shift + 4
- **Browser**: F12 → Device Toolbar → Screenshot

### Share Dashboard Link
If running on a server:
```bash
streamlit run src/dashboard/app.py --server.address 0.0.0.0
# Share: http://[YOUR_IP]:8501
```

### Export as PDF
1. Open dashboard in browser
2. Print (Ctrl+P / Cmd+P)
3. Select "Save as PDF"
4. Adjust layout as needed

---

## 🎨 Customization

### Change Dashboard Title
Edit `src/dashboard/app.py`:
```python
st.set_page_config(
    page_title="Your Custom Title",
    page_icon="🔒",
    layout="wide"
)
```

### Add Custom Metrics
In any dashboard function, add:
```python
col1, col2 = st.columns(2)
with col1:
    st.metric("Custom Metric", "Value", "Change")
```

### Modify Color Scheme
Edit the CSS in `src/dashboard/app.py`:
```python
st.markdown("""
<style>
    .metric-card {
        background: your-gradient;
    }
</style>
""", unsafe_allow_html=True)
```

---

## 🔐 Security Considerations

### Local Use Only (Default)
Dashboard runs on localhost by default - only accessible from your machine.

### Network Access
If enabling network access:
- Use firewall rules to restrict access
- Consider VPN for remote access
- Do not expose to public internet without authentication
- Streamlit does not include built-in authentication

### Data Protection
- Database contains sensitive compliance data
- Keep backups secure
- Use appropriate file permissions
- Consider encryption for production use

---

## 📊 Performance Optimization

### Speed Up Loading
```python
# Add caching to analytics functions
@st.cache_data(ttl=3600)  # Cache for 1 hour
def load_data():
    # Your data loading code
    pass
```

### Reduce Memory Usage
- Limit historical data range
- Implement pagination for large tables
- Use data aggregation where possible

### Improve Responsiveness
- Use Streamlit's native caching
- Optimize database queries
- Implement lazy loading

---

## 🆘 Getting Help

### Check Logs
Streamlit logs appear in the terminal where you started the server.

### Verify Installation
```bash
streamlit --version
python --version
pip list | grep streamlit
```

### Test Components
```bash
python scripts/test_analytics.py
```

### Community Support
- Streamlit Docs: https://docs.streamlit.io
- Streamlit Forum: https://discuss.streamlit.io
- GitHub Issues: Report bugs in project repository

---

## 📚 Additional Resources

### Documentation
- `docs/ARCHITECTURE.md` - System architecture
- `docs/DATA_MODEL.md` - Database schema
- `docs/SCORING_METHODOLOGY.md` - Risk scoring details
- `QUICKSTART.md` - Quick start guide
- `REPORT_HIGHLIGHTS.md` - Report insights

### Code Examples
- `scripts/test_analytics.py` - Analytics module examples
- `src/analytics/` - Analytics engine code
- `src/dashboard/app.py` - Dashboard implementation

### Video Tutorials
*(Can be added later)*
- Dashboard walkthrough
- Analytics deep-dive
- Customization guide

---

## ✨ Tips & Tricks

### Keyboard Shortcuts
- **R**: Rerun the app
- **C**: Clear cache
- **Ctrl/Cmd + Shift + R**: Hard refresh

### Browser DevTools
- F12: Open developer tools
- Check console for errors
- Monitor network requests

### Data Exploration
- Use sidebar to switch views quickly
- Hover over charts for details
- Sort tables to find patterns

### Presentation Mode
- Press F11 for fullscreen
- Use "wide" layout for better visibility
- Zoom browser if needed

---

**Dashboard Version:** 1.0  
**Last Updated:** 2025-11-18  
**Platform:** GRC Analytics Platform
