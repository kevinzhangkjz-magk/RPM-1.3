"""
Tests for refactored API client module
Fixed to handle caching properly without Streamlit decorators
"""

import pytest
import httpx
from unittest.mock import Mock, patch, MagicMock
import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from lib.api_client_refactored import APIClient, CacheManager, get_api_client


class TestCacheManager:
    """Test suite for CacheManager class"""
    
    def test_cache_init(self):
        """Test cache manager initialization"""
        cache = CacheManager(ttl=300)
        assert cache.ttl == 300
        assert len(cache.cache) == 0
    
    def test_cache_key_generation(self):
        """Test cache key generation"""
        cache = CacheManager()
        key1 = cache._get_cache_key('GET', '/api/test', param1='value1')
        key2 = cache._get_cache_key('GET', '/api/test', param1='value1')
        key3 = cache._get_cache_key('POST', '/api/test', param1='value1')
        
        assert key1 == key2  # Same parameters should generate same key
        assert key1 != key3  # Different method should generate different key
    
    def test_cache_set_and_get(self):
        """Test setting and getting cached data"""
        cache = CacheManager(ttl=300)
        test_data = {'test': 'data'}
        
        # Set data
        cache.set('GET', '/api/test', test_data)
        
        # Get data immediately
        result = cache.get('GET', '/api/test')
        assert result == test_data
    
    def test_cache_expiration(self):
        """Test cache expiration"""
        cache = CacheManager(ttl=0)  # Immediate expiration
        test_data = {'test': 'data'}
        
        cache.set('GET', '/api/test', test_data)
        
        # Data should be expired immediately
        result = cache.get('GET', '/api/test')
        assert result is None
    
    def test_cache_clear(self):
        """Test clearing cache"""
        cache = CacheManager()
        cache.set('GET', '/api/test1', {'data': 1})
        cache.set('GET', '/api/test2', {'data': 2})
        
        assert len(cache.cache) == 2
        
        cache.clear()
        assert len(cache.cache) == 0


class TestAPIClientRefactored:
    """Test suite for refactored APIClient class"""
    
    @pytest.fixture
    def cache_manager(self):
        """Create a cache manager for testing"""
        return CacheManager(ttl=300)
    
    @pytest.fixture
    def api_client(self, cache_manager):
        """Create an API client instance with test cache"""
        return APIClient(cache_manager=cache_manager)
    
    @pytest.fixture
    def mock_response(self):
        """Create a mock HTTP response"""
        response = Mock(spec=httpx.Response)
        response.status_code = 200
        response.json.return_value = {"success": True}
        response.raise_for_status = Mock()
        return response
    
    def test_init(self, api_client):
        """Test API client initialization"""
        assert api_client.base_url is not None
        assert api_client.timeout == 30
        assert 'Content-Type' in api_client.headers
        assert api_client.headers['Content-Type'] == 'application/json'
        assert api_client.cache is not None
    
    def test_set_auth_token(self, api_client):
        """Test setting authentication token"""
        token = "test_token_123"
        api_client.set_auth_token(token)
        assert 'Authorization' in api_client.headers
        assert api_client.headers['Authorization'] == f'Bearer {token}'
    
    @patch('lib.api_client_refactored.httpx.Client')
    def test_get_sites_with_cache(self, mock_client_class, api_client):
        """Test fetching sites with caching"""
        # Setup mock
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        mock_response = Mock()
        mock_response.json.return_value = {
            'sites': [
                {'site_id': 'site1', 'site_name': 'Test Site 1'},
                {'site_id': 'site2', 'site_name': 'Test Site 2'}
            ]
        }
        mock_response.raise_for_status = Mock()
        mock_client.request.return_value = mock_response
        
        # First call - should hit API
        sites1 = api_client.get_sites(use_cache=True)
        assert len(sites1) == 2
        assert mock_client.request.call_count == 1
        
        # Second call - should use cache
        sites2 = api_client.get_sites(use_cache=True)
        assert sites2 == sites1
        assert mock_client.request.call_count == 1  # No additional API call
        
        # Third call without cache - should hit API again
        sites3 = api_client.get_sites(use_cache=False)
        assert len(sites3) == 2
        assert mock_client.request.call_count == 2
    
    @patch('lib.api_client_refactored.httpx.Client')
    def test_get_site_detail(self, mock_client_class, api_client):
        """Test fetching site details"""
        # Setup mock
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        site_data = {
            'site_id': 'site1',
            'site_name': 'Test Site',
            'capacity_kw': 5000,
            'location': 'Test Location'
        }
        
        mock_response = Mock()
        mock_response.json.return_value = site_data
        mock_response.raise_for_status = Mock()
        mock_client.request.return_value = mock_response
        
        # Test
        result = api_client.get_site_detail('site1')
        
        assert result['site_id'] == 'site1'
        assert result['capacity_kw'] == 5000
        mock_client.request.assert_called_once()
    
    @patch('lib.api_client_refactored.httpx.Client')
    def test_get_site_performance(self, mock_client_class, api_client):
        """Test fetching site performance data"""
        # Setup mock
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        perf_data = {
            'performance_ratio': 95.5,
            'availability': 98.2,
            'data': [
                {'timestamp': '2024-01-01', 'power_output': 4500}
            ]
        }
        
        mock_response = Mock()
        mock_response.json.return_value = perf_data
        mock_response.raise_for_status = Mock()
        mock_client.request.return_value = mock_response
        
        # Test
        result = api_client.get_site_performance('site1', '2024-01-01', '2024-01-31')
        
        assert result['performance_ratio'] == 95.5
        assert result['availability'] == 98.2
        assert len(result['data']) == 1
    
    @patch('lib.api_client_refactored.httpx.Client')
    def test_query_ai_assistant(self, mock_client_class, api_client):
        """Test AI assistant query with input validation"""
        # Setup mock
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        ai_response = {
            'summary': 'Test response',
            'data': [{'site': 'site1', 'value': 100}],
            'chart_type': 'bar'
        }
        
        mock_response = Mock()
        mock_response.json.return_value = ai_response
        mock_response.raise_for_status = Mock()
        mock_client.request.return_value = mock_response
        
        # Test valid query
        result = api_client.query_ai_assistant("Test query")
        assert result['summary'] == 'Test response'
        assert result['chart_type'] == 'bar'
        
        # Test query validation
        with pytest.raises(ValueError):
            api_client.query_ai_assistant("")  # Empty query
        
        with pytest.raises(ValueError):
            api_client.query_ai_assistant("x" * 1001)  # Too long
    
    @patch('lib.api_client_refactored.httpx.Client')
    def test_error_handling_401(self, mock_client_class, api_client):
        """Test handling of 401 authentication error"""
        from tenacity import RetryError
        
        # Setup mock
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        mock_response = Mock()
        mock_response.status_code = 401
        error = httpx.HTTPStatusError("Unauthorized", request=Mock(), response=mock_response)
        mock_response.raise_for_status.side_effect = error
        mock_client.request.return_value = mock_response
        
        # Test - should raise RetryError after failed retries
        with pytest.raises(RetryError):
            api_client.get_sites()
    
    @patch('lib.api_client_refactored.httpx.Client')
    def test_retry_logic(self, mock_client_class, api_client):
        """Test retry logic on failures"""
        # Setup mock
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        # Create response objects
        mock_response_fail = Mock()
        mock_response_fail.raise_for_status.side_effect = httpx.RequestError("Network error")
        
        mock_response_success = Mock()
        mock_response_success.json.return_value = {'sites': []}
        mock_response_success.raise_for_status = Mock()
        
        # First two calls fail, third succeeds
        mock_client.request.side_effect = [
            mock_response_fail,
            mock_response_fail,
            mock_response_success
        ]
        
        # Test - should succeed after retries
        result = api_client.get_sites()
        assert result == []
        assert mock_client.request.call_count == 3
    
    @patch('lib.api_client_refactored.httpx.Client')
    def test_dashboard_config(self, mock_client_class, api_client):
        """Test dashboard configuration methods"""
        # Setup mock
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        config_data = {
            'widgets': ['widget1', 'widget2'],
            'layout': {'key': 'value'}
        }
        
        # Test get dashboard config
        mock_response = Mock()
        mock_response.json.return_value = config_data
        mock_response.raise_for_status = Mock()
        mock_client.request.return_value = mock_response
        
        result = api_client.get_dashboard_config('user123')
        assert result['widgets'] == ['widget1', 'widget2']
        
        # Test save dashboard config
        mock_response = Mock()
        mock_response.raise_for_status = Mock()
        mock_client.request.return_value = mock_response
        
        success = api_client.save_dashboard_config('user123', config_data)
        assert success is True
        
        # Verify cache was cleared
        assert len(api_client.cache.cache) == 0
    
    def test_cache_invalidation(self, api_client):
        """Test cache invalidation on save operations"""
        # Add some data to cache
        api_client.cache.set('GET', '/test1', {'data': 1})
        api_client.cache.set('GET', '/test2', {'data': 2})
        assert len(api_client.cache.cache) == 2
        
        # Close should clear cache
        api_client.close()
        assert len(api_client.cache.cache) == 0
    
    def test_singleton_pattern(self):
        """Test that get_api_client returns singleton"""
        client1 = get_api_client()
        client2 = get_api_client()
        assert client1 is client2  # Should be same instance


class TestWebSocketIntegration:
    """Test WebSocket-related functionality"""
    
    @pytest.fixture
    def api_client(self):
        """Create an API client for WebSocket testing"""
        return APIClient()
    
    @pytest.mark.asyncio
    async def test_websocket_connection(self, api_client):
        """Test WebSocket connection establishment"""
        # This would need actual WebSocket server or more complex mocking
        # For now, just verify the method exists
        assert hasattr(api_client, 'establish_websocket')
    
    def test_websocket_url_configuration(self, api_client):
        """Test WebSocket URL is properly configured"""
        assert api_client.ws_base_url is not None
        assert api_client.ws_base_url.startswith('ws://')


if __name__ == "__main__":
    pytest.main([__file__, '-v'])