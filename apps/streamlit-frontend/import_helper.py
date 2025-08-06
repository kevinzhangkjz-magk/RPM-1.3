"""
Import helper for Streamlit Cloud compatibility
This module handles all the complex import logic in one place
"""

import sys
import os
from pathlib import Path

# Get the current file's directory
current_file = Path(__file__)
streamlit_frontend_dir = current_file.parent

# Add all necessary paths to sys.path
sys.path.insert(0, str(streamlit_frontend_dir))
sys.path.insert(0, str(streamlit_frontend_dir / 'lib'))
sys.path.insert(0, str(streamlit_frontend_dir / 'components'))

# Now import all modules
try:
    # Try with package structure
    from lib import session_state_isolated
    from lib import api_client_refactored
    from lib import auth_manager
    from lib import security
    from components import navigation
    from components import theme
except ImportError:
    # Import directly if package structure fails
    import session_state_isolated
    import api_client_refactored
    import auth_manager
    import security
    import navigation
    import theme

# Export the commonly used functions
initialize_session_state = session_state_isolated.initialize_session_state
get_session_value = session_state_isolated.get_session_value
set_session_value = session_state_isolated.set_session_value
get_api_client = api_client_refactored.get_api_client
check_and_redirect_auth = auth_manager.check_and_redirect_auth
input_sanitizer = security.input_sanitizer
render_breadcrumb = navigation.render_breadcrumb

# For additional imports
update_navigation_context = getattr(session_state_isolated, 'update_navigation_context', None)
is_authenticated = getattr(session_state_isolated, 'is_authenticated', None)
set_authenticated = getattr(session_state_isolated, 'set_authentication', None)  # Use correct function name
add_chat_message = getattr(session_state_isolated, 'add_chat_message', None)
get_chat_history = getattr(session_state_isolated, 'get_chat_history', None)
clear_session = getattr(session_state_isolated, 'clear_session', None)
