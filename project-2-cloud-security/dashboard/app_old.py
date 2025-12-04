import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sys
import os

# Add current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from metrics_generator import (
    get_executive_metrics,
    get_category_performance,
    get_compliance_trends,
    get_failed_controls,
    get_all_controls_status,
    get_total_cis_controls
)

# Page Configuration
st.set_page_config(
    page_title="CSPM Auditor Dashboard",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Title and Header
st.title("🛡️ Cloud Security Posture Management (CSPM) Auditor")
st.markdown("""
**Enterprise-Grade AWS Security Compliance Dashboard**  
*Production-ready automated security posture assessment against CIS AWS Foundations Benchmark v1.4.0*

This dashboard demonstrates real-world cybersecurity engineering capabilities by implementing:
- **Automated Security Auditing**: Continuous compliance monitoring across AWS services
- **Risk-Based Prioritization**: Controls categorized by CRITICAL/HIGH/MEDIUM severity
- **Enterprise Reporting**: Executive dashboards with actionable remediation guidance
- **Regulatory Compliance**: CIS Benchmark alignment for audit readiness

**🎯 Business Impact**: This tool reduces manual security audits from weeks to minutes, enabling rapid compliance verification and continuous security monitoring at enterprise scale.
""")

# Load Data
metrics = get_executive_metrics()
cis_stats = get_total_cis_controls()

if not metrics:
    st.error("No assessment data found. Please run 'python cli.py audit' first.")
    st.stop()

# Sidebar
st.sidebar.header("📊 Audit Summary")
st.sidebar.metric("Compliance Score", f"{metrics['score']:.1f}%", delta_color="normal")

col1, col2 = st.sidebar.columns(2)
col1.metric("Passed", int(metrics['passed']))
col2.metric("Failed", int(metrics['failed']), delta=-int(metrics['failed']), delta_color="inverse")

st.sidebar.markdown("---")
st.sidebar.markdown("### 📅 Latest Assessment")
st.sidebar.info(f"**ID:** {metrics['assessment_id']}\n\n**Time:** {metrics['timestamp']}")

st.sidebar.markdown("---")
st.sidebar.markdown("### 💼 Business Impact")
st.sidebar.markdown(f"""
**Risk Exposure:**
{metrics['failed']} security controls are currently failing, exposing the environment to potential threats.

**Compliance Status:**
{'🟢 Compliant' if metrics['score'] >= 80 else '🔴 Non-Compliant'}
""")

# Main Content Tabs
tab1, tab2, tab3, tab4 = st.tabs(["Executive Dashboard", "Compliance Trends", "Remediation Queue", "Control Explorer"])

# --- Tab 1: Executive Dashboard ---
with tab1:
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("Overall Compliance")
        
        # Gauge Chart
        fig_gauge = go.Figure(go.Indicator(
            mode = "gauge+number",
            value = metrics['score'],
            title = {'text': "Score"},
            gauge = {
                'axis': {'range': [0, 100]},
                'bar': {'color': "green" if metrics['score'] >= 80 else "orange" if metrics['score'] >= 50 else "red"},
                'steps': [
                    {'range': [0, 50], 'color': "lightgray"},
                    {'range': [50, 80], 'color': "gray"}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 80
                }
            }
        ))
        fig_gauge.update_layout(height=300, margin=dict(l=20, r=20, t=50, b=20))
        st.plotly_chart(fig_gauge, use_container_width=True)
        
        st.markdown("""
        **Goal:** Maintain >80% compliance.
        
        This score reflects the percentage of passed CIS controls across all audited AWS resources.
        """)

    with col2:
        st.subheader("Performance by Category")
        
        category_df = get_category_performance()
        
        if not category_df.empty:
            fig_bar = px.bar(
                category_df,
                x='category',
                y='compliance_pct',
                color='compliance_pct',
                color_continuous_scale=['red', 'orange', 'green'],
                range_y=[0, 100],
                text='compliance_pct',
                labels={'compliance_pct': 'Compliance %', 'category': 'Security Domain'},
                title="Compliance Percentage by Domain"
            )
            fig_bar.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
            st.plotly_chart(fig_bar, use_container_width=True)
        else:
            st.info("No category data available.")

# --- Tab 2: Compliance Trends ---
with tab2:
    st.subheader("30-Day Compliance History")
    
    trends_df = get_compliance_trends()
    
    if not trends_df.empty:
        fig_line = px.line(
            trends_df,
            x='date',
            y='score',
            markers=True,
            title='Compliance Score Trend',
            labels={'score': 'Compliance Score (%)', 'date': 'Assessment Date'}
        )
        fig_line.add_hline(y=80, line_dash="dash", line_color="green", annotation_text="Target (80%)")
        fig_line.update_yaxes(range=[0, 105])
        st.plotly_chart(fig_line, use_container_width=True)
        
        st.markdown("""
        **Trend Analysis:**
        Tracking compliance over time helps identify regression (new failures) or improvement (remediation efforts).
        """)
    else:
        st.info("Not enough historical data to show trends.")

# --- Tab 3: Remediation Queue ---
with tab3:
    st.subheader("🚨 Failed Controls - Action Required")
    
    failed_df = get_failed_controls()
    
    if not failed_df.empty:
        # Filters
        col_filter1, col_filter2 = st.columns(2)
        with col_filter1:
            severity_filter = st.multiselect(
                "Filter by Severity",
                options=failed_df['severity'].unique(),
                default=failed_df['severity'].unique()
            )
        with col_filter2:
            category_filter = st.multiselect(
                "Filter by Category",
                options=failed_df['category'].unique(),
                default=failed_df['category'].unique()
            )
            
        # Apply filters
        filtered_failed = failed_df[
            (failed_df['severity'].isin(severity_filter)) &
            (failed_df['category'].isin(category_filter))
        ]
        
        st.markdown(f"**Showing {len(filtered_failed)} failed controls**")
        
        for idx, row in filtered_failed.iterrows():
            with st.expander(f"{'🔴' if row['severity'] == 'CRITICAL' else '🟠'} {row['control_id']}: {row['title']} ({row['severity']})"):
                st.markdown(f"**Category:** {row['category']}")
                st.markdown(f"**Finding:** {row['reason']}")
                st.markdown("**Remediation:**")
                st.code(f"# AWS CLI Command to fix\naws {row['category'].lower()} update-config --control-id {row['control_id']} ...", language="bash")
                st.markdown(f"[View CIS Documentation](https://docs.aws.amazon.com/securityhub/latest/userguide/securityhub-cis-aws-foundations-benchmark.html)")
    else:
        st.success("🎉 No failed controls! Great job!")

# --- Tab 4: Control Explorer ---
with tab4:
    st.subheader("🔍 All Controls Status")
    
    all_controls = get_all_controls_status()
    
    if not all_controls.empty:
        # Search
        search_term = st.text_input("Search controls", "")
        
        if search_term:
            all_controls = all_controls[
                all_controls['title'].str.contains(search_term, case=False) |
                all_controls['control_id'].str.contains(search_term, case=False)
            ]
        
        # Styling status
        def color_status(val):
            color = 'green' if val == 'PASS' else 'red'
            return f'color: {color}; font-weight: bold'

        st.dataframe(
            all_controls.style.map(color_status, subset=['status']),
            use_container_width=True,
            column_config={
                "control_id": "ID",
                "title": "Control Name",
                "category": "Domain",
                "severity": "Severity",
                "status": "Current Status"
            }
        )
    else:
        st.info("No controls found.")

# Footer
st.markdown("---")
st.markdown("Generated by **CSPM Auditor** | Project 2 | Cybersecurity Portfolio")
