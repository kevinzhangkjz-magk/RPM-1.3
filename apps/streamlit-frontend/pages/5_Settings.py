"""
Settings Page - Configuration Management
Manages PPA rates and other system settings
"""

import streamlit as st
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import from helper
from import_helper import (
    initialize_session_state,
    get_api_client,
    check_and_redirect_auth,
    render_breadcrumb,
    theme
)

# Import settings components
from components.financial_settings import render_financial_settings

# Page config
st.set_page_config(
    page_title="Settings - RPM",
    page_icon="⚙️",
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

# Header
st.title("⚙️ System Settings")
st.markdown("Configure system parameters and financial settings")

# Render breadcrumb
render_breadcrumb()

# Settings tabs
tab1, tab2, tab3 = st.tabs(["💰 Financial", "🔧 System", "👤 User"])

with tab1:
    # Financial settings (PPA rates)
    render_financial_settings(api_client)

with tab2:
    # System settings
    st.subheader("System Configuration")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Performance Thresholds")
        
        r2_critical = st.slider(
            "R² Critical Threshold",
            min_value=0.0,
            max_value=1.0,
            value=0.7,
            step=0.05,
            help="Sites below this R² value are considered critical"
        )
        
        r2_warning = st.slider(
            "R² Warning Threshold",
            min_value=0.0,
            max_value=1.0,
            value=0.8,
            step=0.05,
            help="Sites below this R² value trigger warnings"
        )
        
        rmse_critical = st.number_input(
            "RMSE Critical Threshold (MW)",
            min_value=0.0,
            value=3.0,
            step=0.5,
            help="RMSE above this value is considered critical"
        )
        
        rmse_warning = st.number_input(
            "RMSE Warning Threshold (MW)",
            min_value=0.0,
            value=2.0,
            step=0.5,
            help="RMSE above this value triggers warnings"
        )
    
    with col2:
        st.markdown("### Data Processing")
        
        default_hours = st.number_input(
            "Default Monthly Hours",
            min_value=1,
            value=720,
            help="Default operational hours per month for calculations"
        )
        
        min_data_points = st.number_input(
            "Minimum Data Points",
            min_value=1,
            value=10,
            help="Minimum data points required for metric calculations"
        )
        
        variance_threshold = st.slider(
            "Variance Threshold",
            min_value=0.0,
            max_value=0.2,
            value=0.05,
            step=0.01,
            help="Minimum variance to detect stuck sensors"
        )
        
        negative_irradiance_limit = st.number_input(
            "Negative Irradiance Limit",
            max_value=0,
            value=-10,
            help="Filter out irradiance values below this threshold"
        )
    
    if st.button("💾 Save System Settings", type="primary"):
        # Save to session state
        st.session_state.system_config = {
            'r2_critical': r2_critical,
            'r2_warning': r2_warning,
            'rmse_critical': rmse_critical,
            'rmse_warning': rmse_warning,
            'default_hours': default_hours,
            'min_data_points': min_data_points,
            'variance_threshold': variance_threshold,
            'negative_irradiance_limit': negative_irradiance_limit
        }
        st.success("System settings saved!")

with tab3:
    # User settings
    st.subheader("User Preferences")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Display Preferences")
        
        theme_choice = st.selectbox(
            "Theme",
            ["Dark", "Light", "Auto"],
            index=0
        )
        
        date_format = st.selectbox(
            "Date Format",
            ["MM/DD/YYYY", "DD/MM/YYYY", "YYYY-MM-DD"],
            index=0
        )
        
        time_format = st.selectbox(
            "Time Format",
            ["12-hour", "24-hour"],
            index=0
        )
        
        units = st.selectbox(
            "Power Units",
            ["MW", "kW", "GW"],
            index=0
        )
    
    with col2:
        st.markdown("### Notification Settings")
        
        email_notifications = st.checkbox(
            "Email Notifications",
            value=True,
            help="Receive email alerts for critical issues"
        )
        
        if email_notifications:
            email = st.text_input(
                "Email Address",
                placeholder="user@example.com"
            )
            
            notification_types = st.multiselect(
                "Alert Types",
                ["Critical", "Warning", "Info", "Reports"],
                default=["Critical", "Warning"]
            )
        
        dashboard_refresh = st.select_slider(
            "Dashboard Refresh Rate",
            options=[60, 300, 600, 1800, 3600],
            value=300,
            format_func=lambda x: f"{x//60} min" if x < 3600 else f"{x//3600} hr"
        )
    
    if st.button("💾 Save User Preferences", type="primary"):
        # Save to session state
        st.session_state.user_preferences = {
            'theme': theme_choice,
            'date_format': date_format,
            'time_format': time_format,
            'units': units,
            'email_notifications': email_notifications,
            'dashboard_refresh': dashboard_refresh
        }
        st.success("User preferences saved!")

# Info section
st.markdown("---")
st.info("""
**Note:** Settings are stored in your session and will persist during your current session. 
For permanent changes, export your configuration and contact your system administrator.
""")