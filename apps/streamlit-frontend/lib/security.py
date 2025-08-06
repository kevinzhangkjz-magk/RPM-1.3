"""
Security utilities for input sanitization and validation
Implements OWASP best practices for web application security
"""

import re
import html
import logging
from typing import Any, Dict, List, Optional, Union
import hashlib
import secrets
from datetime import datetime, timedelta
import jwt
from functools import wraps

logger = logging.getLogger(__name__)


class InputSanitizer:
    """Sanitize and validate user inputs to prevent security vulnerabilities"""
    
    # Regex patterns for validation
    PATTERNS = {
        'email': re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'),
        'site_id': re.compile(r'^[a-zA-Z0-9_-]{1,50}$'),
        'alphanumeric': re.compile(r'^[a-zA-Z0-9\s_-]+$'),
        'numeric': re.compile(r'^[0-9]+$'),
        'date': re.compile(r'^\d{4}-\d{2}-\d{2}$'),
        'sql_injection': re.compile(r'(\b(SELECT|INSERT|UPDATE|DELETE|DROP|UNION|CREATE|ALTER|EXEC|EXECUTE)\b)', re.IGNORECASE),
        'xss_tags': re.compile(r'<[^>]*script|<[^>]*iframe|javascript:|on\w+=', re.IGNORECASE)
    }
    
    @staticmethod
    def sanitize_html(text: str) -> str:
        """
        Escape HTML special characters to prevent XSS attacks.
        
        Args:
            text: Input text to sanitize
            
        Returns:
            Sanitized text with HTML entities escaped
        """
        if not text:
            return ""
        
        # HTML escape
        sanitized = html.escape(str(text))
        
        # Remove any remaining suspicious patterns
        if InputSanitizer.PATTERNS['xss_tags'].search(sanitized):
            logger.warning(f"Potential XSS attempt detected and blocked")
            # Remove all tags
            sanitized = re.sub(r'<[^>]+>', '', sanitized)
        
        return sanitized
    
    @staticmethod
    def sanitize_query(query: str, max_length: int = 1000) -> str:
        """
        Sanitize user queries for AI assistant.
        
        Args:
            query: User query text
            max_length: Maximum allowed length
            
        Returns:
            Sanitized query
            
        Raises:
            ValueError: If query is invalid or potentially malicious
        """
        if not query:
            raise ValueError("Query cannot be empty")
        
        # Trim and limit length
        query = query.strip()[:max_length]
        
        # Check for SQL injection patterns
        if InputSanitizer.PATTERNS['sql_injection'].search(query):
            logger.warning("Potential SQL injection attempt detected")
            # Remove SQL keywords
            query = InputSanitizer.PATTERNS['sql_injection'].sub('', query)
        
        # Escape HTML
        query = InputSanitizer.sanitize_html(query)
        
        # Remove multiple spaces
        query = re.sub(r'\s+', ' ', query)
        
        return query
    
    @staticmethod
    def validate_site_id(site_id: str) -> bool:
        """
        Validate site ID format.
        
        Args:
            site_id: Site identifier to validate
            
        Returns:
            True if valid, False otherwise
        """
        if not site_id or len(site_id) > 50:
            return False
        
        return bool(InputSanitizer.PATTERNS['site_id'].match(site_id))
    
    @staticmethod
    def validate_date_range(start_date: str, end_date: str) -> bool:
        """
        Validate date range inputs.
        
        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            
        Returns:
            True if valid date range, False otherwise
        """
        try:
            # Check format
            if not (InputSanitizer.PATTERNS['date'].match(start_date) and 
                   InputSanitizer.PATTERNS['date'].match(end_date)):
                return False
            
            # Parse dates
            start = datetime.strptime(start_date, '%Y-%m-%d')
            end = datetime.strptime(end_date, '%Y-%m-%d')
            
            # Validate range
            if start > end:
                return False
            
            # Don't allow ranges > 1 year
            if (end - start).days > 365:
                logger.warning("Date range exceeds maximum allowed (365 days)")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Date validation error: {str(e)}")
            return False
    
    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """
        Sanitize filename to prevent directory traversal attacks.
        
        Args:
            filename: Original filename
            
        Returns:
            Sanitized filename
        """
        # Remove path components
        filename = filename.replace('..', '').replace('/', '').replace('\\', '')
        
        # Keep only alphanumeric, dash, underscore, and dot
        filename = re.sub(r'[^a-zA-Z0-9._-]', '', filename)
        
        # Limit length
        if len(filename) > 100:
            name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
            filename = f"{name[:90]}.{ext}" if ext else name[:100]
        
        return filename or 'unnamed'


class RateLimiter:
    """Implement rate limiting to prevent abuse"""
    
    def __init__(self, max_requests: int = 100, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: Dict[str, List[datetime]] = {}
    
    def is_allowed(self, identifier: str) -> bool:
        """
        Check if request is allowed based on rate limit.
        
        Args:
            identifier: User or session identifier
            
        Returns:
            True if allowed, False if rate limited
        """
        now = datetime.now()
        
        # Clean old requests
        if identifier in self.requests:
            self.requests[identifier] = [
                req_time for req_time in self.requests[identifier]
                if now - req_time < timedelta(seconds=self.window_seconds)
            ]
        else:
            self.requests[identifier] = []
        
        # Check rate limit
        if len(self.requests[identifier]) >= self.max_requests:
            logger.warning(f"Rate limit exceeded for {identifier}")
            return False
        
        # Add current request
        self.requests[identifier].append(now)
        return True


class SessionSecurity:
    """Handle secure session management"""
    
    def __init__(self, secret_key: Optional[str] = None):
        self.secret_key = secret_key or secrets.token_urlsafe(32)
        self.algorithm = 'HS256'
    
    def generate_csrf_token(self) -> str:
        """
        Generate CSRF token for form protection.
        
        Returns:
            CSRF token string
        """
        return secrets.token_urlsafe(32)
    
    def verify_csrf_token(self, token: str, stored_token: str) -> bool:
        """
        Verify CSRF token.
        
        Args:
            token: Token from request
            stored_token: Token stored in session
            
        Returns:
            True if tokens match
        """
        if not token or not stored_token:
            return False
        
        # Constant-time comparison to prevent timing attacks
        return secrets.compare_digest(token, stored_token)
    
    def create_jwt_token(self, user_id: str, expires_hours: int = 24) -> str:
        """
        Create JWT token for authentication.
        
        Args:
            user_id: User identifier
            expires_hours: Token expiration time in hours
            
        Returns:
            JWT token string
        """
        payload = {
            'user_id': user_id,
            'exp': datetime.utcnow() + timedelta(hours=expires_hours),
            'iat': datetime.utcnow(),
            'jti': secrets.token_urlsafe(16)  # JWT ID for revocation
        }
        
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
    
    def verify_jwt_token(self, token: str) -> Optional[Dict]:
        """
        Verify and decode JWT token.
        
        Args:
            token: JWT token string
            
        Returns:
            Decoded payload if valid, None otherwise
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("JWT token has expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.error(f"Invalid JWT token: {str(e)}")
            return None
    
    def hash_password(self, password: str) -> str:
        """
        Hash password using strong algorithm.
        
        Args:
            password: Plain text password
            
        Returns:
            Hashed password
        """
        # Use PBKDF2 with salt
        salt = secrets.token_bytes(32)
        key = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 100000)
        return salt.hex() + key.hex()
    
    def verify_password(self, password: str, hashed: str) -> bool:
        """
        Verify password against hash.
        
        Args:
            password: Plain text password
            hashed: Stored hash
            
        Returns:
            True if password matches
        """
        try:
            salt = bytes.fromhex(hashed[:64])
            stored_key = bytes.fromhex(hashed[64:])
            new_key = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 100000)
            return secrets.compare_digest(stored_key, new_key)
        except Exception as e:
            logger.error(f"Password verification error: {str(e)}")
            return False


def require_auth(func):
    """
    Decorator to require authentication for sensitive operations.
    
    Usage:
        @require_auth
        def sensitive_function(session_state):
            # Function implementation
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        import streamlit as st
        
        # Check for authentication token in session
        if not st.session_state.get('api_token'):
            st.error("Authentication required. Please log in.")
            st.stop()
        
        # Verify token is still valid
        security = SessionSecurity()
        token_data = security.verify_jwt_token(st.session_state.api_token)
        
        if not token_data:
            st.error("Session expired. Please log in again.")
            st.session_state.api_token = None
            st.stop()
        
        return func(*args, **kwargs)
    
    return wrapper


# Global instances
input_sanitizer = InputSanitizer()
rate_limiter = RateLimiter()
session_security = SessionSecurity()