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
    .big-metric {
        font-size: 2rem;
        font-weight: bold;
        color: #1f77b4;
    }
    .metric-label {
        font-size: 0.9rem;
        color: #666;
    }
    .risk-critical { color: #d62728; }
    .risk-high { color: #ff7f0e; }
    .risk-medium { color: #ffbb00; }
    .risk-low { color: #2ca02c; }
</style>
""", unsafe_allow_html=True)

# Database path
DB_PATH = str(project_root / 'data' / 'processed' / 'grc_analytics.db')


def load_data():
    """Load all analytics data."""
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


def show_executive_summary(data):
    """Display executive summary dashboard."""
    st.title("🛡️ GRC Analytics Platform")
    st.markdown("### Executive Dashboard")
    
    # Key metrics row
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        compliance_pct = data['velocity']['current_compliance']
        st.metric(
            "Current Compliance",
            f"{compliance_pct:.1f}%",
            f"{data['velocity']['velocity_per_month']:.2f}% per month"
        )
    
    with col2:
        st.metric(
            "High-Risk Controls",
            data['risk_summary']['high_risk_controls'] + data['risk_summary']['critical_risk_controls'],
            "Requiring attention"
        )
    
    with col3:
        remediation_pct = data['remediation']['completion_rate']
        st.metric(
            "Remediation Progress",
            f"{remediation_pct:.1f}%",
            f"{data['remediation']['in_progress']} in progress"
        )
    
    with col4:
        roi_pct = data['roi_report']['high_priority_investment']['portfolio_roi_percentage']
        st.metric(
            "High-Priority ROI",
            f"{roi_pct:.0f}%",
            "3-year projection"
        )
    
    st.markdown("---")
    
    # Compliance trend chart
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("#### Compliance Trend (6 Months)")
        
        df_trend = pd.DataFrame(data['compliance_trend'])
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df_trend['month'],
            y=df_trend['compliance_percentage'],
            mode='lines+markers',
            name='Compliance %',
            line=dict(color='#1f77b4', width=3),
            marker=dict(size=8)
        ))
        
        fig.update_layout(
            xaxis_title="Month",
            yaxis_title="Compliance %",
            yaxis_range=[0, 100],
            height=300,
            margin=dict(l=0, r=0, t=0, b=0)
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("#### Risk Distribution")
        
        risk_data = {
            'Critical': data['risk_summary']['critical_risk_controls'],
            'High': data['risk_summary']['high_risk_controls'],
            'Medium': data['risk_summary']['medium_risk_controls'],
            'Low': data['risk_summary']['low_risk_controls']
        }
        
        fig = go.Figure(data=[go.Pie(
            labels=list(risk_data.keys()),
            values=list(risk_data.values()),
            hole=.3,
            marker_colors=['#d62728', '#ff7f0e', '#ffbb00', '#2ca02c']
        )])
        
        fig.update_layout(
            height=300,
            margin=dict(l=0, r=0, t=0, b=0),
            showlegend=True
        )
        
        st.plotly_chart(fig, use_container_width=True)


def show_risk_analysis(data):
    """Display risk analysis dashboard."""
    st.title("⚠️ Risk Analysis")
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Average Priority Score",
            f"{data['risk_summary']['average_priority_score']:.2f}",
            "Out of 100"
        )
    
    with col2:
        st.metric(
            "Critical Risk Controls",
            data['risk_summary']['critical_risk_controls'],
            "Priority Score > 75"
        )
    
    with col3:
        st.metric(
            "High Risk Controls",
            data['risk_summary']['high_risk_controls'],
            "Priority Score 50-75"
        )
    
    with col4:
        st.metric(
            "Total Controls Assessed",
            data['risk_summary']['total_controls']
        )
    
    st.markdown("---")
    
    # Filters
    st.markdown("### 🔍 Filter Controls")
    col1, col2, col3 = st.columns(3)
    
    df_high_risk = pd.DataFrame(data['high_risk_controls'])
    
    if not df_high_risk.empty:
        with col1:
            risk_filter = st.selectbox(
                "Risk Level",
                ["All", "Critical (≥75)", "High (50-75)"]
            )
        
        with col2:
            status_filter = st.selectbox(
                "Compliance Status",
                ["All"] + sorted(df_high_risk['compliance_status'].unique().tolist())
            )
        
        with col3:
            family_filter = st.selectbox(
                "Control Family",
                ["All"] + sorted(df_high_risk['family'].unique().tolist())
            )
        
        # Apply filters
        filtered_df = df_high_risk.copy()
        
        if risk_filter == "Critical (≥75)":
            filtered_df = filtered_df[filtered_df['priority_score'] >= 75]
        elif risk_filter == "High (50-75)":
            filtered_df = filtered_df[(filtered_df['priority_score'] >= 50) & (filtered_df['priority_score'] < 75)]
        
        if status_filter != "All":
            filtered_df = filtered_df[filtered_df['compliance_status'] == status_filter]
        
        if family_filter != "All":
            filtered_df = filtered_df[filtered_df['family'] == family_filter]
        
        st.markdown(f"### High-Risk Controls ({len(filtered_df)} controls)")
        
        # Format the dataframe
        display_df = filtered_df[[
            'control_id', 'control_name', 'family', 'priority_score',
            'kev_cve_count', 'attack_technique_count', 'compliance_status'
        ]].copy()
        
        display_df.columns = [
            'Control ID', 'Control Name', 'Family', 'Priority Score',
            'KEV CVEs', 'ATT&CK Techniques', 'Status'
        ]
        
        # Style the dataframe
        def highlight_priority(val):
            if val >= 75:
                return 'background-color: #ffcccc'
            elif val >= 50:
                return 'background-color: #ffe6cc'
            return ''
        
        styled_df = display_df.style.applymap(
            highlight_priority,
            subset=['Priority Score']
        ).format({
            'Priority Score': '{:.2f}'
        })
        
        st.dataframe(styled_df, use_container_width=True, height=400)
        
        # Drill-down: Detailed view
        st.markdown("---")
        st.markdown("### 📋 Control Details (Click to Expand)")
        
        for idx, row in filtered_df.head(5).iterrows():
            with st.expander(f"**{row['control_id']}** - {row['control_name'][:60]}..."):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown(f"**Family:** {row['family']}")
                    st.markdown(f"**Priority Score:** {row['priority_score']:.2f}")
                    st.markdown(f"**Compliance Status:** {row['compliance_status']}")
                
                with col2:
                    st.markdown(f"**KEV CVEs:** {row['kev_cve_count']}")
                    st.markdown(f"**ATT&CK Techniques:** {row['attack_technique_count']}")
                    st.markdown(f"**Risk Category:** {'Critical' if row['priority_score'] >= 75 else 'High'}")
                
                if row['kev_cve_count'] > 0:
                    st.info(f"⚠️ This control protects against **{row['kev_cve_count']} known exploited vulnerabilities** (CISA KEV)")
                
                if row['attack_technique_count'] > 0:
                    st.info(f"🎯 Mitigates **{row['attack_technique_count']} MITRE ATT&CK techniques**")
        
        # Risk distribution by family
        st.markdown("---")
        st.markdown("### Risk Distribution by Control Family")
        
        family_risk = filtered_df.groupby('family').agg({
            'priority_score': 'mean',
            'control_id': 'count'
        }).reset_index()
        family_risk.columns = ['Family', 'Avg Priority', 'Control Count']
        family_risk = family_risk.sort_values('Avg Priority', ascending=False)
        
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=family_risk['Family'],
            y=family_risk['Avg Priority'],
            marker_color=family_risk['Avg Priority'].apply(
                lambda x: '#d62728' if x >= 75 else '#ff7f0e' if x >= 50 else '#ffbb00'
            ),
            text=family_risk['Avg Priority'].round(1),
            textposition='outside',
            hovertemplate='<b>%{x}</b><br>Avg Priority: %{y:.1f}<br>Controls: ' + 
                         family_risk['Control Count'].astype(str) + '<extra></extra>'
        ))
        
        fig.update_layout(
            xaxis_title="Control Family",
            yaxis_title="Average Priority Score",
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No high-risk controls identified.")


def show_compliance_trends(data):
    """Display compliance trends dashboard."""
    st.title("📈 Compliance Trends")
    
    # Velocity metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Current Compliance",
            f"{data['velocity']['current_compliance']:.1f}%"
        )
    
    with col2:
        velocity = data['velocity']['velocity_per_month']
        st.metric(
            "Velocity",
            f"{velocity:.2f}% per month",
            data['velocity']['trend'].capitalize()
        )
    
    with col3:
        projected = data['velocity']['projected_3_months']
        st.metric(
            "3-Month Projection",
            f"{projected:.1f}%"
        )
    
    with col4:
        if data['velocity']['months_to_95_percent']:
            st.metric(
                "Months to 95%",
                f"{data['velocity']['months_to_95_percent']:.1f}"
            )
        else:
            st.metric("Months to 95%", "N/A")
    
    st.markdown("---")
    
    # Compliance trend chart (detailed)
    st.markdown("### Historical Compliance Trend")
    
    df_trend = pd.DataFrame(data['compliance_trend'])
    
    fig = go.Figure()
    
    # Compliant
    fig.add_trace(go.Bar(
        x=df_trend['month'],
        y=df_trend['compliant'],
        name='Compliant',
        marker_color='#2ca02c'
    ))
    
    # Partial
    fig.add_trace(go.Bar(
        x=df_trend['month'],
        y=df_trend['partial'],
        name='Partial',
        marker_color='#ffbb00'
    ))
    
    # Non-compliant
    fig.add_trace(go.Bar(
        x=df_trend['month'],
        y=df_trend['non_compliant'],
        name='Non-Compliant',
        marker_color='#d62728'
    ))
    
    fig.update_layout(
        barmode='stack',
        xaxis_title="Month",
        yaxis_title="Number of Controls",
        height=400
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Family trends with drill-down
    st.markdown("### Compliance by Control Family")
    
    df_families = pd.DataFrame(data['family_trends'])
    
    if not df_families.empty:
        # Add velocity indicators
        df_families['trend_indicator'] = df_families['velocity'].apply(
            lambda x: '📈' if x > 0 else '📉' if x < 0 else '➡️'
        )
        
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            x=df_families['family'],
            y=df_families['current_compliance'],
            marker_color=df_families['current_compliance'].apply(
                lambda x: '#2ca02c' if x >= 80 else '#ffbb00' if x >= 60 else '#d62728'
            ),
            text=df_families['current_compliance'].round(1).astype(str) + '%',
            textposition='outside',
            hovertemplate='<b>%{x}</b><br>Compliance: %{y:.1f}%<br>Velocity: ' +
                         df_families['velocity'].round(2).astype(str) + '%/month<extra></extra>'
        ))
        
        fig.update_layout(
            xaxis_title="Control Family",
            yaxis_title="Compliance %",
            yaxis_range=[0, 110],
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Family details table
        st.markdown("#### Family Trends Details")
        
        display_families = df_families[[
            'family', 'current_compliance', 'velocity', 'total_controls'
        ]].copy()
        display_families.columns = ['Family', 'Current %', 'Velocity (%/month)', 'Total Controls']
        
        # Sort by velocity (worst first)
        display_families = display_families.sort_values('Velocity (%/month)')
        
        styled_families = display_families.style.format({
            'Current %': '{:.1f}%',
            'Velocity (%/month)': '{:.2f}%'
        }).applymap(
            lambda x: 'background-color: #ffcccc' if x < -2 else 'background-color: #ffe6cc' if x < 0 else 'background-color: #ccffcc' if x > 0 else '',
            subset=['Velocity (%/month)']
        )
        
        st.dataframe(styled_families, use_container_width=True)
        
        # Highlight worst performers
        worst_families = df_families.nsmallest(3, 'velocity')
        if not worst_families.empty:
            st.warning("⚠️ **Families Declining Most Rapidly:**")
            for _, fam in worst_families.iterrows():
                st.markdown(f"- **{fam['family']}**: {fam['current_compliance']:.1f}% (velocity: {fam['velocity']:.2f}%/month)")
        
        # Highlight best performers
        best_families = df_families.nlargest(3, 'velocity')
        if not best_families.empty and best_families.iloc[0]['velocity'] > 0:
            st.success("✅ **Families Improving:**")
            for _, fam in best_families.iterrows():
                if fam['velocity'] > 0:
                    st.markdown(f"- **{fam['family']}**: {fam['current_compliance']:.1f}% (velocity: {fam['velocity']:.2f}%/month)")
    
    # Remediation tracking
    st.markdown("### Remediation Tracking")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        remediation_data = {
            'Completed': data['remediation']['completed'],
            'In Progress': data['remediation']['in_progress'],
            'Open': data['remediation']['open'],
            'Overdue': data['remediation']['overdue']
        }
        
        fig = go.Figure(data=[go.Pie(
            labels=list(remediation_data.keys()),
            values=list(remediation_data.values()),
            marker_colors=['#2ca02c', '#1f77b4', '#ff7f0e', '#d62728']
        )])
        
        fig.update_layout(height=300, margin=dict(l=0, r=0, t=30, b=0))
        fig.update_traces(textposition='inside', textinfo='percent+label')
        
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("#### Remediation Metrics")
        st.metric("Total Actions", data['remediation']['total_actions'])
        st.metric("Completion Rate", f"{data['remediation']['completion_rate']:.1f}%")
        if data['remediation']['average_days_to_complete']:
            st.metric("Avg Days to Complete", f"{data['remediation']['average_days_to_complete']:.0f}")


def show_roi_analysis(data):
    """Display ROI analysis dashboard."""
    st.title("💰 ROI Analysis")
    
    roi_data = data['roi_report']['high_priority_investment']
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Portfolio ROI",
            f"{roi_data['portfolio_roi_percentage']:.0f}%",
            "3-year projection"
        )
    
    with col2:
        st.metric(
            "Total Investment",
            f"${roi_data['total_remediation_cost']:,.0f}"
        )
    
    with col3:
        st.metric(
            "Risk Reduction Value",
            f"${roi_data['total_risk_reduction']:,.0f}",
            "Over 3 years"
        )
    
    with col4:
        st.metric(
            "Net Present Value",
            f"${roi_data['total_net_present_value']:,.0f}"
        )
    
    st.markdown("---")
    
    # Top ROI controls
    st.markdown("### Top 10 Controls by ROI")
    
    top_controls = roi_data['top_roi_controls'][:10]
    df_roi = pd.DataFrame(top_controls)
    
    if not df_roi.empty:
        display_df = df_roi[[
            'control_id', 'control_name', 'remediation_cost',
            'risk_reduction_total', 'roi_percentage', 'payback_period_months'
        ]].copy()
        
        display_df.columns = [
            'Control ID', 'Control Name', 'Cost',
            'Risk Reduction', 'ROI %', 'Payback (Months)'
        ]
        
        styled_df = display_df.style.format({
            'Cost': '${:,.0f}',
            'Risk Reduction': '${:,.0f}',
            'ROI %': '{:.1f}%',
            'Payback (Months)': '{:.1f}'
        })
        
        st.dataframe(styled_df, use_container_width=True)
        
        # ROI visualization
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            x=df_roi['control_id'][:10],
            y=df_roi['roi_percentage'][:10],
            marker_color=df_roi['roi_percentage'][:10].apply(
                lambda x: '#2ca02c' if x > 100 else '#ff7f0e' if x > 0 else '#d62728'
            ),
            text=df_roi['roi_percentage'][:10].round(0),
            textposition='outside'
        ))
        
        fig.update_layout(
            xaxis_title="Control ID",
            yaxis_title="ROI %",
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # Recommendation
    st.markdown("### Investment Recommendation")
    recommendation = data['roi_report']['recommendation']
    
    st.info(f"**Priority:** {recommendation['priority'].replace('_', ' ').title()}")
    st.write(recommendation['rationale'])
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("High-Priority Efficiency", f"{recommendation['high_priority_efficiency']:.2f}")
    with col2:
        st.metric("Full Portfolio Efficiency", f"{recommendation['full_portfolio_efficiency']:.2f}")


def main():
    """Main dashboard application."""
    
    # Sidebar
    st.sidebar.title("Navigation")
    page = st.sidebar.radio(
        "Select View",
        ["Executive Summary", "Risk Analysis", "Compliance Trends", "ROI Analysis"]
    )
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("### About")
    st.sidebar.info(
        "GRC Analytics Platform\n\n"
        "Real-time compliance monitoring and risk analysis with integrated "
        "threat intelligence from CISA KEV and MITRE ATT&CK."
    )
    
    # Load data
    data = load_data()
    
    # Show selected page
    if page == "Executive Summary":
        show_executive_summary(data)
    elif page == "Risk Analysis":
        show_risk_analysis(data)
    elif page == "Compliance Trends":
        show_compliance_trends(data)
    elif page == "ROI Analysis":
        show_roi_analysis(data)
    
    # Footer
    st.sidebar.markdown("---")
    st.sidebar.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")


if __name__ == '__main__':
    main()
