"""
Authentication Manager
Handles login, token management, and auth state
"""

import streamlit as st
import httpx
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import jwt
from functools import wraps

from lib.session_state_isolated import (
    get_session_value, 
    set_session_value,
    set_authentication,
    is_authenticated,
    clear_session
)
from lib.security import session_security

logger = logging.getLogger(__name__)


class AuthManager:
    """Manages authentication flow and token handling"""
    
    def __init__(self, api_base_url: str = None):
        self.api_base_url = api_base_url or "http://localhost:8000"
        self.auth_endpoint = f"{self.api_base_url}/api/auth/login"
        self.refresh_endpoint = f"{self.api_base_url}/api/auth/refresh"
        
    def login(self, username: str, password: str) -> Dict[str, Any]:
        """
        Authenticate user and get JWT token
        
        Args:
            username: User's username
            password: User's password
            
        Returns:
            Auth response with token and user info
            
        Raises:
            Exception: On authentication failure
        """
        try:
            response = httpx.post(
                self.auth_endpoint,
                json={"username": username, "password": password},
                timeout=10
            )
            
            if response.status_code == 200:
                auth_data = response.json()
                logger.info(f"User {username} authenticated successfully")
                return auth_data
            elif response.status_code == 401:
                raise Exception("Invalid credentials")
            elif response.status_code == 403:
                raise Exception("Account locked or disabled")
            elif response.status_code == 404:
                # Auth endpoint not implemented yet, bypass for now
                logger.warning("Auth endpoint not found, bypassing authentication")
                return self._create_bypass_auth_response(username)
            else:
                raise Exception(f"Authentication failed: {response.status_code}")
                
        except httpx.ConnectError:
            logger.error("Cannot connect to auth server, bypassing auth")
            # Bypass auth if backend is running but auth not implemented
            return self._create_bypass_auth_response(username)
            
        except httpx.TimeoutException:
            raise Exception("Authentication timeout")
            
    def _create_bypass_auth_response(self, username: str) -> Dict[str, Any]:
        """
        Create mock auth response for development/demo
        
        Args:
            username: Username
            
        Returns:
            Mock auth response
        """
        # Create mock JWT token
        payload = {
            'user_id': username,
            'username': username,
            'exp': datetime.utcnow() + timedelta(hours=24),
            'iat': datetime.utcnow(),
            'permissions': ['read', 'write']
        }
        
        # Use a demo secret key
        secret_key = "demo-secret-key-not-for-production"
        token = jwt.encode(payload, secret_key, algorithm='HS256')
        
        return {
            'access_token': token,
            'token_type': 'bearer',
            'user_id': username,
            'username': username,
            'permissions': ['read', 'write'],
            'expires_in': 86400  # 24 hours
        }
    
    def refresh_token(self, refresh_token: str) -> Dict[str, Any]:
        """
        Refresh authentication token
        
        Args:
            refresh_token: Current refresh token
            
        Returns:
            New auth response
        """
        try:
            response = httpx.post(
                self.refresh_endpoint,
                json={"refresh_token": refresh_token},
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                raise Exception("Token refresh failed")
                
        except Exception as e:
            logger.error(f"Token refresh error: {str(e)}")
            raise
    
    def logout(self) -> None:
        """Clear authentication and session data"""
        clear_session()
        logger.info("User logged out")
    
    def check_auth_required(self) -> bool:
        """
        Check if authentication is required
        
        Returns:
            True if auth needed, False otherwise
        """
        # Check if already authenticated
        if is_authenticated():
            return False
            
        # Check if on login page
        import inspect
        frame = inspect.currentframe()
        if frame and frame.f_back:
            filename = frame.f_back.f_code.co_filename
            if '0_Login.py' in filename:
                return False
                
        return True
    
    def require_auth(self):
        """
        Decorator to require authentication for pages
        
        Usage:
            auth_manager = AuthManager()
            
            @auth_manager.require_auth()
            def protected_page():
                # Page content
        """
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                if not is_authenticated():
                    st.error("🔒 Authentication required")
                    st.info("Please login to access this page")
                    if st.button("Go to Login"):
                        st.switch_page("pages/0_Login.py")
                    st.stop()
                return func(*args, **kwargs)
            return wrapper
        return decorator


# Global auth manager instance
_auth_manager = None

def get_auth_manager() -> AuthManager:
    """Get singleton auth manager instance"""
    global _auth_manager
    if _auth_manager is None:
        import os
        api_url = os.getenv('API_BASE_URL', 'http://localhost:8000')
        _auth_manager = AuthManager(api_url)
    return _auth_manager


def check_and_redirect_auth():
    """
    Check authentication and redirect if needed
    Should be called at the top of protected pages
    """
    # Temporarily bypass auth check until backend auth is implemented
    return
    
    if not is_authenticated():
        st.error("🔒 Authentication required")
        st.info("Please login to access this page")
        if st.button("Go to Login", type="primary"):
            st.switch_page("pages/0_Login.py")
        st.stop()