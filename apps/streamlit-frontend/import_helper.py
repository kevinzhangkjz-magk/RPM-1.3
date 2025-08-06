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
    Path('/mount/src/rpm-1.3/apps/streamlit-frontend/lib'),
    Path('/app/lib'),
    Path('./lib'),
]

possible_components_paths = [
    streamlit_frontend_dir / 'components',
    streamlit_frontend_dir.parent / 'components',
    Path('/mount/src/rpm-1.3/apps/streamlit-frontend/components'),
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
    print("WARNING: lib directory not found, modules will be created inline")

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
    print("WARNING: components directory not found")

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

# Handle API client - ALWAYS create a real API client
if api_client_refactored:
    get_api_client = getattr(api_client_refactored, 'get_api_client', None)
    
if not api_client_refactored or not get_api_client:
    print("WARNING: api_client_refactored not loaded properly, creating inline API client")
    # Create the real API client inline if module loading failed
    import httpx
    import logging
    from typing import Dict, List, Optional, Any, Tuple
    from tenacity import retry, stop_after_attempt, wait_exponential
    import json
    from datetime import datetime, timedelta
    from dotenv import load_dotenv
    
    load_dotenv()
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    class CacheManager:
        """Cache manager for API responses"""
        def __init__(self, ttl: int = 300):
            self.cache: Dict[str, Tuple[Any, datetime]] = {}
            self.ttl = ttl
        
        def _get_cache_key(self, method: str, endpoint: str, **kwargs) -> str:
            key_data = f"{method}:{endpoint}:{json.dumps(kwargs, sort_keys=True)}"
            import hashlib
            return hashlib.md5(key_data.encode()).hexdigest()
        
        def get(self, method: str, endpoint: str, **kwargs) -> Optional[Any]:
            key = self._get_cache_key(method, endpoint, **kwargs)
            if key in self.cache:
                data, timestamp = self.cache[key]
                if datetime.now() - timestamp < timedelta(seconds=self.ttl):
                    return data
                else:
                    del self.cache[key]
            return None
        
        def set(self, method: str, endpoint: str, data: Any, **kwargs) -> None:
            key = self._get_cache_key(method, endpoint, **kwargs)
            self.cache[key] = (data, datetime.now())
        
        def clear(self) -> None:
            self.cache.clear()
    
    class APIClient:
        """Real API client for communicating with FastAPI backend"""
        
        def __init__(self, cache_manager: Optional[CacheManager] = None):
            self.base_url = os.getenv('API_BASE_URL', 'http://localhost:8000')
            self.timeout = int(os.getenv('API_TIMEOUT', '30'))
            self.headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }
            self.auth = ('testuser', 'testpass')  # Basic Auth credentials
            self._client = None
            self.cache = cache_manager or CacheManager()
            logger.info(f"APIClient initialized with base_url: {self.base_url}")
        
        @property
        def client(self) -> httpx.Client:
            if self._client is None:
                self._client = httpx.Client(
                    base_url=self.base_url,
                    timeout=self.timeout,
                    headers=self.headers,
                    auth=self.auth
                )
            return self._client
        
        @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
        def _make_request(self, method: str, endpoint: str, **kwargs) -> httpx.Response:
            try:
                logger.info(f"Making {method} request to {endpoint}")
                response = self.client.request(method, endpoint, **kwargs)
                response.raise_for_status()
                logger.info(f"Request successful: {response.status_code}")
                return response
            except Exception as e:
                logger.error(f"Request failed: {e}")
                raise
        
        def get_sites(self) -> List[Dict[str, Any]]:
            """Get all sites from the API"""
            cached = self.cache.get('GET', '/api/sites/')
            if cached is not None:
                return cached
            
            try:
                response = self._make_request('GET', '/api/sites/')
                data = response.json()
                self.cache.set('GET', '/api/sites/', data)
                return data
            except Exception as e:
                logger.error(f"Failed to get sites: {e}")
                # Return empty list instead of None to prevent AttributeError
                return []
        
        def get_site_details(self, site_id: str) -> Dict[str, Any]:
            """Get details for a specific site"""
            endpoint = f'/api/sites/{site_id}'
            cached = self.cache.get('GET', endpoint)
            if cached is not None:
                return cached
            
            try:
                response = self._make_request('GET', endpoint)
                data = response.json()
                self.cache.set('GET', endpoint, data)
                return data
            except Exception as e:
                logger.error(f"Failed to get site details: {e}")
                return {}
        
        def get_portfolio_summary(self) -> Dict[str, Any]:
            """Get portfolio summary"""
            endpoint = '/api/portfolio/summary'
            cached = self.cache.get('GET', endpoint)
            if cached is not None:
                return cached
            
            try:
                response = self._make_request('GET', endpoint)
                data = response.json()
                self.cache.set('GET', endpoint, data)
                return data
            except Exception as e:
                logger.error(f"Failed to get portfolio summary: {e}")
                return {}
    
    # Global instance
    _api_client_instance = None
    
    def get_api_client() -> APIClient:
        """Get or create singleton API client instance"""
        global _api_client_instance
        if _api_client_instance is None:
            _api_client_instance = APIClient()
        return _api_client_instance

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