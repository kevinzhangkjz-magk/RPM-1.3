import pytest
from datetime import datetime
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from main import app
from src.dal.skids import SkidsRepository

client = TestClient(app)


class TestSkidsAPI:
    """Test cases for Skids API endpoints"""

    @pytest.fixture
    def mock_skids_data(self):
        """Mock skids performance data"""
        return [
            {
                "skid_id": "SKID001",
                "skid_name": "Skid 01",
                "avg_actual_power": 450.5,
                "avg_expected_power": 468.2,
                "deviation_percentage": -3.8,
                "data_point_count": 1440
            },
            {
                "skid_id": "SKID002",
                "skid_name": "Skid 02",
                "avg_actual_power": 520.1,
                "avg_expected_power": 500.8,
                "deviation_percentage": 3.9,
                "data_point_count": 1440
            }
        ]

    @patch('src.api.routes.get_current_user')
    @patch.object(SkidsRepository, 'get_skids_performance_data')
    def test_get_site_skids_success(self, mock_get_data, mock_auth, mock_skids_data):
        """Test successful retrieval of site skids performance data"""
        # Setup mocks
        mock_auth.return_value = "testuser"
        mock_get_data.return_value = mock_skids_data
        
        # Make request
        response = client.get(
            "/api/sites/ASMB2/skids",
            params={
                "start_date": "2024-01-01T00:00:00Z",
                "end_date": "2024-01-31T23:59:59Z"
            },
            headers={"Authorization": "Basic dGVzdHVzZXI6dGVzdHBhc3M="}
        )
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["site_id"] == "ASMB2"
        assert len(data["skids"]) == 2
        assert data["total_count"] == 2
        assert data["skids"][0]["skid_id"] == "SKID001"
        assert data["skids"][0]["avg_actual_power"] == 450.5

    @patch('src.api.routes.get_current_user')  
    @patch.object(SkidsRepository, 'get_skids_performance_data')
    def test_get_site_skids_no_data(self, mock_get_data, mock_auth):
        """Test case when no skids data is found"""
        # Setup mocks
        mock_auth.return_value = "testuser"
        mock_get_data.return_value = []
        
        # Make request
        response = client.get(
            "/api/sites/ASMB2/skids",
            params={
                "start_date": "2024-01-01T00:00:00Z",
                "end_date": "2024-01-31T23:59:59Z"
            },
            headers={"Authorization": "Basic dGVzdHVzZXI6dGVzdHBhc3M="}
        )
        
        # Assertions
        assert response.status_code == 404
        data = response.json()
        assert data["detail"]["error"] == "NoDataFound"

    def test_get_site_skids_invalid_date_range(self):
        """Test validation error for invalid date range"""
        response = client.get(
            "/api/sites/ASMB2/skids",
            params={
                "start_date": "2024-01-31T00:00:00Z",
                "end_date": "2024-01-01T23:59:59Z"  # End before start
            },
            headers={"Authorization": "Basic dGVzdHVzZXI6dGVzdHBhc3M="}
        )
        
        # Should return validation error
        assert response.status_code == 400

    @patch('src.api.routes.get_current_user')
    @patch.object(SkidsRepository, 'get_skids_performance_data')
    def test_get_site_skids_database_error(self, mock_get_data, mock_auth):
        """Test handling of database errors"""
        # Setup mocks
        mock_auth.return_value = "testuser"
        mock_get_data.side_effect = Exception("Database connection failed")
        
        # Make request
        response = client.get(
            "/api/sites/ASMB2/skids",
            params={
                "start_date": "2024-01-01T00:00:00Z",
                "end_date": "2024-01-31T23:59:59Z"
            },
            headers={"Authorization": "Basic dGVzdHVzZXI6dGVzdHBhc3M="}
        )
        
        # Assertions
        assert response.status_code == 500
        data = response.json()
        assert data["detail"]["error"] == "InternalServerError"