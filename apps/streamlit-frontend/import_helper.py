"""
Import helper for Streamlit Cloud compatibility
This module handles all the complex import logic in one place
"""

import sys
import os
from pathlib import Path
import importlib.util

# Get the current file's directory
current_file = Path(__file__)
streamlit_frontend_dir = current_file.parent
lib_dir = streamlit_frontend_dir / 'lib'
components_dir = streamlit_frontend_dir / 'components'

# Function to load module from file
def load_module_from_file(module_name, file_path):
    """Load a module directly from a file path"""
    try:
        spec = importlib.util.spec_from_file_location(module_name, file_path)
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)
            return module
    except Exception as e:
        print(f"Failed to load {module_name} from {file_path}: {e}")
        return None

# Load all required modules directly from files
session_state_isolated = load_module_from_file(
    "session_state_isolated", 
    lib_dir / "session_state_isolated.py"
)

api_client_refactored = load_module_from_file(
    "api_client_refactored", 
    lib_dir / "api_client_refactored.py"
)

auth_manager = load_module_from_file(
    "auth_manager", 
    lib_dir / "auth_manager.py"
)

security = load_module_from_file(
    "security", 
    lib_dir / "security.py"
)

navigation = load_module_from_file(
    "navigation", 
    components_dir / "navigation.py"
)

theme = load_module_from_file(
    "theme", 
    components_dir / "theme.py"
)

# Export the commonly used functions with proper error handling
if session_state_isolated:
    initialize_session_state = getattr(session_state_isolated, 'initialize_session_state', lambda: None)
    get_session_value = getattr(session_state_isolated, 'get_session_value', lambda k, d=None: d)
    set_session_value = getattr(session_state_isolated, 'set_session_value', lambda k, v: None)
    update_navigation_context = getattr(session_state_isolated, 'update_navigation_context', None)
    is_authenticated = getattr(session_state_isolated, 'is_authenticated', lambda: False)
    set_authenticated = getattr(session_state_isolated, 'set_authentication', None)
    add_chat_message = getattr(session_state_isolated, 'add_chat_message', None)
    get_chat_history = getattr(session_state_isolated, 'get_chat_history', lambda: [])
    clear_session = getattr(session_state_isolated, 'clear_session', lambda: None)
else:
    # Provide stub functions if module failed to load
    def initialize_session_state(): pass
    def get_session_value(key, default=None): return default
    def set_session_value(key, value): pass
    update_navigation_context = None
    def is_authenticated(): return False
    set_authenticated = None
    add_chat_message = None
    def get_chat_history(): return []
    def clear_session(): pass

if api_client_refactored:
    get_api_client = getattr(api_client_refactored, 'get_api_client', lambda: None)
else:
    def get_api_client(): return None

if auth_manager:
    check_and_redirect_auth = getattr(auth_manager, 'check_and_redirect_auth', lambda: None)
else:
    def check_and_redirect_auth(): pass

if security:
    input_sanitizer = getattr(security, 'input_sanitizer', lambda x: x)
else:
    def input_sanitizer(x): return x

if navigation:
    render_breadcrumb = getattr(navigation, 'render_breadcrumb', lambda: None)
else:
    def render_breadcrumb(): pass

# Export theme module directly
if not theme:
    # Create a stub theme module with minimal functionality
    class ThemeStub:
        @staticmethod
        def apply_custom_theme():
            pass
    theme = ThemeStub()