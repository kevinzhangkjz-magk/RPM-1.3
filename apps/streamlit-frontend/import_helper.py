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

# Try different possible locations for lib and components
possible_lib_paths = [
    streamlit_frontend_dir / 'lib',
    streamlit_frontend_dir.parent / 'lib',
    Path('/mount/src/rpm-1.3/lib'),
    Path('/app/lib'),
    Path('./lib'),
]

possible_components_paths = [
    streamlit_frontend_dir / 'components',
    streamlit_frontend_dir.parent / 'components',
    Path('/mount/src/rpm-1.3/components'),
    Path('/app/components'),
    Path('./components'),
]

# Find the actual lib and components directories
lib_dir = None
components_dir = None

for path in possible_lib_paths:
    if path.exists() and path.is_dir():
        lib_dir = path
        print(f"Found lib directory at: {lib_dir}")
        break

for path in possible_components_paths:
    if path.exists() and path.is_dir():
        components_dir = path
        print(f"Found components directory at: {components_dir}")
        break

# If still not found, try to locate by file
if not lib_dir:
    # Search for a specific file we know exists
    for path in possible_lib_paths:
        test_file = path / "session_state_isolated.py"
        if test_file.exists():
            lib_dir = path
            print(f"Found lib directory via file search at: {lib_dir}")
            break

if not components_dir:
    # Search for a specific file we know exists
    for path in possible_components_paths:
        test_file = path / "theme.py"
        if test_file.exists():
            components_dir = path
            print(f"Found components directory via file search at: {components_dir}")
            break

# Function to load module from file
def load_module_from_file(module_name, file_path):
    """Load a module directly from a file path"""
    try:
        if not file_path.exists():
            print(f"File not found: {file_path}")
            return None
            
        spec = importlib.util.spec_from_file_location(module_name, file_path)
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)
            return module
    except Exception as e:
        print(f"Failed to load {module_name} from {file_path}: {e}")
        return None

# Initialize all modules as None
session_state_isolated = None
api_client_refactored = None
auth_manager = None
security = None
navigation = None
theme = None

# Load modules if directories were found
if lib_dir:
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
else:
    print("WARNING: lib directory not found, creating stub implementations")

if components_dir:
    navigation = load_module_from_file(
        "navigation", 
        components_dir / "navigation.py"
    )
    
    theme = load_module_from_file(
        "theme", 
        components_dir / "theme.py"
    )
else:
    print("WARNING: components directory not found, creating stub implementations")

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
    print("WARNING: session_state_isolated not loaded, using stub functions")
    def initialize_session_state(): 
        import streamlit as st
        if 'initialized' not in st.session_state:
            st.session_state.initialized = True
    def get_session_value(key, default=None): 
        import streamlit as st
        return st.session_state.get(key, default)
    def set_session_value(key, value): 
        import streamlit as st
        st.session_state[key] = value
    update_navigation_context = None
    def is_authenticated(): 
        import streamlit as st
        return st.session_state.get('authenticated', False)
    def set_authenticated(value):
        import streamlit as st
        st.session_state['authenticated'] = value
    set_authenticated = set_authenticated
    def add_chat_message(role, content):
        import streamlit as st
        if 'chat_history' not in st.session_state:
            st.session_state.chat_history = []
        st.session_state.chat_history.append({'role': role, 'content': content})
    add_chat_message = add_chat_message
    def get_chat_history(): 
        import streamlit as st
        return st.session_state.get('chat_history', [])
    def clear_session(): 
        import streamlit as st
        for key in list(st.session_state.keys()):
            del st.session_state[key]

if api_client_refactored:
    get_api_client = getattr(api_client_refactored, 'get_api_client', lambda: None)
else:
    print("WARNING: api_client_refactored not loaded, creating mock API client")
    # Create a mock API client for testing
    class MockAPIClient:
        def __init__(self):
            self.base_url = "http://localhost:8000"
            
        def get_sites(self):
            """Return mock site data"""
            return {
                'sites': [
                    {
                        'site_id': 'DEMO-001',
                        'site_name': 'Demo Solar Site 1',
                        'status': 'online',
                        'current_power': 850.5,
                        'capacity': 1000,
                        'daily_energy': 6800,
                        'pr': 85.2,
                        'availability': 99.5
                    },
                    {
                        'site_id': 'DEMO-002',
                        'site_name': 'Demo Solar Site 2',
                        'status': 'warning',
                        'current_power': 420.3,
                        'capacity': 500,
                        'daily_energy': 3200,
                        'pr': 82.1,
                        'availability': 98.2
                    }
                ]
            }
            
        def get_site_details(self, site_id):
            """Return mock site details"""
            return {
                'site_id': site_id,
                'site_name': f'Demo Site {site_id}',
                'data': []
            }
            
        def get_portfolio_summary(self):
            """Return mock portfolio summary"""
            return {
                'total_sites': 2,
                'total_capacity': 1500,
                'total_power': 1270.8,
                'average_pr': 83.6
            }
    
    def get_api_client():
        return MockAPIClient()

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

print(f"Import helper initialization complete. Modules loaded: "
      f"session={session_state_isolated is not None}, "
      f"api={api_client_refactored is not None}, "
      f"auth={auth_manager is not None}, "
      f"security={security is not None}, "
      f"nav={navigation is not None}, "
      f"theme={theme is not None}")