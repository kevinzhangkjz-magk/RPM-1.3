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
lib_dir = streamlit_frontend_dir / 'lib'
components_dir = streamlit_frontend_dir / 'components'

# Add all necessary paths to sys.path - ensure they're at the beginning
if str(streamlit_frontend_dir) not in sys.path:
    sys.path.insert(0, str(streamlit_frontend_dir))
if str(lib_dir) not in sys.path:
    sys.path.insert(0, str(lib_dir))
if str(components_dir) not in sys.path:
    sys.path.insert(0, str(components_dir))

# Import all modules with proper error handling
session_state_isolated = None
api_client_refactored = None
auth_manager = None
security = None
navigation = None
theme = None

# Try importing from lib directory first
try:
    from lib import session_state_isolated
    from lib import api_client_refactored
    from lib import auth_manager
    from lib import security
except ImportError as e1:
    # Try direct import
    try:
        import session_state_isolated
        import api_client_refactored
        import auth_manager
        import security
    except ImportError as e2:
        # Last resort: try to import from explicit path
        import importlib.util
        
        # Load session_state_isolated
        spec = importlib.util.spec_from_file_location(
            "session_state_isolated", 
            lib_dir / "session_state_isolated.py"
        )
        if spec and spec.loader:
            session_state_isolated = importlib.util.module_from_spec(spec)
            sys.modules["session_state_isolated"] = session_state_isolated
            spec.loader.exec_module(session_state_isolated)
        
        # Load api_client_refactored
        spec = importlib.util.spec_from_file_location(
            "api_client_refactored", 
            lib_dir / "api_client_refactored.py"
        )
        if spec and spec.loader:
            api_client_refactored = importlib.util.module_from_spec(spec)
            sys.modules["api_client_refactored"] = api_client_refactored
            spec.loader.exec_module(api_client_refactored)
        
        # Load auth_manager
        spec = importlib.util.spec_from_file_location(
            "auth_manager", 
            lib_dir / "auth_manager.py"
        )
        if spec and spec.loader:
            auth_manager = importlib.util.module_from_spec(spec)
            sys.modules["auth_manager"] = auth_manager
            spec.loader.exec_module(auth_manager)
        
        # Load security
        spec = importlib.util.spec_from_file_location(
            "security", 
            lib_dir / "security.py"
        )
        if spec and spec.loader:
            security = importlib.util.module_from_spec(spec)
            sys.modules["security"] = security
            spec.loader.exec_module(security)

# Try importing from components directory
try:
    from components import navigation
    from components import theme
except ImportError:
    try:
        import navigation
        import theme
    except ImportError:
        # Last resort: try to import from explicit path
        import importlib.util
        
        # Load navigation
        spec = importlib.util.spec_from_file_location(
            "navigation", 
            components_dir / "navigation.py"
        )
        if spec and spec.loader:
            navigation = importlib.util.module_from_spec(spec)
            sys.modules["navigation"] = navigation
            spec.loader.exec_module(navigation)
        
        # Load theme
        spec = importlib.util.spec_from_file_location(
            "theme", 
            components_dir / "theme.py"
        )
        if spec and spec.loader:
            theme = importlib.util.module_from_spec(spec)
            sys.modules["theme"] = theme
            spec.loader.exec_module(theme)

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