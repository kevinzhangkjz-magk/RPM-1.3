"""
API Client for FastAPI Backend Integration
Handles all API communication with error handling and caching
"""

import os
import httpx
import streamlit as st
from typing import Dict, List, Optional, Any
from tenacity import retry, stop_after_attempt, wait_exponential
import json
from datetime import datetime
from dotenv import load_dotenv
import asyncio
import websockets
from functools import lru_cache

# Load environment variables
load_dotenv()


class APIClient:
    """
    API client for communicating with FastAPI backend.
    Implements retry logic, caching, and error handling.
    """
    
    def __init__(self):
        self.base_url = os.getenv('API_BASE_URL', 'http://localhost:8000')
        self.timeout = int(os.getenv('API_TIMEOUT', '30'))
        self.ws_base_url = os.getenv('WS_BASE_URL', 'ws://localhost:8000')
        self.headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        self._client = None
    
    @property
    def client(self) -> httpx.Client:
        """Get or create HTTP client."""
        if self._client is None:
            self._client = httpx.Client(
                base_url=self.base_url,
                timeout=self.timeout,
                headers=self.headers
            )
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
            response = self.client.request(method, endpoint, **kwargs)
            response.raise_for_status()
            return response
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                st.error("Authentication required. Please log in.")
                raise
            elif e.response.status_code == 404:
                st.error(f"Resource not found: {endpoint}")
                raise
            else:
                st.error(f"API error: {e.response.status_code}")
                raise
        except httpx.RequestError as e:
            st.error(f"Network error: {str(e)}")
            raise
    
    @st.cache_data(ttl=300)
    def get_sites(self) -> List[Dict]:
        """
        Get list of all sites.
        
        Returns:
            List of site dictionaries
        """
        response = self._make_request('GET', '/api/sites')
        data = response.json()
        return data.get('sites', [])
    
    @st.cache_data(ttl=300)
    def get_site_detail(self, site_id: str) -> Dict:
        """
        Get detailed information for a specific site.
        
        Args:
            site_id: Site identifier
            
        Returns:
            Site detail dictionary
        """
        response = self._make_request('GET', f'/api/sites/{site_id}')
        return response.json()
    
    @st.cache_data(ttl=60)
    def get_site_performance(self, site_id: str, 
                           start_date: Optional[str] = None,
                           end_date: Optional[str] = None) -> Dict:
        """
        Get performance data for a site.
        
        Args:
            site_id: Site identifier
            start_date: Start date for data range
            end_date: End date for data range
            
        Returns:
            Performance data dictionary
        """
        params = {}
        if start_date:
            params['start_date'] = start_date
        if end_date:
            params['end_date'] = end_date
        
        response = self._make_request(
            'GET', 
            f'/api/sites/{site_id}/performance',
            params=params
        )
        return response.json()
    
    @st.cache_data(ttl=300)
    def get_site_skids(self, site_id: str) -> List[Dict]:
        """
        Get skids for a specific site.
        
        Args:
            site_id: Site identifier
            
        Returns:
            List of skid dictionaries
        """
        response = self._make_request('GET', f'/api/sites/{site_id}/skids')
        data = response.json()
        return data.get('skids', [])
    
    @st.cache_data(ttl=300)
    def get_site_inverters(self, site_id: str, skid_id: Optional[str] = None) -> List[Dict]:
        """
        Get inverters for a site, optionally filtered by skid.
        
        Args:
            site_id: Site identifier
            skid_id: Optional skid identifier for filtering
            
        Returns:
            List of inverter dictionaries
        """
        endpoint = f'/api/sites/{site_id}/inverters'
        params = {}
        if skid_id:
            params['skid_id'] = skid_id
        
        response = self._make_request('GET', endpoint, params=params)
        data = response.json()
        return data.get('inverters', [])
    
    def query_ai_assistant(self, query: str) -> Dict:
        """
        Send query to AI assistant.
        
        Args:
            query: Natural language query
            
        Returns:
            AI response with summary and optional visualization data
        """
        payload = {'query': query}
        response = self._make_request('POST', '/api/query', json=payload)
        return response.json()
    
    def query_ai_assistant_with_context(self, query: str, context: Dict) -> Dict:
        """
        Send query to AI assistant with conversational context.
        
        Args:
            query: Natural language query
            context: Conversational context including previous queries
            
        Returns:
            AI response with summary and optional visualization data
        """
        payload = {
            'query': query,
            'context': context,
            'output_format': 'detailed'
        }
        
        # Try enhanced endpoint first, fallback to standard
        try:
            response = self._make_request('POST', '/api/query/enhanced', json=payload)
            return response.json()
        except:
            # Fallback to standard endpoint
            return self.query_ai_assistant(query)
    
    async def establish_websocket(self, site_id: str) -> None:
        """
        Establish WebSocket connection for real-time updates.
        
        Args:
            site_id: Site to subscribe to updates for
        """
        ws_url = f"{self.ws_base_url}/ws/{site_id}"
        
        try:
            async with websockets.connect(ws_url) as websocket:
                while True:
                    message = await websocket.recv()
                    data = json.loads(message)
                    
                    # Update session state with real-time data
                    if 'performance_update' in data:
                        st.session_state.real_time_data = data['performance_update']
                        st.rerun()
                    
        except Exception as e:
            st.error(f"WebSocket connection error: {str(e)}")
    
    def start_real_time_updates(self, site_id: str) -> None:
        """
        Start real-time updates for a site.
        
        Args:
            site_id: Site identifier
        """
        # In production, this would run in background
        # For MVP, we'll use polling with st.rerun()
        pass
    
    def get_dashboard_config(self, user_id: str) -> Dict:
        """
        Get user's dashboard configuration.
        
        Args:
            user_id: User identifier
            
        Returns:
            Dashboard configuration dictionary
        """
        try:
            response = self._make_request('GET', f'/api/users/{user_id}/dashboard')
            return response.json()
        except:
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
        try:
            response = self._make_request(
                'PUT', 
                f'/api/users/{user_id}/dashboard',
                json=config
            )
            return True
        except:
            return False
    
    def close(self) -> None:
        """Close the HTTP client."""
        if self._client:
            self._client.close()
            self._client = None


# Singleton instance
@lru_cache(maxsize=1)
def get_api_client() -> APIClient:
    """
    Get singleton API client instance.
    
    Returns:
        APIClient instance
    """
    return APIClient()