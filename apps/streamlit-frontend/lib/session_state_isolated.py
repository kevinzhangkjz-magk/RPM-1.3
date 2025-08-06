"""
Isolated Session State Management for Multi-User Support
Implements proper session isolation to prevent data leakage between concurrent users
"""

import streamlit as st
from typing import Any, Dict, Optional, Set
import json
import uuid
import hashlib
from datetime import datetime, timedelta
from threading import RLock
import logging
from collections import defaultdict
from functools import wraps

logger = logging.getLogger(__name__)


class IsolatedSessionManager:
    """
    Thread-safe session manager with proper user isolation.
    Prevents data leakage between concurrent sessions.
    """
    
    def __init__(self):
        self._sessions: Dict[str, Dict[str, Any]] = {}
        self._session_metadata: Dict[str, Dict] = {}
        self._lock = RLock()
        self._max_sessions = 100
        self._session_timeout = 3600  # 1 hour
        self._cleanup_interval = 300  # 5 minutes
        self._last_cleanup = datetime.now()
    
    def get_session_id(self) -> str:
        """
        Get or create unique session ID for current user.
        Uses combination of session state ID and user context.
        """
        # Get Streamlit's session ID if available
        if hasattr(st.session_state, '_session_id'):
            return st.session_state._session_id
        
        # Generate unique session ID
        # Use combination of factors for uniqueness
        session_key = f"{id(st.session_state)}_{datetime.now().isoformat()}"
        session_id = hashlib.sha256(session_key.encode()).hexdigest()[:16]
        
        # Store in session state for consistency
        st.session_state._session_id = session_id
        
        # Initialize session if new
        with self._lock:
            if session_id not in self._sessions:
                self._initialize_session(session_id)
        
        return session_id
    
    def _initialize_session(self, session_id: str) -> None:
        """
        Initialize new isolated session.
        
        Args:
            session_id: Unique session identifier
        """
        self._sessions[session_id] = {
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
                'refresh_interval': 300,
                'chart_type': 'plotly',
                'notification_enabled': True
            },
            'csrf_token': None,
            'permissions': set(),
            'rate_limit_key': None
        }
        
        self._session_metadata[session_id] = {
            'created': datetime.now(),
            'last_accessed': datetime.now(),
            'access_count': 0,
            'ip_address': None,
            'user_agent': None
        }
        
        logger.info(f"Initialized new session: {session_id}")
    
    def get_session_data(self, session_id: str, key: str, default: Any = None) -> Any:
        """
        Get data from isolated session.
        
        Args:
            session_id: Session identifier
            key: Data key
            default: Default value if not found
            
        Returns:
            Session data or default
        """
        with self._lock:
            # Cleanup old sessions periodically
            self._cleanup_expired_sessions()
            
            if session_id not in self._sessions:
                self._initialize_session(session_id)
            
            # Update access metadata
            if session_id in self._session_metadata:
                self._session_metadata[session_id]['last_accessed'] = datetime.now()
                self._session_metadata[session_id]['access_count'] += 1
            
            return self._sessions[session_id].get(key, default)
    
    def set_session_data(self, session_id: str, key: str, value: Any) -> None:
        """
        Set data in isolated session.
        
        Args:
            session_id: Session identifier
            key: Data key
            value: Data value
        """
        with self._lock:
            if session_id not in self._sessions:
                self._initialize_session(session_id)
            
            # Validate data before setting
            if not self._validate_session_data(key, value):
                logger.warning(f"Invalid data for key {key} in session {session_id}")
                return
            
            self._sessions[session_id][key] = value
            
            # Update metadata
            if session_id in self._session_metadata:
                self._session_metadata[session_id]['last_accessed'] = datetime.now()
    
    def _validate_session_data(self, key: str, value: Any) -> bool:
        """
        Validate session data to prevent security issues.
        
        Args:
            key: Data key
            value: Data value
            
        Returns:
            True if valid, False otherwise
        """
        # Size limits
        MAX_STRING_LENGTH = 10000
        MAX_LIST_LENGTH = 1000
        MAX_DICT_SIZE = 100
        
        if isinstance(value, str) and len(value) > MAX_STRING_LENGTH:
            return False
        
        if isinstance(value, list) and len(value) > MAX_LIST_LENGTH:
            return False
        
        if isinstance(value, dict) and len(value) > MAX_DICT_SIZE:
            return False
        
        # Prevent storing sensitive keys
        sensitive_patterns = ['password', 'secret', 'private_key', 'api_key']
        if any(pattern in key.lower() for pattern in sensitive_patterns):
            logger.warning(f"Attempted to store sensitive data with key: {key}")
            return False
        
        return True
    
    def delete_session(self, session_id: str) -> None:
        """
        Delete session data completely.
        
        Args:
            session_id: Session identifier
        """
        with self._lock:
            if session_id in self._sessions:
                del self._sessions[session_id]
                logger.info(f"Deleted session: {session_id}")
            
            if session_id in self._session_metadata:
                del self._session_metadata[session_id]
    
    def _cleanup_expired_sessions(self) -> None:
        """
        Remove expired sessions to prevent memory leaks.
        """
        now = datetime.now()
        
        # Only cleanup periodically
        if (now - self._last_cleanup).seconds < self._cleanup_interval:
            return
        
        self._last_cleanup = now
        expired_sessions = []
        
        for session_id, metadata in self._session_metadata.items():
            last_accessed = metadata.get('last_accessed', now)
            if (now - last_accessed).seconds > self._session_timeout:
                expired_sessions.append(session_id)
        
        # Remove expired sessions
        for session_id in expired_sessions:
            self.delete_session(session_id)
        
        if expired_sessions:
            logger.info(f"Cleaned up {len(expired_sessions)} expired sessions")
        
        # Enforce maximum session limit
        if len(self._sessions) > self._max_sessions:
            # Remove oldest sessions
            sorted_sessions = sorted(
                self._session_metadata.items(),
                key=lambda x: x[1]['last_accessed']
            )
            
            sessions_to_remove = len(self._sessions) - self._max_sessions
            for session_id, _ in sorted_sessions[:sessions_to_remove]:
                self.delete_session(session_id)
            
            logger.warning(f"Removed {sessions_to_remove} sessions due to limit")
    
    def get_active_session_count(self) -> int:
        """
        Get count of active sessions.
        
        Returns:
            Number of active sessions
        """
        with self._lock:
            return len(self._sessions)
    
    def validate_session_permissions(self, session_id: str, 
                                    required_permission: str) -> bool:
        """
        Check if session has required permission.
        
        Args:
            session_id: Session identifier
            required_permission: Permission to check
            
        Returns:
            True if permission granted
        """
        with self._lock:
            if session_id not in self._sessions:
                return False
            
            permissions = self._sessions[session_id].get('permissions', set())
            return required_permission in permissions or 'admin' in permissions


# Global session manager instance
_session_manager = IsolatedSessionManager()


def get_session_manager() -> IsolatedSessionManager:
    """Get singleton session manager instance."""
    return _session_manager


def with_session_isolation(func):
    """
    Decorator to ensure function runs with isolated session context.
    
    Usage:
        @with_session_isolation
        def my_function():
            # Function has access to isolated session
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        manager = get_session_manager()
        session_id = manager.get_session_id()
        
        # Add session context to kwargs
        kwargs['_session_id'] = session_id
        
        return func(*args, **kwargs)
    
    return wrapper


# Convenience functions for backward compatibility

def initialize_session_state() -> None:
    """
    Initialize session state with isolation.
    """
    manager = get_session_manager()
    session_id = manager.get_session_id()
    
    # Session is auto-initialized, just log
    logger.debug(f"Session initialized: {session_id}")


def get_session_value(key: str, default: Any = None) -> Any:
    """
    Get value from isolated session.
    
    Args:
        key: Data key
        default: Default value
        
    Returns:
        Session value or default
    """
    manager = get_session_manager()
    session_id = manager.get_session_id()
    return manager.get_session_data(session_id, key, default)


def set_session_value(key: str, value: Any) -> None:
    """
    Set value in isolated session.
    
    Args:
        key: Data key
        value: Data value
    """
    manager = get_session_manager()
    session_id = manager.get_session_id()
    manager.set_session_data(session_id, key, value)


def update_navigation_context(site_id: Optional[str] = None,
                            skid_id: Optional[str] = None,
                            inverter_id: Optional[str] = None) -> None:
    """
    Update navigation context with isolation.
    
    Args:
        site_id: Selected site ID
        skid_id: Selected skid ID
        inverter_id: Selected inverter ID
    """
    manager = get_session_manager()
    session_id = manager.get_session_id()
    
    if site_id is not None:
        current_site = manager.get_session_data(session_id, 'selected_site')
        manager.set_session_data(session_id, 'selected_site', site_id)
        
        # Clear downstream selections when site changes
        if site_id != current_site:
            manager.set_session_data(session_id, 'selected_skid', None)
            manager.set_session_data(session_id, 'selected_inverter', None)
    
    if skid_id is not None:
        current_skid = manager.get_session_data(session_id, 'selected_skid')
        manager.set_session_data(session_id, 'selected_skid', skid_id)
        
        # Clear downstream selections when skid changes
        if skid_id != current_skid:
            manager.set_session_data(session_id, 'selected_inverter', None)
    
    if inverter_id is not None:
        manager.set_session_data(session_id, 'selected_inverter', inverter_id)
    
    # Update navigation history
    nav_history = manager.get_session_data(session_id, 'navigation_history', [])
    nav_entry = {
        'timestamp': datetime.now().isoformat(),
        'site': site_id,
        'skid': skid_id,
        'inverter': inverter_id
    }
    nav_history.append(nav_entry)
    
    # Keep only last 20 entries
    if len(nav_history) > 20:
        nav_history = nav_history[-20:]
    
    manager.set_session_data(session_id, 'navigation_history', nav_history)


def add_chat_message(role: str, content: str, metadata: Optional[Dict] = None) -> None:
    """
    Add message to isolated chat history.
    
    Args:
        role: 'user' or 'assistant'
        content: Message content
        metadata: Optional metadata
    """
    manager = get_session_manager()
    session_id = manager.get_session_id()
    
    # Sanitize content
    from lib.security import input_sanitizer
    content = input_sanitizer.sanitize_html(content)
    
    message = {
        'role': role,
        'content': content,
        'timestamp': datetime.now().isoformat(),
        'metadata': metadata or {}
    }
    
    chat_history = manager.get_session_data(session_id, 'chat_history', [])
    chat_history.append(message)
    
    # Keep only last 50 messages
    if len(chat_history) > 50:
        chat_history = chat_history[-50:]
    
    manager.set_session_data(session_id, 'chat_history', chat_history)


def is_authenticated() -> bool:
    """
    Check if current session is authenticated.
    
    Returns:
        True if authenticated
    """
    manager = get_session_manager()
    session_id = manager.get_session_id()
    
    token = manager.get_session_data(session_id, 'api_token')
    
    if not token:
        return False
    
    # Verify token is still valid
    from lib.security import session_security
    token_data = session_security.verify_jwt_token(token)
    
    if not token_data:
        # Token expired or invalid, clear it
        manager.set_session_data(session_id, 'api_token', None)
        manager.set_session_data(session_id, 'user_id', None)
        return False
    
    return True


def set_authentication(token: str, user_id: str, permissions: Set[str] = None) -> None:
    """
    Set authentication for isolated session.
    
    Args:
        token: JWT token
        user_id: User identifier
        permissions: User permissions set
    """
    manager = get_session_manager()
    session_id = manager.get_session_id()
    
    manager.set_session_data(session_id, 'api_token', token)
    manager.set_session_data(session_id, 'user_id', user_id)
    
    if permissions:
        manager.set_session_data(session_id, 'permissions', permissions)
    
    # Generate CSRF token for this session
    from lib.security import session_security
    csrf_token = session_security.generate_csrf_token()
    manager.set_session_data(session_id, 'csrf_token', csrf_token)
    
    logger.info(f"Authentication set for user {user_id} in session {session_id}")


def clear_session() -> None:
    """
    Clear current session data (logout).
    """
    manager = get_session_manager()
    session_id = manager.get_session_id()
    manager.delete_session(session_id)
    
    # Reset Streamlit session state
    if hasattr(st.session_state, '_session_id'):
        delattr(st.session_state, '_session_id')


def get_csrf_token() -> Optional[str]:
    """
    Get CSRF token for current session.
    
    Returns:
        CSRF token or None
    """
    manager = get_session_manager()
    session_id = manager.get_session_id()
    return manager.get_session_data(session_id, 'csrf_token')


def verify_csrf_token(token: str) -> bool:
    """
    Verify CSRF token for current session.
    
    Args:
        token: Token to verify
        
    Returns:
        True if valid
    """
    stored_token = get_csrf_token()
    
    if not stored_token or not token:
        return False
    
    from lib.security import session_security
    return session_security.verify_csrf_token(token, stored_token)


def require_permission(permission: str):
    """
    Decorator to require specific permission for function access.
    
    Usage:
        @require_permission('admin')
        def admin_function():
            # Admin only function
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            manager = get_session_manager()
            session_id = manager.get_session_id()
            
            if not manager.validate_session_permissions(session_id, permission):
                st.error(f"Permission denied. Required: {permission}")
                st.stop()
            
            return func(*args, **kwargs)
        
        return wrapper
    
    return decorator


# Session monitoring functions for admin

def get_session_stats() -> Dict:
    """
    Get statistics about active sessions.
    
    Returns:
        Session statistics dictionary
    """
    manager = get_session_manager()
    
    with manager._lock:
        active_count = len(manager._sessions)
        
        # Calculate average session age
        now = datetime.now()
        total_age = timedelta()
        
        for metadata in manager._session_metadata.values():
            created = metadata.get('created', now)
            total_age += (now - created)
        
        avg_age = total_age / active_count if active_count > 0 else timedelta()
        
        return {
            'active_sessions': active_count,
            'max_sessions': manager._max_sessions,
            'average_session_age': str(avg_age),
            'session_timeout': manager._session_timeout,
            'last_cleanup': manager._last_cleanup.isoformat()
        }