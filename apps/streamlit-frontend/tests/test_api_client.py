"""
Tests for API client module
"""

import pytest
import httpx
from unittest.mock import Mock, patch, MagicMock
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from lib.api_client import APIClient


class TestAPIClient:
    """Test suite for APIClient class"""
    
    @pytest.fixture
    def api_client(self):
        """Create an API client instance for testing"""
        return APIClient()
    
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
    
    def test_set_auth_token(self, api_client):
        """Test setting authentication token"""
        token = "test_token_123"
        api_client.set_auth_token(token)
        assert 'Authorization' in api_client.headers
        assert api_client.headers['Authorization'] == f'Bearer {token}'
    
    @patch('lib.api_client.httpx.Client')
    def test_get_sites(self, mock_client_class, api_client):
        """Test fetching sites from API"""
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
        
        # Clear cache for testing
        api_client.get_sites.clear()
        
        # Test
        sites = api_client.get_sites()
        
        assert len(sites) == 2
        assert sites[0]['site_id'] == 'site1'
        assert sites[1]['site_name'] == 'Test Site 2'
    
    @patch('lib.api_client.httpx.Client')
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
        
        # Clear cache
        api_client.get_site_detail.clear()
        
        # Test
        result = api_client.get_site_detail('site1')
        
        assert result['site_id'] == 'site1'
        assert result['capacity_kw'] == 5000
    
    @patch('lib.api_client.httpx.Client')
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
        
        # Clear cache
        api_client.get_site_performance.clear()
        
        # Test
        result = api_client.get_site_performance('site1', '2024-01-01', '2024-01-31')
        
        assert result['performance_ratio'] == 95.5
        assert result['availability'] == 98.2
        assert len(result['data']) == 1
    
    @patch('lib.api_client.httpx.Client')
    def test_query_ai_assistant(self, mock_client_class, api_client):
        """Test AI assistant query"""
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
        
        # Test
        result = api_client.query_ai_assistant("Test query")
        
        assert result['summary'] == 'Test response'
        assert result['chart_type'] == 'bar'
        assert len(result['data']) == 1
    
    @patch('lib.api_client.httpx.Client')
    def test_error_handling_401(self, mock_client_class, api_client):
        """Test handling of 401 authentication error"""
        # Setup mock
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        mock_response = Mock()
        mock_response.status_code = 401
        error = httpx.HTTPStatusError("Unauthorized", request=Mock(), response=mock_response)
        mock_response.raise_for_status.side_effect = error
        mock_client.request.return_value = mock_response
        
        # Clear cache
        api_client.get_sites.clear()
        
        # Test - should raise error
        with pytest.raises(httpx.HTTPStatusError):
            api_client.get_sites()
    
    @patch('lib.api_client.httpx.Client')
    def test_retry_logic(self, mock_client_class, api_client):
        """Test retry logic on failures"""
        # Setup mock
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        # First two calls fail, third succeeds
        mock_response_fail = Mock()
        mock_response_fail.raise_for_status.side_effect = httpx.RequestError("Network error")
        
        mock_response_success = Mock()
        mock_response_success.json.return_value = {'sites': []}
        mock_response_success.raise_for_status = Mock()
        
        mock_client.request.side_effect = [
            mock_response_fail,
            mock_response_fail,
            mock_response_success
        ]
        
        # Clear cache
        api_client.get_sites.clear()
        
        # Test - should succeed after retries
        result = api_client.get_sites()
        assert result == []
        assert mock_client.request.call_count == 3


if __name__ == "__main__":
    pytest.main([__file__])