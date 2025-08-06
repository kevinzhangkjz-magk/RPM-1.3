"""
RPM Streamlit Application - Main Entry Point
Solar Asset Performance Monitoring Platform
"""

import streamlit as st
from pathlib import Path
import sys

# Add project root to path - handle both local and Streamlit Cloud
import os
current_dir = Path(__file__).parent
# Add multiple possible paths to handle different environments
sys.path.insert(0, str(current_dir))
sys.path.insert(0, str(current_dir.absolute()))
# For Streamlit Cloud - add the explicit path
sys.path.insert(0, '/mount/src/rpm-1.3/apps/streamlit-frontend')

from lib.session_state_isolated import initialize_session_state, get_session_value
from lib.api_client_refactored import get_api_client
from components.navigation import render_breadcrumb
import components.theme as theme

# Page configuration
st.set_page_config(
    page_title="RPM - Solar Performance Monitoring",
    page_icon="☀️",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'About': "RPM 1.3 - Solar Asset Performance Monitoring Platform"
    }
)

# Initialize session state
initialize_session_state()

# Apply custom CSS
theme.apply_custom_theme()

# Get API client singleton (thread-safe)
api_client = get_api_client()

# Main app header
col1, col2, col3 = st.columns([1, 3, 1])
with col2:
    st.title("⚡ RPM - Solar Performance Monitoring")
    st.markdown("### Monitor and analyze solar site performance data")

# Render breadcrumb navigation
render_breadcrumb()

# Main content area
st.markdown("---")

# Hero section
col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    ## Welcome to RPM 1.3
    
    Your comprehensive platform for solar asset performance monitoring and diagnostics.
    
    ### Key Features:
    - 📊 **Real-time Performance Monitoring**
    - 🔍 **Hierarchical Drill-down Analysis**
    - 🤖 **AI-Powered Diagnostics**
    - 📈 **Customizable Dashboards**
    - ⚡ **Power Curve Visualization**
    """)
    
    if st.button("🚀 View Portfolio", type="primary", use_container_width=True):
        st.switch_page("pages/1_Portfolio.py")

with col2:
    # Quick stats placeholder
    st.info("""
    ### System Overview
    
    Loading system statistics...
    
    - **Active Sites**: Fetching...
    - **Total Capacity**: Calculating...
    - **Current Performance**: Analyzing...
    - **Active Alerts**: Checking...
    """)

# Features grid
st.markdown("---")
st.markdown("## Platform Capabilities")

col1, col2, col3 = st.columns(3)

with col1:
    with st.container(border=True):
        st.markdown("""
        ### 📊 Site Overview
        
        View performance data for all your solar sites at a glance.
        
        - Portfolio-level metrics
        - Site comparisons
        - Performance rankings
        """)
        if st.button("Explore Sites", use_container_width=True):
            st.switch_page("pages/1_Portfolio.py")

with col2:
    with st.container(border=True):
        st.markdown("""
        ### 🔍 Detailed Analysis
        
        Drill down into specific site data with power curve visualizations.
        
        - Site → Skid → Inverter hierarchy
        - Power curve analysis
        - Performance trending
        """)
        if st.button("View Analytics", use_container_width=True):
            st.switch_page("pages/2_Site_Detail.py")

with col3:
    with st.container(border=True):
        st.markdown("""
        ### 🤖 AI Assistant
        
        Get instant answers to diagnostic questions about your assets.
        
        - Natural language queries
        - Automated diagnostics
        - Intelligent insights
        """)
        if st.button("Ask AI", use_container_width=True):
            st.switch_page("pages/4_AI_Assistant.py")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666;'>
    RPM 1.3 © 2025 | Solar Asset Performance Monitoring Platform
</div>
""", unsafe_allow_html=True)