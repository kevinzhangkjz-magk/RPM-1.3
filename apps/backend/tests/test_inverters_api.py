import pytest
from datetime import datetime
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from main import app
from src.dal.inverters import InvertersRepository

client = TestClient(app)


class TestInvertersAPI:
    """Test cases for Inverters API endpoints"""

    @pytest.fixture
    def mock_inverters_data(self):
        """Mock inverters performance data"""
        return [
            {
                "inverter_id": "INV001",
                "inverter_name": "Inverter 01",
                "avg_actual_power": 45.5,
                "avg_expected_power": 46.8,
                "deviation_percentage": -2.8,
                "availability": 1.0,
                "data_point_count": 1440
            },
            {
                "inverter_id": "INV002",
                "inverter_name": "Inverter 02",
                "avg_actual_power": 47.2,
                "avg_expected_power": 46.8,
                "deviation_percentage": 0.9,
                "availability": 1.0,
                "data_point_count": 1440
            }
        ]

    @patch('src.api.routes.get_current_user')
    @patch.object(InvertersRepository, 'get_inverters_performance_data')
    def test_get_skid_inverters_success(self, mock_get_data, mock_auth, mock_inverters_data):
        """Test successful retrieval of skid inverters performance data"""
        # Setup mocks
        mock_auth.return_value = "testuser"
        mock_get_data.return_value = mock_inverters_data
        
        # Make request
        response = client.get(
            "/api/skids/SKID001/inverters",
            params={
                "start_date": "2024-01-01T00:00:00Z",
                "end_date": "2024-01-31T23:59:59Z"
            },
            headers={"Authorization": "Basic dGVzdHVzZXI6dGVzdHBhc3M="}
        )
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["skid_id"] == "SKID001"
        assert len(data["inverters"]) == 2
        assert data["total_count"] == 2
        assert data["inverters"][0]["inverter_id"] == "INV001"
        assert data["inverters"][0]["avg_actual_power"] == 45.5
        assert data["inverters"][0]["availability"] == 1.0

    @patch('src.api.routes.get_current_user')
    @patch.object(InvertersRepository, 'get_inverters_performance_data')
    def test_get_skid_inverters_no_data(self, mock_get_data, mock_auth):
        """Test case when no inverters data is found"""
        # Setup mocks
        mock_auth.return_value = "testuser"
        mock_get_data.return_value = []
        
        # Make request
        response = client.get(
            "/api/skids/SKID001/inverters",
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

    def test_get_skid_inverters_invalid_date_range(self):
        """Test validation error for invalid date range"""
        response = client.get(
            "/api/skids/SKID001/inverters",
            params={
                "start_date": "2024-01-31T00:00:00Z",
                "end_date": "2024-01-01T23:59:59Z"  # End before start
            },
            headers={"Authorization": "Basic dGVzdHVzZXI6dGVzdHBhc3M="}
        )
        
        # Should return validation error
        assert response.status_code == 400

    @patch('src.api.routes.get_current_user')
    @patch.object(InvertersRepository, 'get_inverters_performance_data')
    def test_get_skid_inverters_database_error(self, mock_get_data, mock_auth):
        """Test handling of database errors"""
        # Setup mocks
        mock_auth.return_value = "testuser"
        mock_get_data.side_effect = Exception("Database connection failed")
        
        # Make request
        response = client.get(
            "/api/skids/SKID001/inverters",
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