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

# Detect environment and set paths
if os.path.exists('/mount/src/rpm-1.3/apps/streamlit-frontend'):
    # Streamlit Cloud environment
    BASE_PATH = '/mount/src/rpm-1.3/apps/streamlit-frontend'
else:
    # Local environment
    BASE_PATH = str(current_dir)

# Add all necessary paths
sys.path.insert(0, BASE_PATH)
sys.path.insert(0, os.path.join(BASE_PATH, 'lib'))
sys.path.insert(0, os.path.join(BASE_PATH, 'components'))

# Import directly from the modules
try:
    # Try imports with lib/components prefix first
    from lib.session_state_isolated import initialize_session_state, get_session_value
    from lib.api_client_refactored import get_api_client
    from components.navigation import render_breadcrumb
    import components.theme as theme
except ImportError as e1:
    try:
        # Try direct imports without lib/components prefix
        import session_state_isolated
        import api_client_refactored
        import navigation
        import theme
        
        # Create the expected functions/modules
        initialize_session_state = session_state_isolated.initialize_session_state
        get_session_value = session_state_isolated.get_session_value
        get_api_client = api_client_refactored.get_api_client
        render_breadcrumb = navigation.render_breadcrumb
    except ImportError as e2:
        # If all imports fail, show diagnostic information
        st.error(f"Failed to import required modules!")
        st.error(f"Current working directory: {os.getcwd()}")
        st.error(f"BASE_PATH: {BASE_PATH}")
        st.error(f"Python path: {sys.path[:5]}")  # Show first 5 paths
        st.error(f"First error: {e1}")
        st.error(f"Second error: {e2}")
        
        # Check if files exist
        lib_path = os.path.join(BASE_PATH, 'lib')
        if os.path.exists(lib_path):
            st.error(f"Contents of lib directory: {os.listdir(lib_path)[:10]}")
        else:
            st.error(f"lib directory not found at: {lib_path}")
        st.stop()

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