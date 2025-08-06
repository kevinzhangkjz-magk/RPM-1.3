"""
Login Page - Authentication for RPM Platform
"""

import streamlit as st
import httpx
import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import from helper
try:
    from import_helper import (
        initialize_session_state,
        get_api_client,
        input_sanitizer,
        is_authenticated,
        theme,
        set_authenticated,
        clear_session
    )
except ImportError:
    # Fallback: Add path and try again
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from import_helper import (
        initialize_session_state,
        get_api_client,
        input_sanitizer,
        is_authenticated,
        theme,
        set_authenticated,
        clear_session
    )

# Page config
st.set_page_config(
    page_title="Login - RPM",
    page_icon="🔐",
    layout="centered"
)

# Initialize session state
initialize_session_state()

# Apply theme
theme.apply_custom_theme()

# Check if already authenticated
if is_authenticated():
    st.success("✅ Already logged in!")
    if st.button("Go to Portfolio", type="primary"):
        st.switch_page("pages/1_Portfolio.py")
    if st.button("Logout"):
        clear_session()
        st.rerun()
    st.stop()

# Login form
st.title("🔐 RPM Login")
st.markdown("### Sign in to access the Solar Performance Monitoring Platform")

# Create login form
with st.form("login_form"):
    username = st.text_input("Username", placeholder="Enter your username")
    password = st.text_input("Password", type="password", placeholder="Enter your password")
    submitted = st.form_submit_button("Login", type="primary", use_container_width=True)

if submitted:
    # Validate inputs
    if not username or not password:
        st.error("Please enter both username and password")
    else:
        # Sanitize inputs
        username = input_sanitizer.sanitize_html(username)
        
        # Attempt authentication
        try:
            from lib.auth_manager import get_auth_manager
        except ImportError:
            import auth_manager
            get_auth_manager = auth_manager.get_auth_manager
        auth_manager = get_auth_manager()
        api_client = get_api_client()
        
        try:
            # Authenticate
            auth_response = auth_manager.login(username, password)
            
            # Extract auth data
            token = auth_response.get("access_token")
            user_id = auth_response.get("user_id", username)
            permissions = set(auth_response.get("permissions", []))
            
            # Set authentication in session
            set_authenticated(token, user_id, permissions)
            
            # Update API client with token
            api_client.set_auth_token(token)
            
            st.success("✅ Login successful!")
            st.info("Redirecting to portfolio...")
            st.balloons()
            
            # Redirect to portfolio
            st.switch_page("pages/1_Portfolio.py")
                
        except Exception as e:
            error_msg = str(e)
            if "Invalid credentials" in error_msg:
                st.error("❌ Invalid username or password")
            elif "Account locked" in error_msg:
                st.error("🚫 Account locked or insufficient permissions")
            elif "Cannot connect" in error_msg:
                st.warning("⚠️ Cannot connect to auth server. Using demo mode if credentials match.")
                st.info("Backend may not be running. Demo credentials will work offline.")
            else:
                st.error(f"Authentication error: {error_msg}")

# Demo credentials hint
with st.expander("Demo Credentials"):
    st.info("""
    **For testing purposes:**
    - Username: `demo`
    - Password: `demo123`
    
    Or use your assigned credentials.
    """)

# Footer
st.markdown("---")
st.caption("RPM 1.3 © 2025 | Secure Solar Asset Monitoring")