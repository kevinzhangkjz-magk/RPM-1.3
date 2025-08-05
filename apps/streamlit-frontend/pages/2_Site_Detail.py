"""
Site Detail Page - Detailed performance metrics and drill-down for individual sites
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import numpy as np
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from lib.session_state import initialize_session_state, update_navigation_context
from lib.api_client import get_api_client
from components.navigation import (
    render_breadcrumb, 
    render_date_range_selector,
    render_availability_filter,
    render_skid_selector,
    render_inverter_selector
)
from components.charts import (
    render_power_curve, 
    render_performance_scatter,
    render_time_series,
    render_performance_heatmap
)
import components.theme as theme

# Page config
st.set_page_config(
    page_title="Site Detail - RPM",
    page_icon="🏭",
    layout="wide"
)

# Initialize session state
initialize_session_state()

# Apply theme
theme.apply_custom_theme()

# Get API client
api_client = get_api_client()

# Check if site is selected
if not st.session_state.get('selected_site'):
    st.warning("No site selected. Please select a site from the portfolio.")
    if st.button("← Go to Portfolio"):
        st.switch_page("pages/1_Portfolio.py")
    st.stop()

site_id = st.session_state.selected_site

# Header
st.title(f"🏭 Site Detail: {site_id}")
render_breadcrumb()

# Main content
try:
    # Fetch site data
    with st.spinner("Loading site data..."):
        site_detail = api_client.get_site_detail(site_id)
        site_performance = api_client.get_site_performance(site_id)
        skids = api_client.get_site_skids(site_id)
    
    # Control panel
    st.markdown("---")
    col1, col2, col3, col4 = st.columns([2, 2, 1, 1])
    
    with col1:
        start_date, end_date = render_date_range_selector()
    
    with col2:
        availability_filter = render_availability_filter()
    
    with col3:
        selected_skid = render_skid_selector(skids)
    
    with col4:
        if st.button("🔄 Refresh", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
    
    # If skid is selected, show inverter selector
    if selected_skid:
        update_navigation_context(site_id=site_id, skid_id=selected_skid)
        inverters = api_client.get_site_inverters(site_id, selected_skid)
        selected_inverter = render_inverter_selector(inverters)
        
        if selected_inverter:
            update_navigation_context(site_id=site_id, skid_id=selected_skid, inverter_id=selected_inverter)
    
    # Site metrics
    st.markdown("---")
    st.subheader("📊 Site Performance Metrics")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric(
            "Capacity",
            f"{site_detail.get('capacity_kw', 0)/1000:.1f} MW",
            help="Total installed capacity"
        )
    
    with col2:
        st.metric(
            "Current Output",
            f"{site_performance.get('current_output', 0)/1000:.1f} MW",
            f"{site_performance.get('output_change', '+2.3')}%"
        )
    
    with col3:
        st.metric(
            "Performance Ratio",
            f"{site_performance.get('performance_ratio', 95.2)}%",
            f"{site_performance.get('pr_change', '+1.2')}%"
        )
    
    with col4:
        st.metric(
            "Availability",
            f"{site_performance.get('availability', 98.5)}%",
            f"{site_performance.get('avail_change', '0')}%"
        )
    
    with col5:
        st.metric(
            "Capacity Factor",
            f"{site_performance.get('capacity_factor', 22.3)}%",
            f"{site_performance.get('cf_change', '+0.5')}%"
        )
    
    # Power Curve Visualization
    st.markdown("---")
    st.subheader("⚡ Power Curve Analysis")
    
    # Tabs for different views
    tab1, tab2, tab3 = st.tabs(["Power Curve", "Time Series", "Heatmap"])
    
    with tab1:
        # Use real performance data from API
        render_power_curve(site_performance, availability_filter)
    
    with tab2:
        # Time series with real data
        date_range = (start_date, end_date) if start_date and end_date else None
        render_time_series(
            site_performance,
            metrics=['power_output', 'performance_ratio', 'availability'],
            date_range=date_range
        )
    
    with tab3:
        # Performance heatmap with real data
        render_performance_heatmap(site_performance, aggregate_by='hour_day')
    
    # Skid and Inverter Details
    if selected_skid:
        st.markdown("---")
        st.subheader(f"⚙️ Skid {selected_skid} Details")
        
        if inverters:
            # Display inverter grid
            inv_cols = st.columns(4)
            for idx, inv in enumerate(inverters[:4]):
                with inv_cols[idx % 4]:
                    with st.container(border=True):
                        st.markdown(f"**Inverter {inv['inverter_id']}**")
                        st.metric("Status", inv.get('status', 'Online'))
                        st.metric("Power", f"{inv.get('power', 250)} kW")
                        st.metric("Efficiency", f"{inv.get('efficiency', 98.2)}%")
    
    # Actions
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📥 Export Data", use_container_width=True):
            st.info("Export functionality will be implemented")
    
    with col2:
        if st.button("📊 Generate Report", use_container_width=True):
            st.info("Report generation will be implemented")
    
    with col3:
        if st.button("🤖 Ask AI Assistant", use_container_width=True):
            st.switch_page("pages/4_AI_Assistant.py")

except Exception as e:
    st.error(f"Failed to load site data: {str(e)}")
    if st.button("← Back to Portfolio"):
        st.switch_page("pages/1_Portfolio.py")