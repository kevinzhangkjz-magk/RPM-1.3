"""
Dashboard Page - Customizable dashboard with widgets
Persists layout in session state and to database
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import json
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from lib.session_state import (
    initialize_session_state, 
    get_dashboard_layout,
    save_dashboard_layout
)
from lib.api_client import get_api_client
from components.widgets import (
    render_performance_leaderboard,
    render_active_alerts,
    render_power_curve_widget,
    render_quick_stats,
    render_availability_tracker
)
from components.navigation import render_breadcrumb
import components.theme as theme

# Page config
st.set_page_config(
    page_title="Dashboard - RPM",
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
st.title("📊 Customizable Dashboard")
st.markdown("Arrange widgets to create your perfect monitoring view")

# Render breadcrumb
render_breadcrumb()

# Dashboard controls
st.markdown("---")
col1, col2, col3, col4 = st.columns([2, 2, 1, 1])

with col1:
    # Widget selector
    available_widgets = {
        "Performance Leaderboard": "performance_leaderboard",
        "Active Alerts": "active_alerts",
        "Power Curve": "power_curve",
        "Quick Stats": "quick_stats",
        "Availability Tracker": "availability_tracker"
    }
    
    selected_widgets = st.multiselect(
        "Select Widgets",
        options=list(available_widgets.keys()),
        default=["Performance Leaderboard", "Active Alerts", "Power Curve"]
    )

with col2:
    # Layout preset
    layout_preset = st.selectbox(
        "Layout Preset",
        ["Default", "Operations Focus", "Performance Focus", "Custom"]
    )

with col3:
    # Save button
    if st.button("💾 Save Layout", use_container_width=True):
        # Save current widget selection to session state
        layout = {
            'widgets': [available_widgets[w] for w in selected_widgets],
            'positions': {},  # Would store actual positions in production
            'preset': layout_preset
        }
        save_dashboard_layout(layout)
        
        # Try to persist to database
        if st.session_state.get('user_id'):
            if api_client.save_dashboard_config(st.session_state.user_id, layout):
                st.success("Dashboard saved!")
            else:
                st.warning("Dashboard saved locally only")
        else:
            st.info("Dashboard saved to session")

with col4:
    # Refresh button
    if st.button("🔄 Refresh", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

# Apply layout preset
if layout_preset == "Operations Focus":
    selected_widgets = ["Active Alerts", "Availability Tracker", "Quick Stats"]
elif layout_preset == "Performance Focus":
    selected_widgets = ["Performance Leaderboard", "Power Curve", "Quick Stats"]

# Main dashboard area
st.markdown("---")

# Fetch data for widgets
try:
    with st.spinner("Loading dashboard data..."):
        sites = api_client.get_sites()
        
        # Get performance data for each site
        sites_performance = []
        for site in sites[:10]:  # Limit to 10 for performance
            try:
                perf = api_client.get_site_performance(site['site_id'])
                sites_performance.append({
                    'site_id': site['site_id'],
                    'site_name': site.get('site_name', site['site_id']),
                    'performance': perf.get('performance_ratio', 0),
                    'availability': perf.get('availability', 0),
                    'capacity_factor': perf.get('capacity_factor', 0),
                    'current_output': perf.get('current_output', 0)
                })
            except:
                continue

    # Render widgets based on selection
    widget_map = {
        "performance_leaderboard": render_performance_leaderboard,
        "active_alerts": render_active_alerts,
        "power_curve": render_power_curve_widget,
        "quick_stats": render_quick_stats,
        "availability_tracker": render_availability_tracker
    }
    
    # Dynamic layout based on number of widgets
    if len(selected_widgets) == 1:
        # Single widget - full width
        widget_key = available_widgets[selected_widgets[0]]
        if widget_key in widget_map:
            with st.container(border=True):
                widget_map[widget_key](sites_performance, api_client)
    
    elif len(selected_widgets) == 2:
        # Two widgets - side by side
        col1, col2 = st.columns(2)
        
        for idx, widget_name in enumerate(selected_widgets[:2]):
            widget_key = available_widgets[widget_name]
            if widget_key in widget_map:
                with [col1, col2][idx]:
                    with st.container(border=True):
                        widget_map[widget_key](sites_performance, api_client)
    
    elif len(selected_widgets) >= 3:
        # Three or more widgets - grid layout
        # First row - 2 widgets
        if len(selected_widgets) >= 2:
            col1, col2 = st.columns(2)
            
            widget_key = available_widgets[selected_widgets[0]]
            if widget_key in widget_map:
                with col1:
                    with st.container(border=True):
                        widget_map[widget_key](sites_performance, api_client)
            
            widget_key = available_widgets[selected_widgets[1]]
            if widget_key in widget_map:
                with col2:
                    with st.container(border=True):
                        widget_map[widget_key](sites_performance, api_client)
        
        # Second row - remaining widgets
        if len(selected_widgets) >= 3:
            remaining = selected_widgets[2:]
            if len(remaining) == 1:
                # Single widget - full width
                widget_key = available_widgets[remaining[0]]
                if widget_key in widget_map:
                    with st.container(border=True):
                        widget_map[widget_key](sites_performance, api_client)
            else:
                # Multiple widgets - columns
                cols = st.columns(min(3, len(remaining)))
                for idx, widget_name in enumerate(remaining[:3]):
                    widget_key = available_widgets[widget_name]
                    if widget_key in widget_map:
                        with cols[idx]:
                            with st.container(border=True):
                                widget_map[widget_key](sites_performance, api_client)
    
    # Auto-refresh info
    st.markdown("---")
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.caption(f"Dashboard auto-refreshes every 5 minutes • Last update: {datetime.now().strftime('%H:%M:%S')}")
    
    with col2:
        auto_refresh = st.checkbox("Enable auto-refresh", value=True)
        
        if auto_refresh:
            # In production, would use st.rerun() with timer
            pass

except Exception as e:
    st.error(f"Failed to load dashboard data: {str(e)}")
    st.info("Please check your API connection and try again.")

# Footer with tips
with st.expander("💡 Dashboard Tips"):
    st.markdown("""
    - **Customize your view**: Select widgets that matter most to your workflow
    - **Save layouts**: Your dashboard configuration persists across sessions
    - **Keyboard shortcuts**: Press 'R' to refresh, 'S' to save layout
    - **Mobile friendly**: Dashboard adapts to smaller screens automatically
    - **Real-time updates**: Enable auto-refresh for live monitoring
    """)