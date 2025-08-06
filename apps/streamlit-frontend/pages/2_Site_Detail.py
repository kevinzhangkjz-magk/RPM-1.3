"""
Site Analysis Page - Power Curve and Skids Performance Analysis
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import numpy as np
import sys
from pathlib import Path
import calendar

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import from helper
from import_helper import (
    initialize_session_state,
    get_session_value,
    get_api_client,
    check_and_redirect_auth,
    theme
)

# Page config
st.set_page_config(
    page_title="Site Analysis - RPM",
    page_icon="⚡",
    layout="wide"
)

# Initialize session state
initialize_session_state()

# Apply theme
theme.apply_custom_theme()

# Check authentication
check_and_redirect_auth()

# Get API client
api_client = get_api_client()

# Check if site is selected
site_id = get_session_value('selected_site')
if not site_id:
    st.warning("No site selected. Please select a site from the portfolio.")
    if st.button("← Back to Portfolio"):
        st.switch_page("pages/1_Portfolio.py")
    st.stop()

# Header with connection status
col1, col2 = st.columns([6, 1])
with col1:
    if st.button("← Back to Portfolio"):
        st.switch_page("pages/1_Portfolio.py")
with col2:
    st.success("● Connected")

# Breadcrumb
st.caption(f"Portfolio > {site_id}")

# Page title
st.title(f"Power Curve - Site: {site_id}")
st.markdown("Actual vs. Expected Performance Analysis")

# Month/Year selector
current_year = datetime.now().year
current_month = datetime.now().month

col1, col2, col3 = st.columns([1, 1, 4])
with col1:
    selected_year = st.selectbox(
        "Year",
        options=list(range(2020, current_year + 1)),
        index=list(range(2020, current_year + 1)).index(current_year),
        key="year_selector"
    )

with col2:
    selected_month = st.selectbox(
        "Month",
        options=list(range(1, 13)),
        format_func=lambda x: calendar.month_name[x],
        index=current_month - 1,
        key="month_selector"
    )

with col3:
    if st.button("🔄 Refresh Data"):
        st.cache_data.clear()
        st.rerun()

# Fetch power curve data
try:
    with st.spinner("Loading power curve data..."):
        # Get power curve data from API
        power_curve_response = api_client._make_request(
            'GET',
            f'/api/sites/{site_id}/power-curve',
            params={'year': selected_year, 'month': selected_month}
        ).json()
        
        # Show fallback banner if using previous month's data
        if power_curve_response.get('data_fallback', False):
            st.warning(
                f"⚠️ Current month data not available. Showing data from {power_curve_response.get('data_month', 'previous month')}.",
                icon="⚠️"
            )
    
    # Main layout with power curve and metrics
    col_chart, col_metrics = st.columns([3, 1])
    
    with col_chart:
        st.subheader("Power Curve Visualization")
        
        # Create power curve scatter plot
        if power_curve_response.get('data_points'):
            df = pd.DataFrame(power_curve_response['data_points'])
            
            # Filter valid data points
            df = df.dropna(subset=['poa_irradiance', 'actual_power_mw'])
            df = df[df['poa_irradiance'] > 0]
            
            if not df.empty:
                fig = go.Figure()
                
                # Actual power scatter
                fig.add_trace(go.Scatter(
                    x=df['poa_irradiance'],
                    y=df['actual_power_mw'],
                    mode='markers',
                    name='Actual Power',
                    marker=dict(
                        color='#54b892',
                        size=4,
                        opacity=0.6
                    )
                ))
                
                # Expected power line (if available)
                if 'expected_power_mw' in df.columns:
                    # Sort by irradiance for smooth line
                    df_sorted = df.sort_values('poa_irradiance')
                    fig.add_trace(go.Scatter(
                        x=df_sorted['poa_irradiance'],
                        y=df_sorted['expected_power_mw'],
                        mode='lines',
                        name='Expected Power',
                        line=dict(
                            color='#bd6821',
                            width=2,
                            dash='dash'
                        )
                    ))
                
                fig.update_layout(
                    height=500,
                    xaxis_title="POA Irradiance (W/m²)",
                    yaxis_title="Power (MW)",
                    paper_bgcolor='#1b2437',
                    plot_bgcolor='#1b2437',
                    font=dict(color='#f0f0f0'),
                    xaxis=dict(gridcolor='#5f5f5f'),
                    yaxis=dict(gridcolor='#5f5f5f'),
                    legend=dict(
                        orientation="h",
                        yanchor="bottom",
                        y=1.02,
                        xanchor="right",
                        x=1
                    ),
                    hovermode='closest'
                )
                
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.error("No valid data points for power curve")
        else:
            st.error("No power curve data available")
    
    with col_metrics:
        st.subheader("RMSE")
        rmse_value = power_curve_response.get('rmse', 0.0)
        st.markdown(f"### {rmse_value:.1f} MW")
        
        st.markdown("---")
        
        st.subheader("R-Squared")
        r_squared = power_curve_response.get('r_squared', 0.0)
        st.markdown(f"### {r_squared:.2f}")
    
    # Skids Performance Section
    st.markdown("---")
    
    # Fetch skids performance data
    with st.spinner("Loading skids performance data..."):
        skids_response = api_client._make_request(
            'GET',
            f'/api/sites/{site_id}/skids-performance',
            params={'year': selected_year, 'month': selected_month}
        ).json()
    
    # Skids header with View All Skids button
    col1, col2 = st.columns([3, 1])
    with col1:
        st.subheader("Skid Performance")
        st.caption("Click to view detailed comparison")
    with col2:
        view_all_skids = st.button("View All Skids →", use_container_width=True)
    
    # Show skids analysis if button clicked or always show
    if True:  # Always show skids analysis below
        st.markdown("---")
        
        # Breadcrumb update
        st.caption(f"Portfolio > {site_id} > Skids")
        
        st.title(f"Skid Performance - Site: {site_id}")
        st.markdown("Comparative Analysis of All Skids")
        
        # Main layout for skids
        col_chart, col_summary = st.columns([3, 1])
        
        with col_chart:
            st.subheader("Skid Comparative Analysis")
            
            if skids_response.get('skids'):
                skids_df = pd.DataFrame(skids_response['skids'])
                
                # Create bar chart
                fig = go.Figure()
                
                # Add actual power bars
                fig.add_trace(go.Bar(
                    x=skids_df['skid_id'],
                    y=skids_df['actual_power_mw'],
                    name='Actual Power',
                    marker_color='#54b892'
                ))
                
                fig.update_layout(
                    height=400,
                    xaxis_title="Skids",
                    yaxis_title="Power (MW)",
                    paper_bgcolor='#1b2437',
                    plot_bgcolor='#1b2437',
                    font=dict(color='#f0f0f0'),
                    xaxis=dict(gridcolor='#5f5f5f'),
                    yaxis=dict(gridcolor='#5f5f5f'),
                    showlegend=False,
                    hovermode='x unified'
                )
                
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No skids data available")
        
        with col_summary:
            st.subheader("Site Summary")
            
            st.metric("Total Skids:", skids_response.get('total_skids', 0))
            st.metric("Connected:", "Yes" if skids_response.get('total_skids', 0) > 0 else "No")
            
            st.markdown("---")
            
            # Top Performers (highest absolute power)
            st.subheader("Top Performers")
            skids_data = skids_response.get('skids', [])
            if skids_data:
                # Sort by actual power MW descending
                sorted_by_power = sorted(skids_data, key=lambda x: x.get('actual_power_mw', 0), reverse=True)
                for skid in sorted_by_power[:3]:
                    col1, col2 = st.columns([2, 1])
                    with col1:
                        st.caption(skid['skid_id'])
                    with col2:
                        st.caption(f"{skid.get('actual_power_mw', 0):.2f} MW")
            else:
                st.caption("No data available")
            
            st.markdown("---")
            
            # Under Performers (lowest absolute power)
            st.subheader("Under Performers")
            skids_data = skids_response.get('skids', [])
            if skids_data:
                # Sort by actual power MW ascending (lowest first)
                sorted_by_power = sorted(skids_data, key=lambda x: x.get('actual_power_mw', 0))
                for skid in sorted_by_power[:3]:
                    col1, col2 = st.columns([2, 1])
                    with col1:
                        st.caption(skid['skid_id'])
                    with col2:
                        st.caption(f"{skid.get('actual_power_mw', 0):.2f} MW")
            else:
                st.caption("No underperforming skids")
        
        # Bottom action buttons
        st.markdown("---")
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("← Back to Portfolio", key="back_bottom"):
                st.switch_page("pages/1_Portfolio.py")
        with col2:
            st.button("Export Data", use_container_width=True, disabled=True)
        with col3:
            st.button("View Report", use_container_width=True, disabled=True)

except Exception as e:
    st.error(f"Failed to load site data: {str(e)}")
    if st.button("← Back to Portfolio", key="error_back"):
        st.switch_page("pages/1_Portfolio.py")