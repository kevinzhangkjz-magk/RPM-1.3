"""
AI-Powered Dashboard Widgets for Renewable Energy Asset Management
Provides intelligent widgets with AI-generated insights
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import numpy as np

def render_performance_leaderboard(api_client, top_n: int = 5) -> None:
    """
    Render Performance Leaderboard widget with AI-generated insights.
    
    Args:
        api_client: API client for data fetching
        top_n: Number of top/bottom performers to show
    """
    with st.container():
        st.subheader("🏆 Performance Leaderboard")
        
        # Query AI for performance rankings
        query = f"Give me the top {top_n} best and worst performing sites with R-squared and RMSE"
        
        with st.spinner("Analyzing performance..."):
            response = api_client.query_ai_assistant(query)
        
        if response.get('data'):
            # Create two columns for best and worst
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("### ✅ Top Performers")
                render_performance_list(response['data'][:top_n], 'good')
            
            with col2:
                st.markdown("### ⚠️ Needs Attention")
                render_performance_list(response['data'][-top_n:], 'bad')
        
        # AI Insights
        if response.get('summary'):
            with st.expander("💡 AI Insights"):
                st.markdown(response['summary'])

def render_active_alerts(api_client) -> None:
    """
    Render Active Alerts widget with severity classification and recommendations.
    
    Args:
        api_client: API client for data fetching
    """
    with st.container():
        st.subheader("🚨 Active Alerts")
        
        # Query AI for critical issues
        query = "Which sites have critical performance issues requiring immediate attention?"
        
        with st.spinner("Checking alerts..."):
            response = api_client.query_ai_assistant(query)
        
        if response.get('data'):
            alerts = response['data']
            
            # Group by severity
            critical = [a for a in alerts if a.get('status') == 'CRITICAL']
            warning = [a for a in alerts if a.get('status') == 'WARNING']
            monitor = [a for a in alerts if a.get('status') == 'MONITOR']
            
            # Display alerts by severity
            if critical:
                st.error(f"🚨 **{len(critical)} Critical Alerts**")
                for alert in critical[:3]:
                    render_alert_card(alert, 'critical')
            
            if warning:
                st.warning(f"⚠️ **{len(warning)} Warnings**")
                for alert in warning[:2]:
                    render_alert_card(alert, 'warning')
            
            if monitor:
                st.info(f"📌 **{len(monitor)} Monitoring**")
                for alert in monitor[:2]:
                    render_alert_card(alert, 'monitor')
        
        # Recommendations
        if response.get('recommendations'):
            with st.expander("📋 Recommended Actions"):
                for idx, rec in enumerate(response['recommendations'], 1):
                    st.markdown(f"{idx}. {rec}")

def render_power_curve_widget(api_client, site_id: Optional[str] = None) -> None:
    """
    Render Power Curve widget with AI-powered anomaly detection.
    
    Args:
        api_client: API client for data fetching
        site_id: Optional specific site to display
    """
    with st.container():
        st.subheader("📈 Power Curve Analysis")
        
        # Site selection
        if not site_id:
            sites = api_client.get_sites()
            site_names = [s['site_name'] for s in sites]
            selected_site = st.selectbox("Select Site", site_names, key="pc_site")
            site_id = next(s['site_id'] for s in sites if s['site_name'] == selected_site)
        
        # Date range
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("Start Date", datetime.now() - timedelta(days=30))
        with col2:
            end_date = st.date_input("End Date", datetime.now())
        
        # Fetch performance data
        performance = api_client.get_site_performance(
            site_id,
            start_date.isoformat(),
            end_date.isoformat()
        )
        
        if performance.get('data_points'):
            df = pd.DataFrame(performance['data_points'])
            
            # Create power curve plot
            fig = go.Figure()
            
            # Actual vs Expected
            fig.add_trace(go.Scatter(
                x=df.get('poa_irradiance', df.index),
                y=df.get('actual_power', []),
                mode='markers',
                name='Actual',
                marker=dict(color='#54b892', size=5)
            ))
            
            fig.add_trace(go.Scatter(
                x=df.get('poa_irradiance', df.index),
                y=df.get('expected_power', []),
                mode='markers',
                name='Expected',
                marker=dict(color='#647cb2', size=5)
            ))
            
            # Query AI for anomalies
            query = f"Identify anomalies in the power curve for site {site_id}"
            anomaly_response = api_client.query_ai_assistant(query)
            
            # Add anomaly highlights if detected
            if anomaly_response.get('data'):
                anomalies = anomaly_response['data']
                # Add anomaly markers
                # Implementation depends on anomaly data structure
            
            fig.update_layout(
                title=f"Power Curve - {site_id}",
                xaxis_title="POA Irradiance (W/m²)",
                yaxis_title="Power (MW)",
                height=400,
                template="plotly_dark"
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # AI Analysis
            if anomaly_response.get('summary'):
                with st.expander("🔍 AI Analysis"):
                    st.markdown(anomaly_response['summary'])

def render_kpi_summary(api_client) -> None:
    """
    Render Key Performance Indicators summary widget.
    
    Args:
        api_client: API client for data fetching
    """
    with st.container():
        st.subheader("📊 Key Performance Indicators")
        
        # Query AI for KPI summary
        query = "Provide portfolio KPI summary: average R-squared, RMSE, capacity factor, and financial metrics"
        
        with st.spinner("Calculating KPIs..."):
            response = api_client.query_ai_assistant(query)
        
        if response.get('metrics'):
            metrics = response['metrics']
            
            # Display KPIs in columns
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric(
                    "Avg R²",
                    f"{metrics.get('avg_r_squared', 0):.3f}",
                    delta=f"{metrics.get('r_squared_change', 0):.3f}"
                )
            
            with col2:
                st.metric(
                    "Avg RMSE",
                    f"{metrics.get('avg_rmse', 0):.2f} MW",
                    delta=f"{metrics.get('rmse_change', 0):.2f} MW"
                )
            
            with col3:
                st.metric(
                    "Revenue at Risk",
                    f"${metrics.get('total_revenue_impact', 0):,.0f}",
                    delta=f"${metrics.get('revenue_change', 0):,.0f}"
                )
            
            with col4:
                st.metric(
                    "Sites Below Target",
                    f"{metrics.get('sites_below_target', 0)}",
                    delta=f"{metrics.get('sites_change', 0):+d}"
                )
        
        # Trend chart
        if response.get('data'):
            df = pd.DataFrame(response['data'])
            if not df.empty:
                fig = px.line(
                    df,
                    x='date' if 'date' in df.columns else df.index,
                    y='value' if 'value' in df.columns else df.columns[0],
                    title="Performance Trend",
                    template="plotly_dark"
                )
                st.plotly_chart(fig, use_container_width=True)

def render_site_comparison(api_client, site_ids: List[str] = None) -> None:
    """
    Render Site Comparison widget for multi-site analysis.
    
    Args:
        api_client: API client for data fetching
        site_ids: List of site IDs to compare
    """
    with st.container():
        st.subheader("🔄 Site Comparison")
        
        # Site selection
        sites = api_client.get_sites()
        site_names = [s['site_name'] for s in sites]
        
        selected_sites = st.multiselect(
            "Select Sites to Compare",
            site_names,
            default=site_names[:3] if len(site_names) >= 3 else site_names,
            key="compare_sites"
        )
        
        if selected_sites:
            # Query AI for comparison
            query = f"Compare performance metrics for sites: {', '.join(selected_sites)}"
            
            with st.spinner("Comparing sites..."):
                response = api_client.query_ai_assistant(query)
            
            if response.get('data'):
                df = pd.DataFrame(response['data'])
                
                # Create comparison chart
                fig = go.Figure()
                
                # Add bars for each metric
                metrics = ['r_squared', 'rmse', 'capacity_factor']
                for metric in metrics:
                    if metric in df.columns:
                        fig.add_trace(go.Bar(
                            x=df.get('site_name', df.index),
                            y=df[metric],
                            name=metric.replace('_', ' ').title()
                        ))
                
                fig.update_layout(
                    title="Site Performance Comparison",
                    barmode='group',
                    height=400,
                    template="plotly_dark"
                )
                
                st.plotly_chart(fig, use_container_width=True)
            
            # AI Insights
            if response.get('summary'):
                with st.expander("💡 Comparison Insights"):
                    st.markdown(response['summary'])

def render_predictive_maintenance(api_client) -> None:
    """
    Render Predictive Maintenance widget with AI-driven recommendations.
    
    Args:
        api_client: API client for data fetching
    """
    with st.container():
        st.subheader("🛠️ Predictive Maintenance")
        
        # Query AI for maintenance predictions
        query = "Predict maintenance needs based on performance degradation patterns"
        
        with st.spinner("Analyzing maintenance needs..."):
            response = api_client.query_ai_assistant(query)
        
        if response.get('data'):
            maintenance_items = response['data']
            
            # Group by urgency
            urgent = [m for m in maintenance_items if m.get('urgency') == 'urgent']
            scheduled = [m for m in maintenance_items if m.get('urgency') == 'scheduled']
            preventive = [m for m in maintenance_items if m.get('urgency') == 'preventive']
            
            # Display maintenance schedule
            tab1, tab2, tab3 = st.tabs(["🚨 Urgent", "📅 Scheduled", "🔧 Preventive"])
            
            with tab1:
                if urgent:
                    for item in urgent:
                        render_maintenance_card(item, 'urgent')
                else:
                    st.success("No urgent maintenance required")
            
            with tab2:
                if scheduled:
                    for item in scheduled:
                        render_maintenance_card(item, 'scheduled')
                else:
                    st.info("No scheduled maintenance")
            
            with tab3:
                if preventive:
                    for item in preventive:
                        render_maintenance_card(item, 'preventive')
                else:
                    st.info("No preventive maintenance suggested")
        
        # ROI Analysis
        if response.get('metrics') and response['metrics'].get('maintenance_roi'):
            st.metric(
                "Estimated ROI",
                f"{response['metrics']['maintenance_roi']:.1%}",
                help="Return on investment for recommended maintenance"
            )

# Helper functions
def render_performance_list(sites: List[Dict], performance_type: str) -> None:
    """Render a list of sites with performance metrics."""
    for site in sites:
        if performance_type == 'good':
            icon = "✅"
            color = "green"
        else:
            icon = "⚠️"
            color = "orange"
        
        with st.container():
            st.markdown(
                f"{icon} **{site.get('site_name', 'Unknown')}**  \n"
                f"R²: {site.get('r_squared', 0):.3f} | "
                f"RMSE: {site.get('rmse', 0):.2f} MW"
            )

def render_alert_card(alert: Dict, severity: str) -> None:
    """Render an alert card with appropriate styling."""
    colors = {
        'critical': '#ff4444',
        'warning': '#ffaa00',
        'monitor': '#4444ff'
    }
    
    st.markdown(
        f"""
        <div style="padding: 10px; border-left: 4px solid {colors.get(severity, '#888')}; margin: 5px 0;">
            <strong>{alert.get('site_name', 'Unknown Site')}</strong><br>
            {alert.get('message', 'No details available')}<br>
            <small>Impact: ${alert.get('revenue_impact', 0):,.0f}/month</small>
        </div>
        """,
        unsafe_allow_html=True
    )

def render_maintenance_card(item: Dict, urgency: str) -> None:
    """Render a maintenance card."""
    st.markdown(
        f"""
        **{item.get('site_name', 'Unknown')}** - {item.get('component', 'Unknown')}  
        {item.get('description', 'Maintenance required')}  
        Estimated Cost: ${item.get('cost', 0):,.0f}  
        Expected Benefit: ${item.get('benefit', 0):,.0f}/month
        """
    )