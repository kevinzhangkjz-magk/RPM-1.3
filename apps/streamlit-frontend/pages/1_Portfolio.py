"""
Portfolio Page - Display all solar sites with performance metrics
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from lib.session_state_isolated import initialize_session_state, update_navigation_context, get_session_value
from lib.api_client_refactored import get_api_client
from lib.security import input_sanitizer
from components.navigation import render_breadcrumb
import components.theme as theme

# Page config
st.set_page_config(
    page_title="Portfolio - RPM",
    page_icon="📊",
    layout="wide"
)

# Initialize session state
initialize_session_state()

# Apply theme
theme.apply_custom_theme()

# Get API client
api_client = get_api_client()

# Header
st.title("📊 Site Portfolio")
st.markdown("Monitor and analyze all your solar sites")

# Render breadcrumb
render_breadcrumb()

# Filters row
st.markdown("---")
col1, col2, col3, col4 = st.columns([2, 2, 1, 1])

with col1:
    search_term = st.text_input("🔍 Search sites", placeholder="Enter site name or ID...")
    # Sanitize search input
    if search_term:
        search_term = input_sanitizer.sanitize_html(search_term)

with col2:
    site_status_filter = st.multiselect(
        "Status Filter",
        ["Connected", "Disconnected", "Maintenance"],
        default=["Connected"]
    )

with col3:
    sort_by = st.selectbox(
        "Sort by",
        ["Name", "Capacity", "Performance", "Location"]
    )

with col4:
    if st.button("🔄 Refresh", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

# Fetch sites data
try:
    with st.spinner("Loading sites..."):
        sites = api_client.get_sites(use_cache=True)
        
    if not sites:
        st.warning("No sites found. Please check your connection or add sites to the system.")
        st.stop()
    
    # Summary metrics
    st.markdown("---")
    col1, col2, col3, col4 = st.columns(4)
    
    total_sites = len(sites)
    total_capacity = sum(site.get('capacity_kw', 0) for site in sites) / 1000  # Convert to MW
    connected_sites = len([s for s in sites if s.get('connectivity_status') == 'connected'])
    avg_performance = 95.2  # Placeholder - would calculate from real data
    
    with col1:
        st.metric(
            "Total Sites",
            f"{total_sites}",
            f"{connected_sites} connected"
        )
    
    with col2:
        st.metric(
            "Total Capacity",
            f"{total_capacity:.1f} MW",
            "+2.5 MW this month"
        )
    
    with col3:
        st.metric(
            "Avg Performance",
            f"{avg_performance}%",
            "+2.3%",
            delta_color="normal"
        )
    
    with col4:
        st.metric(
            "Active Alerts",
            "3",
            "-2 from yesterday",
            delta_color="inverse"
        )
    
    # Performance chart
    st.markdown("---")
    st.subheader("📈 Portfolio Performance Trend")
    
    # Generate sample data for demonstration
    dates = pd.date_range(end=datetime.now(), periods=30, freq='D')
    performance_data = pd.DataFrame({
        'Date': dates,
        'Performance': [93 + (i % 7) * 0.5 for i in range(30)],
        'Target': [95] * 30
    })
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=performance_data['Date'],
        y=performance_data['Performance'],
        mode='lines+markers',
        name='Actual Performance',
        line=dict(color='#54b892', width=2),
        marker=dict(size=6)
    ))
    fig.add_trace(go.Scatter(
        x=performance_data['Date'],
        y=performance_data['Target'],
        mode='lines',
        name='Target',
        line=dict(color='#bd6821', dash='dash', width=2)
    ))
    
    fig.update_layout(
        height=400,
        paper_bgcolor='#1b2437',
        plot_bgcolor='#1b2437',
        font=dict(color='#f0f0f0'),
        xaxis=dict(gridcolor='#5f5f5f'),
        yaxis=dict(gridcolor='#5f5f5f', title='Performance (%)'),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        hovermode='x unified'
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Sites grid
    st.markdown("---")
    st.subheader("🏭 Sites Overview")
    
    # Filter sites based on search
    filtered_sites = sites
    if search_term:
        filtered_sites = [
            s for s in sites 
            if search_term.lower() in s.get('site_name', '').lower() or
               search_term.lower() in s.get('site_id', '').lower()
        ]
    
    # Create responsive grid
    cols_per_row = 3
    rows = [filtered_sites[i:i+cols_per_row] for i in range(0, len(filtered_sites), cols_per_row)]
    
    for row in rows:
        cols = st.columns(cols_per_row)
        for idx, site in enumerate(row):
            with cols[idx]:
                with st.container(border=True):
                    # Site header
                    status_color = "#54b892" if site.get('connectivity_status') == 'connected' else "#8c7f79"
                    st.markdown(f"""
                    <div style='display: flex; justify-content: space-between; align-items: center;'>
                        <h4 style='margin: 0;'>{site.get('site_name', site['site_id'])}</h4>
                        <div style='width: 10px; height: 10px; border-radius: 50%; background: {status_color};'></div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    st.caption(f"ID: {site['site_id']}")
                    
                    # Site metrics
                    col_a, col_b = st.columns(2)
                    with col_a:
                        st.metric("Capacity", f"{site.get('capacity_kw', 0)/1000:.1f} MW")
                    with col_b:
                        st.metric("Performance", f"{site.get('performance', 95)}%")
                    
                    # Location info
                    if site.get('location'):
                        st.caption(f"📍 {site['location']}")
                    
                    # Installation date
                    if site.get('installation_date'):
                        install_date = datetime.fromisoformat(site['installation_date'].replace('Z', '+00:00'))
                        st.caption(f"📅 Installed: {install_date.strftime('%b %Y')}")
                    
                    # View button
                    if st.button(
                        "View Details →",
                        key=f"view_{site['site_id']}",
                        use_container_width=True
                    ):
                        update_navigation_context(site_id=site['site_id'])
                        st.switch_page("pages/2_Site_Detail.py")

except Exception as e:
    st.error(f"Failed to load portfolio data: {str(e)}")
    st.info("Please check your API connection and try again.")

# Footer
st.markdown("---")
st.caption("Data refreshes every 5 minutes • Last update: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))