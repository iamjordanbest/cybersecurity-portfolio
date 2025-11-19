#!/usr/bin/env python3
"""
GRC Analytics Dashboard

Streamlit dashboard for GRC compliance analytics platform.
"""

import streamlit as st
import sys
from pathlib import Path
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime

# Add src to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / 'src'))

from analytics.risk_scoring import RiskScoringEngine
from analytics.trend_analysis import TrendAnalyzer
from analytics.roi_calculator import ROICalculator

# Constants
DB_PATH = str(project_root / 'data' / 'processed' / 'grc_analytics.db')
RISK_COLORS = {'Critical': '#d62728', 'High': '#ff7f0e', 'Medium': '#ffbb00', 'Low': '#2ca02c'}
COMPLIANCE_COLORS = {'Compliant': '#2ca02c', 'Partial': '#ffbb00', 'Non-Compliant': '#d62728'}

# Page config
st.set_page_config(
    page_title="GRC Analytics Platform",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .big-metric { font-size: 2rem; font-weight: bold; color: #1f77b4; }
    .metric-label { font-size: 0.9rem; color: #666; }
</style>
""", unsafe_allow_html=True)

@st.cache_data(ttl=300)
def load_data():
    """Load all analytics data with caching."""
    try:
        with st.spinner('Loading analytics data...'):
            # Risk scoring
            with RiskScoringEngine(DB_PATH) as engine:
                risk_summary = engine.get_risk_score_summary()
                high_risk_controls = engine.get_high_risk_controls(threshold=50, limit=20)
            
            # Trend analysis
            with TrendAnalyzer(DB_PATH) as analyzer:
                compliance_trend = analyzer.get_compliance_over_time(months_back=6)
                velocity = analyzer.calculate_compliance_velocity()
                family_trends = analyzer.get_family_trends()
                aging = analyzer.get_control_aging_analysis()
                remediation = analyzer.get_remediation_velocity()
            
            # ROI analysis
            with ROICalculator(DB_PATH) as calculator:
                roi_report = calculator.generate_roi_report()
        
        return {
            'risk_summary': risk_summary,
            'high_risk_controls': high_risk_controls,
            'compliance_trend': compliance_trend,
            'velocity': velocity,
            'family_trends': family_trends,
            'aging': aging,
            'remediation': remediation,
            'roi_report': roi_report
        }
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return None

def show_executive_summary(data):
    """Display executive summary dashboard."""
    st.title("🛡️ GRC Analytics Platform")
    st.markdown("### Executive Dashboard")
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Current Compliance", f"{data['velocity']['current_compliance']:.1f}%", f"{data['velocity']['velocity_per_month']:.2f}% per month")
    col2.metric("High-Risk Controls", data['risk_summary']['high_risk_controls'] + data['risk_summary']['critical_risk_controls'], "Requiring attention")
    col3.metric("Remediation Progress", f"{data['remediation']['completion_rate']:.1f}%", f"{data['remediation']['in_progress']} in progress")
    col4.metric("High-Priority ROI", f"{data['roi_report']['high_priority_investment']['portfolio_roi_percentage']:.0f}%", "3-year projection")
    
    st.markdown("---")
    
    # Charts
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("#### Compliance Trend (6 Months)")
        df_trend = pd.DataFrame(data['compliance_trend'])
        fig = go.Figure(go.Scatter(x=df_trend['month'], y=df_trend['compliance_percentage'], mode='lines+markers', name='Compliance %', line=dict(color='#1f77b4', width=3)))
        fig.update_layout(xaxis_title="Month", yaxis_title="Compliance %", yaxis_range=[0, 100], height=300, margin=dict(l=0, r=0, t=0, b=0))
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("#### Risk Distribution")
        risk_data = {k: data['risk_summary'][f'{k.lower()}_risk_controls'] for k in RISK_COLORS.keys()}
        fig = go.Figure(data=[go.Pie(labels=list(risk_data.keys()), values=list(risk_data.values()), hole=.3, marker_colors=list(RISK_COLORS.values()))])
        fig.update_layout(height=300, margin=dict(l=0, r=0, t=0, b=0), showlegend=True)
        st.plotly_chart(fig, use_container_width=True)

def show_risk_analysis(data):
    """Display risk analysis dashboard."""
    st.title("⚠️ Risk Analysis")
    
    # Metrics
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Avg Priority Score", f"{data['risk_summary']['average_priority_score']:.2f}")
    col2.metric("Critical Risk Controls", data['risk_summary']['critical_risk_controls'])
    col3.metric("High Risk Controls", data['risk_summary']['high_risk_controls'])
    col4.metric("Total Controls", data['risk_summary']['total_controls'])
    
    st.markdown("---")
    
    # High Risk Controls Table
    df_high_risk = pd.DataFrame(data['high_risk_controls'])
    if not df_high_risk.empty:
        st.markdown(f"### High-Risk Controls ({len(df_high_risk)})")
        display_df = df_high_risk[['control_id', 'control_name', 'control_family', 'priority_score', 'kev_cve_count', 'attack_technique_count', 'compliance_status']].copy()
        display_df.columns = ['ID', 'Name', 'Family', 'Score', 'KEV', 'ATT&CK', 'Status']
        
        st.dataframe(display_df.style.background_gradient(subset=['Score'], cmap='Reds'), use_container_width=True)
        
        # Risk by Family Chart
        st.markdown("### Risk by Family")
        family_risk = df_high_risk.groupby('control_family')['priority_score'].mean().reset_index()
        fig = px.bar(family_risk, x='control_family', y='priority_score', color='priority_score', color_continuous_scale='Reds', title="Average Risk Score by Family")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No high-risk controls identified.")

def show_compliance_trends(data):
    """Display compliance trends dashboard."""
    st.title("📈 Compliance Trends")
    
    # Metrics
    col1, col2, col3 = st.columns(3)
    col1.metric("Current Compliance", f"{data['velocity']['current_compliance']:.1f}%")
    col2.metric("Velocity", f"{data['velocity']['velocity_per_month']:.2f}%/mo", data['velocity']['trend'])
    col3.metric("3-Month Projection", f"{data['velocity']['projected_3_months']:.1f}%")
    
    st.markdown("---")
    
    # Detailed Trend Chart
    st.markdown("### Historical Compliance Trend")
    df_trend = pd.DataFrame(data['compliance_trend'])
    fig = go.Figure()
    for status, color in COMPLIANCE_COLORS.items():
        key = status.lower().replace('-', '_')
        if key in df_trend.columns:
             fig.add_trace(go.Bar(x=df_trend['month'], y=df_trend[key], name=status, marker_color=color))
    
    fig.update_layout(barmode='stack', xaxis_title="Month", yaxis_title="Controls", height=400)
    st.plotly_chart(fig, use_container_width=True)

def show_roi_analysis(data):
    """Display ROI analysis dashboard."""
    st.title("💰 ROI Analysis")
    roi_data = data['roi_report']['high_priority_investment']
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Portfolio ROI", f"{roi_data['portfolio_roi_percentage']:.0f}%")
    col2.metric("Total Investment", f"${roi_data['total_remediation_cost']:,.0f}")
    col3.metric("Net Present Value", f"${roi_data['total_net_present_value']:,.0f}")
    
    st.markdown("---")
    
    # Top ROI Controls
    st.markdown("### Top Controls by ROI")
    df_roi = pd.DataFrame(roi_data['top_roi_controls'][:10])
    if not df_roi.empty:
        fig = px.bar(df_roi, x='control_id', y='roi_percentage', color='roi_percentage', title="Top 10 Controls by ROI %")
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(df_roi[['control_id', 'control_name', 'remediation_cost', 'roi_percentage', 'payback_period_months']], use_container_width=True)

def main():
    st.sidebar.title("Navigation")
    page = st.sidebar.radio("Select View", ["Executive Summary", "Risk Analysis", "Compliance Trends", "ROI Analysis"])
    
    st.sidebar.info("GRC Analytics Platform\n\nReal-time compliance monitoring and risk analysis.")
    
    data = load_data()
    if data:
        if page == "Executive Summary": show_executive_summary(data)
        elif page == "Risk Analysis": show_risk_analysis(data)
        elif page == "Compliance Trends": show_compliance_trends(data)
        elif page == "ROI Analysis": show_roi_analysis(data)
    
    st.sidebar.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")

if __name__ == '__main__':
    main()

