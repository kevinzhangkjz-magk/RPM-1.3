"""
Refactored API Client for FastAPI Backend Integration
Fixed caching issues for testability
"""

import os
import httpx
import logging
from typing import Dict, List, Optional, Any, Tuple
from tenacity import retry, stop_after_attempt, wait_exponential
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv
import asyncio
import websockets
from functools import lru_cache
import hashlib
import pickle

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CacheManager:
    """Separate cache manager for testability"""
    
    def __init__(self, ttl: int = 300):
        self.cache: Dict[str, Tuple[Any, datetime]] = {}
        self.ttl = ttl
    
    def _get_cache_key(self, method: str, endpoint: str, **kwargs) -> str:
        """Generate cache key from method and parameters"""
        key_data = f"{method}:{endpoint}:{json.dumps(kwargs, sort_keys=True)}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def get(self, method: str, endpoint: str, **kwargs) -> Optional[Any]:
        """Get cached data if still valid"""
        key = self._get_cache_key(method, endpoint, **kwargs)
        
        if key in self.cache:
            data, timestamp = self.cache[key]
            if datetime.now() - timestamp < timedelta(seconds=self.ttl):
                logger.debug(f"Cache hit for {endpoint}")
                return data
            else:
                # Cache expired
                del self.cache[key]
                logger.debug(f"Cache expired for {endpoint}")
        
        return None
    
    def set(self, method: str, endpoint: str, data: Any, **kwargs) -> None:
        """Store data in cache"""
        key = self._get_cache_key(method, endpoint, **kwargs)
        self.cache[key] = (data, datetime.now())
        logger.debug(f"Cached data for {endpoint}")
    
    def clear(self) -> None:
        """Clear all cached data"""
        self.cache.clear()
        logger.info("Cache cleared")


class APIClient:
    """
    Refactored API client for communicating with FastAPI backend.
    Implements retry logic, caching, and error handling with better testability.
    """
    
    def __init__(self, cache_manager: Optional[CacheManager] = None):
        self.base_url = os.getenv('API_BASE_URL', 'http://localhost:8000')
        self.timeout = int(os.getenv('API_TIMEOUT', '30'))
        self.ws_base_url = os.getenv('WS_BASE_URL', 'ws://localhost:8000')
        self.headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        # Add Basic Auth for backend
        self.auth = ('testuser', 'testpass')  # From backend .env
        self._client = None
        self.cache = cache_manager or CacheManager()
        logger.info(f"APIClient initialized with base_url: {self.base_url}")
    
    @property
    def client(self) -> httpx.Client:
        """Get or create HTTP client."""
        if self._client is None:
            self._client = httpx.Client(
                base_url=self.base_url,
                timeout=self.timeout,
                headers=self.headers,
                auth=self.auth  # Add Basic Auth
            )
            logger.debug("HTTP client created with Basic Auth")
        return self._client
    
    def set_auth_token(self, token: str) -> None:
        """
        Set authentication token for API requests.
        
        Args:
            token: JWT authentication token
        """
        self.headers['Authorization'] = f'Bearer {token}'
        if self._client:
            self._client.headers.update(self.headers)
        logger.info("Authentication token set")
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def _make_request(self, method: str, endpoint: str, **kwargs) -> httpx.Response:
        """
        Make HTTP request with retry logic.
        
        Args:
            method: HTTP method
            endpoint: API endpoint
            **kwargs: Additional request parameters
            
        Returns:
            HTTP response
        """
        try:
            logger.info(f"Making {method} request to {endpoint}")
            response = self.client.request(method, endpoint, **kwargs)
            response.raise_for_status()
            logger.info(f"Request successful: {response.status_code}")
            return response
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error {e.response.status_code} for {endpoint}")
            if e.response.status_code == 401:
                logger.error("Authentication required")
            elif e.response.status_code == 404:
                logger.error(f"Resource not found: {endpoint}")
            else:
                logger.error(f"API error: {e.response.status_code}")
            raise
        except httpx.RequestError as e:
            logger.error(f"Network error for {endpoint}: {str(e)}")
            raise
    
    def get_sites(self, use_cache: bool = True) -> List[Dict]:
        """
        Get list of all sites with optional caching.
        
        Args:
            use_cache: Whether to use caching
            
        Returns:
            List of site dictionaries
        """
        endpoint = '/api/sites/'  # Fixed: Added trailing slash
        
        # Check cache if enabled
        if use_cache:
            cached_data = self.cache.get('GET', endpoint)
            if cached_data:
                return cached_data
        
        # Make request to actual API
        response = self._make_request('GET', endpoint)
        data = response.json()
        sites = data.get('sites', [])
        
        # Cache the result if caching enabled
        if use_cache:
            self.cache.set('GET', endpoint, sites)
        
        return sites
    
    def get_site_detail(self, site_id: str, use_cache: bool = True) -> Dict:
        """
        Get detailed information for a specific site.
        
        Args:
            site_id: Site identifier
            use_cache: Whether to use caching
            
        Returns:
            Site detail dictionary
        """
        endpoint = f'/api/sites/{site_id}/'
        
        # Check cache
        if use_cache:
            cached_data = self.cache.get('GET', endpoint)
            if cached_data:
                return cached_data
        
        response = self._make_request('GET', endpoint)
        data = response.json()
        
        # Cache result
        if use_cache:
            self.cache.set('GET', endpoint, data)
        
        return data
    
    def get_site_performance(self, site_id: str, 
                           start_date: Optional[str] = None,
                           end_date: Optional[str] = None,
                           year: Optional[int] = None,
                           month: Optional[int] = None,
                           use_cache: bool = True) -> Dict:
        """
        Get performance data for a site.
        
        Args:
            site_id: Site identifier
            start_date: Start date for data range
            end_date: End date for data range
            year: Optional year to query (defaults to current)
            month: Optional month to query (defaults to current)
            use_cache: Whether to use caching
            
        Returns:
            Performance data dictionary
        """
        endpoint = f'/api/sites/{site_id}/performance'
        params = {}
        if start_date:
            params['start_date'] = start_date
        if end_date:
            params['end_date'] = end_date
        if year:
            params['year'] = year
        if month:
            params['month'] = month
        
        # Check cache
        if use_cache:
            cached_data = self.cache.get('GET', endpoint, params=params)
            if cached_data:
                return cached_data
        
        response = self._make_request('GET', endpoint, params=params)
        data = response.json()
        
        # Cache with shorter TTL for performance data
        if use_cache:
            self.cache.set('GET', endpoint, data, params=params)
        
        return data
    
    def get_site_skids(self, site_id: str, use_cache: bool = True) -> List[Dict]:
        """
        Get skids for a specific site.
        
        Args:
            site_id: Site identifier
            use_cache: Whether to use caching
            
        Returns:
            List of skid dictionaries
        """
        endpoint = f'/api/sites/{site_id}/skids/'
        
        if use_cache:
            cached_data = self.cache.get('GET', endpoint)
            if cached_data:
                return cached_data
        
        response = self._make_request('GET', endpoint)
        data = response.json()
        skids = data.get('skids', [])
        
        if use_cache:
            self.cache.set('GET', endpoint, skids)
        
        return skids
    
    def get_site_inverters(self, site_id: str, 
                          skid_id: Optional[str] = None,
                          use_cache: bool = True) -> List[Dict]:
        """
        Get inverters for a site, optionally filtered by skid.
        
        Args:
            site_id: Site identifier
            skid_id: Optional skid identifier for filtering
            use_cache: Whether to use caching
            
        Returns:
            List of inverter dictionaries
        """
        endpoint = f'/api/sites/{site_id}/inverters/'
        params = {}
        if skid_id:
            params['skid_id'] = skid_id
        
        if use_cache:
            cached_data = self.cache.get('GET', endpoint, params=params)
            if cached_data:
                return cached_data
        
        response = self._make_request('GET', endpoint, params=params)
        data = response.json()
        inverters = data.get('inverters', [])
        
        if use_cache:
            self.cache.set('GET', endpoint, inverters, params=params)
        
        return inverters
    
    def query_ai_assistant(self, query: str) -> Dict:
        """
        Send query to AI assistant.
        
        Args:
            query: Natural language query
            
        Returns:
            AI response with summary and optional visualization data
        """
        # Validate and sanitize input
        if not query or len(query) > 1000:
            raise ValueError("Query must be between 1 and 1000 characters")
        
        # Basic input sanitization
        query = query.strip()
        
        endpoint = '/api/query/'
        payload = {'query': query}
        
        logger.info(f"Sending AI query: {query[:50]}...")
        response = self._make_request('POST', endpoint, json=payload)
        return response.json()
    
    async def establish_websocket(self, site_id: str) -> None:
        """
        Establish WebSocket connection for real-time updates.
        
        Args:
            site_id: Site to subscribe to updates for
        """
        ws_url = f"{self.ws_base_url}/ws/{site_id}"
        logger.info(f"Establishing WebSocket connection to {ws_url}")
        
        try:
            async with websockets.connect(ws_url) as websocket:
                logger.info("WebSocket connected")
                while True:
                    message = await websocket.recv()
                    data = json.loads(message)
                    logger.debug(f"Received WebSocket message: {data}")
                    
                    # Handle different message types
                    if 'performance_update' in data:
                        # Clear relevant cache entries
                        self.cache.clear()
                        logger.info("Performance update received, cache cleared")
                    
        except Exception as e:
            logger.error(f"WebSocket connection error: {str(e)}")
            raise
    
    def get_dashboard_config(self, user_id: str, use_cache: bool = True) -> Dict:
        """
        Get user's dashboard configuration.
        
        Args:
            user_id: User identifier
            use_cache: Whether to use caching
            
        Returns:
            Dashboard configuration dictionary
        """
        endpoint = f'/api/users/{user_id}/dashboard/'
        
        if use_cache:
            cached_data = self.cache.get('GET', endpoint)
            if cached_data:
                return cached_data
        
        try:
            response = self._make_request('GET', endpoint)
            data = response.json()
            
            if use_cache:
                self.cache.set('GET', endpoint, data)
            
            return data
        except:
            logger.warning(f"Failed to get dashboard config for user {user_id}")
            # Return default if not found
            return {
                'widgets': ['performance_leaderboard', 'active_alerts', 'power_curve'],
                'layout': {}
            }
    
    def save_dashboard_config(self, user_id: str, config: Dict) -> bool:
        """
        Save user's dashboard configuration.
        
        Args:
            user_id: User identifier
            config: Dashboard configuration
            
        Returns:
            Success status
        """
        endpoint = f'/api/users/{user_id}/dashboard/'
        
        try:
            response = self._make_request('PUT', endpoint, json=config)
            # Clear cache for this user's dashboard
            self.cache.clear()
            logger.info(f"Dashboard config saved for user {user_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to save dashboard config: {str(e)}")
            return False
    
    def close(self) -> None:
        """Close the HTTP client and clear cache."""
        if self._client:
            self._client.close()
            self._client = None
        self.cache.clear()
        logger.info("API client closed")


# Factory function for singleton pattern
_api_client_instance = None

def get_api_client() -> APIClient:
    """
    Get singleton API client instance.
    
    Returns:
        APIClient instance
    """
    global _api_client_instance
    if _api_client_instance is None:
        _api_client_instance = APIClient()
    
    # Check for auth token in session and apply it
    try:
        from lib.session_state_isolated import get_session_value
        token = get_session_value('api_token')
        if token and 'Authorization' not in _api_client_instance.headers:
            _api_client_instance.set_auth_token(token)
    except:
        pass  # Session not initialized yet
    
    return _api_client_instance