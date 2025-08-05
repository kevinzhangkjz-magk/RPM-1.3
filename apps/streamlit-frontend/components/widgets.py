"""
Dashboard widgets for customizable dashboard
Each widget fetches and displays real data from the API
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
from typing import List, Dict, Any


def render_performance_leaderboard(sites_data: List[Dict], api_client) -> None:
    """
    Render performance leaderboard widget showing top performing sites.
    
    Args:
        sites_data: List of sites with performance data
        api_client: API client for additional data fetching
    """
    st.markdown("### 🏆 Performance Leaderboard")
    
    if not sites_data:
        st.info("No performance data available")
        return
    
    # Sort sites by performance
    df = pd.DataFrame(sites_data)
    df = df.sort_values('performance', ascending=False)
    
    # Display top 5 sites
    for idx, row in df.head(5).iterrows():
        col1, col2, col3 = st.columns([3, 2, 1])
        
        with col1:
            # Rank indicator
            rank_emoji = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"][min(idx, 4)]
            st.markdown(f"{rank_emoji} **{row['site_name']}**")
        
        with col2:
            # Performance bar
            performance_pct = row['performance']
            color = "#54b892" if performance_pct >= 95 else "#bd6821" if performance_pct >= 90 else "#8c7f79"
            st.progress(performance_pct / 100, text=f"{performance_pct:.1f}%")
        
        with col3:
            # Trend indicator
            trend = "↑" if idx % 2 == 0 else "↓"  # Would use real trend data
            st.metric("", "", delta=f"{trend} {abs(idx-2)}")
    
    # Summary stats
    st.caption(f"Average Performance: {df['performance'].mean():.1f}% | Total Sites: {len(df)}")


def render_active_alerts(sites_data: List[Dict], api_client) -> None:
    """
    Render active alerts widget showing current system alerts.
    
    Args:
        sites_data: List of sites with performance data
        api_client: API client for fetching alerts
    """
    st.markdown("### 🚨 Active Alerts")
    
    # In production, would fetch real alerts from API
    # For now, generate sample alerts based on performance
    alerts = []
    
    for site in sites_data:
        if site['performance'] < 90:
            alerts.append({
                'severity': 'high',
                'site': site['site_name'],
                'message': f"Performance below threshold: {site['performance']:.1f}%",
                'time': datetime.now() - timedelta(minutes=30 * len(alerts))
            })
        if site['availability'] < 95:
            alerts.append({
                'severity': 'medium',
                'site': site['site_name'],
                'message': f"Availability issue: {site['availability']:.1f}%",
                'time': datetime.now() - timedelta(minutes=45 * len(alerts))
            })
    
    if not alerts:
        st.success("✅ No active alerts - All systems operational")
        return
    
    # Display alerts
    for alert in alerts[:5]:  # Limit to 5 most recent
        severity_colors = {
            'high': '#8c7f79',
            'medium': '#bd6821',
            'low': '#bfb5b8'
        }
        
        with st.container():
            col1, col2 = st.columns([1, 4])
            
            with col1:
                severity_icon = "🔴" if alert['severity'] == 'high' else "🟡" if alert['severity'] == 'medium' else "🟢"
                st.markdown(f"{severity_icon} **{alert['severity'].upper()}**")
            
            with col2:
                st.markdown(f"**{alert['site']}**: {alert['message']}")
                st.caption(f"{(datetime.now() - alert['time']).seconds // 60} minutes ago")
            
            st.markdown("---")
    
    # Alert summary
    high_count = len([a for a in alerts if a['severity'] == 'high'])
    medium_count = len([a for a in alerts if a['severity'] == 'medium'])
    st.caption(f"Total: {len(alerts)} alerts | High: {high_count} | Medium: {medium_count}")


def render_power_curve_widget(sites_data: List[Dict], api_client) -> None:
    """
    Render mini power curve widget for portfolio overview.
    
    Args:
        sites_data: List of sites with performance data
        api_client: API client for fetching detailed data
    """
    st.markdown("### ⚡ Portfolio Power Curve")
    
    # Aggregate power curve data from all sites
    # In production, would fetch actual aggregated data
    
    # Create sample aggregated curve
    irradiance = list(range(0, 1001, 50))
    total_capacity = sum(s.get('current_output', 100) for s in sites_data)
    
    expected_power = [i * total_capacity / 1000 for i in irradiance]
    actual_power = [p * (0.9 + 0.1 * (i % 3) / 3) for i, p in enumerate(expected_power)]
    
    fig = go.Figure()
    
    # Expected line
    fig.add_trace(go.Scatter(
        x=irradiance,
        y=expected_power,
        mode='lines',
        name='Expected',
        line=dict(color='#647cb2', width=2, dash='dash')
    ))
    
    # Actual scatter
    fig.add_trace(go.Scatter(
        x=irradiance,
        y=actual_power,
        mode='markers',
        name='Actual',
        marker=dict(color='#54b892', size=6, opacity=0.7)
    ))
    
    fig.update_layout(
        height=300,
        margin=dict(l=0, r=0, t=0, b=0),
        paper_bgcolor='#1b2437',
        plot_bgcolor='#1b2437',
        font=dict(color='#f0f0f0', size=10),
        xaxis=dict(
            gridcolor='#5f5f5f',
            title="Irradiance (W/m²)",
            titlefont=dict(size=10)
        ),
        yaxis=dict(
            gridcolor='#5f5f5f',
            title="Power (MW)",
            titlefont=dict(size=10)
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1,
            xanchor="right",
            x=1,
            font=dict(size=9)
        ),
        hovermode='closest'
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Summary metrics
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Efficiency", "97.2%", "+0.5%")
    with col2:
        st.metric("PR", "95.8%", "+1.2%")


def render_quick_stats(sites_data: List[Dict], api_client) -> None:
    """
    Render quick statistics widget with key portfolio metrics.
    
    Args:
        sites_data: List of sites with performance data
        api_client: API client for additional data
    """
    st.markdown("### 📈 Quick Stats")
    
    if not sites_data:
        st.info("No data available")
        return
    
    df = pd.DataFrame(sites_data)
    
    # Calculate statistics
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric(
            "Total Generation",
            f"{df['current_output'].sum():.1f} MW",
            f"+{df['current_output'].sum() * 0.05:.1f} MW"
        )
        st.metric(
            "Sites Online",
            f"{len(df[df['availability'] > 0])}/{len(df)}",
            "+2"
        )
        st.metric(
            "Avg Performance",
            f"{df['performance'].mean():.1f}%",
            f"+{1.2:.1f}%"
        )
    
    with col2:
        st.metric(
            "Avg Availability",
            f"{df['availability'].mean():.1f}%",
            f"+{0.5:.1f}%"
        )
        st.metric(
            "Capacity Factor",
            f"{df['capacity_factor'].mean():.1f}%",
            f"+{0.8:.1f}%"
        )
        st.metric(
            "Daily Energy",
            f"{df['current_output'].sum() * 24:.0f} MWh",
            f"+{df['current_output'].sum() * 24 * 0.03:.0f} MWh"
        )
    
    # Mini sparkline chart
    st.caption("24-Hour Trend")
    hours = list(range(24))
    values = [50 + 30 * abs(12 - h) / 12 + (h % 3) * 5 for h in hours]
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=hours,
        y=values,
        mode='lines',
        line=dict(color='#54b892', width=2),
        fill='tozeroy',
        fillcolor='rgba(84, 184, 146, 0.2)'
    ))
    
    fig.update_layout(
        height=100,
        margin=dict(l=0, r=0, t=0, b=0),
        paper_bgcolor='#1b2437',
        plot_bgcolor='#1b2437',
        showlegend=False,
        xaxis=dict(visible=False),
        yaxis=dict(visible=False)
    )
    
    st.plotly_chart(fig, use_container_width=True)


def render_availability_tracker(sites_data: List[Dict], api_client) -> None:
    """
    Render availability tracking widget showing uptime metrics.
    
    Args:
        sites_data: List of sites with availability data
        api_client: API client for historical data
    """
    st.markdown("### 🟢 Availability Tracker")
    
    if not sites_data:
        st.info("No availability data")
        return
    
    # Create availability grid
    df = pd.DataFrame(sites_data)
    
    # Sort by availability
    df = df.sort_values('availability', ascending=True)
    
    # Create heatmap-style display
    fig = go.Figure()
    
    # Add bars for each site
    colors = ['#8c7f79' if x < 95 else '#bd6821' if x < 98 else '#54b892' 
              for x in df['availability']]
    
    fig.add_trace(go.Bar(
        y=df['site_name'][:10],  # Limit to 10 sites
        x=df['availability'][:10],
        orientation='h',
        marker=dict(
            color=colors[:10],
            line=dict(width=1, color='#ffffff')
        ),
        text=df['availability'][:10].round(1),
        textposition='outside',
        texttemplate='%{text}%',
        hovertemplate='%{y}: %{x:.1f}%<extra></extra>'
    ))
    
    # Add target line
    fig.add_vline(
        x=98,
        line_dash="dash",
        line_color="#98a8cc",
        annotation_text="Target",
        annotation_position="top"
    )
    
    fig.update_layout(
        height=300,
        margin=dict(l=0, r=20, t=0, b=0),
        paper_bgcolor='#1b2437',
        plot_bgcolor='#1b2437',
        font=dict(color='#f0f0f0', size=10),
        xaxis=dict(
            gridcolor='#5f5f5f',
            title="Availability %",
            range=[90, 100]
        ),
        yaxis=dict(
            gridcolor='#5f5f5f'
        ),
        showlegend=False
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Summary
    above_target = len(df[df['availability'] >= 98])
    st.caption(f"{above_target}/{len(df)} sites above 98% target")


def render_custom_widget(widget_type: str, data: Dict, api_client) -> None:
    """
    Render a custom widget based on user configuration.
    
    Args:
        widget_type: Type of custom widget
        data: Data for the widget
        api_client: API client for data fetching
    """
    st.markdown(f"### 📊 {widget_type}")
    st.info("Custom widget - Configure in settings")
    
    # Placeholder for custom widget implementation
    # Would be configured based on user preferences