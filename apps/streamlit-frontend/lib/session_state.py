"""
Session State Management for Streamlit Application
Handles user session data and preferences
"""

import streamlit as st
from typing import Any, Dict, Optional
import json
from datetime import datetime


def initialize_session_state() -> None:
    """
    Initialize default session state values if not already present.
    Called at the start of each page load.
    """
    defaults = {
        'user_id': None,
        'selected_site': None,
        'selected_skid': None,
        'selected_inverter': None,
        'dashboard_layout': {
            'widgets': ['performance_leaderboard', 'active_alerts', 'power_curve'],
            'positions': {}
        },
        'chat_history': [],
        'filters': {
            'date_range': None,
            'availability_filter': False,
            'site_types': []
        },
        'cached_data': {},
        'last_refresh': None,
        'theme_preference': 'dark',
        'navigation_history': [],
        'api_token': None,
        'user_preferences': {
            'auto_refresh': True,
            'refresh_interval': 300,  # seconds
            'chart_type': 'plotly',
            'notification_enabled': True
        }
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def get_session_value(key: str, default: Any = None) -> Any:
    """
    Safely get a value from session state.
    
    Args:
        key: The session state key
        default: Default value if key doesn't exist
        
    Returns:
        The session value or default
    """
    return st.session_state.get(key, default)


def set_session_value(key: str, value: Any) -> None:
    """
    Set a value in session state.
    
    Args:
        key: The session state key
        value: The value to set
    """
    st.session_state[key] = value


def update_navigation_context(site_id: Optional[str] = None, 
                            skid_id: Optional[str] = None,
                            inverter_id: Optional[str] = None) -> None:
    """
    Update the navigation context in session state.
    
    Args:
        site_id: Selected site ID
        skid_id: Selected skid ID
        inverter_id: Selected inverter ID
    """
    if site_id is not None:
        st.session_state.selected_site = site_id
        # Clear downstream selections when site changes
        if site_id != st.session_state.get('selected_site'):
            st.session_state.selected_skid = None
            st.session_state.selected_inverter = None
    
    if skid_id is not None:
        st.session_state.selected_skid = skid_id
        # Clear downstream selections when skid changes
        if skid_id != st.session_state.get('selected_skid'):
            st.session_state.selected_inverter = None
    
    if inverter_id is not None:
        st.session_state.selected_inverter = inverter_id
    
    # Update navigation history
    nav_entry = {
        'timestamp': datetime.now().isoformat(),
        'site': site_id,
        'skid': skid_id,
        'inverter': inverter_id
    }
    
    if 'navigation_history' not in st.session_state:
        st.session_state.navigation_history = []
    
    st.session_state.navigation_history.append(nav_entry)
    
    # Keep only last 20 navigation entries
    if len(st.session_state.navigation_history) > 20:
        st.session_state.navigation_history = st.session_state.navigation_history[-20:]


def save_dashboard_layout(layout: Dict) -> None:
    """
    Save the user's dashboard layout configuration.
    
    Args:
        layout: Dictionary containing widget positions and configuration
    """
    st.session_state.dashboard_layout = layout
    # In production, this would persist to database
    # For now, we save to local storage via session state


def get_dashboard_layout() -> Dict:
    """
    Get the user's saved dashboard layout.
    
    Returns:
        Dictionary containing dashboard configuration
    """
    return st.session_state.get('dashboard_layout', {
        'widgets': ['performance_leaderboard', 'active_alerts', 'power_curve'],
        'positions': {}
    })


def add_chat_message(role: str, content: str, metadata: Optional[Dict] = None) -> None:
    """
    Add a message to the chat history.
    
    Args:
        role: 'user' or 'assistant'
        content: The message content
        metadata: Optional metadata (charts, data, etc.)
    """
    message = {
        'role': role,
        'content': content,
        'timestamp': datetime.now().isoformat(),
        'metadata': metadata or {}
    }
    
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    
    st.session_state.chat_history.append(message)
    
    # Keep only last 50 messages for memory efficiency
    if len(st.session_state.chat_history) > 50:
        st.session_state.chat_history = st.session_state.chat_history[-50:]


def clear_chat_history() -> None:
    """Clear the chat conversation history."""
    st.session_state.chat_history = []


def cache_data(key: str, data: Any, ttl: int = 300) -> None:
    """
    Cache data in session state with TTL.
    
    Args:
        key: Cache key
        data: Data to cache
        ttl: Time to live in seconds
    """
    cache_entry = {
        'data': data,
        'timestamp': datetime.now().timestamp(),
        'ttl': ttl
    }
    
    if 'cached_data' not in st.session_state:
        st.session_state.cached_data = {}
    
    st.session_state.cached_data[key] = cache_entry


def get_cached_data(key: str) -> Optional[Any]:
    """
    Get cached data if still valid.
    
    Args:
        key: Cache key
        
    Returns:
        Cached data or None if expired/not found
    """
    if 'cached_data' not in st.session_state:
        return None
    
    if key not in st.session_state.cached_data:
        return None
    
    cache_entry = st.session_state.cached_data[key]
    current_time = datetime.now().timestamp()
    
    # Check if cache is still valid
    if current_time - cache_entry['timestamp'] > cache_entry['ttl']:
        # Cache expired, remove it
        del st.session_state.cached_data[key]
        return None
    
    return cache_entry['data']


def clear_cache() -> None:
    """Clear all cached data."""
    st.session_state.cached_data = {}


def is_authenticated() -> bool:
    """
    Check if user is authenticated.
    
    Returns:
        True if user has valid authentication
    """
    return st.session_state.get('api_token') is not None


def set_authentication(token: str, user_id: str) -> None:
    """
    Set authentication credentials.
    
    Args:
        token: API authentication token
        user_id: User identifier
    """
    st.session_state.api_token = token
    st.session_state.user_id = user_id