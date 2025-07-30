import pytest
from datetime import datetime
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from fastapi import status
import base64

from main import app
from src.models.site_performance import PerformanceDataPoint, SiteDataSummary


class TestSitePerformanceAPI:
    """Tests for site performance API endpoint"""

    def setup_method(self):
        """Set up test fixtures"""
        self.client = TestClient(app)
        self.test_site_id = "SITE001"
        self.test_start_date = "2024-01-01T00:00:00"
        self.test_end_date = "2024-01-31T23:59:59"

        # Authentication credentials
        self.valid_username = "testuser"
        self.valid_password = "testpass"
        self.invalid_username = "wronguser"
        self.invalid_password = "wrongpass"

        # Sample response data
        self.sample_performance_data = [
            {
                "timestamp": datetime(2024, 1, 15, 12, 0),
                "site_id": "SITE001",
                "poa_irradiance": 850.5,
                "actual_power": 456.2,
                "expected_power": 475.8,
                "inverter_availability": 1.0,
                "site_name": "Solar Farm Alpha",
            }
        ]

        self.sample_summary_data = {
            "data_point_count": 1440,
            "avg_actual_power": 387.5,
            "avg_expected_power": 402.1,
            "avg_poa_irradiance": 612.3,
            "first_reading": datetime(2024, 1, 1),
            "last_reading": datetime(2024, 1, 31),
        }

    def get_auth_headers(self, username: str, password: str) -> dict:
        """Helper method to create HTTP Basic Auth headers"""
        credentials = base64.b64encode(f"{username}:{password}".encode()).decode()
        return {"Authorization": f"Basic {credentials}"}

    def get_valid_auth_headers(self) -> dict:
        """Get valid authentication headers"""
        return self.get_auth_headers(self.valid_username, self.valid_password)

    def get_invalid_auth_headers(self) -> dict:
        """Get invalid authentication headers"""
        return self.get_auth_headers(self.invalid_username, self.invalid_password)

    @patch("src.core.security.settings")
    @patch("src.api.routes.SitePerformanceRepository")
    def test_get_site_performance_success(self, mock_repository_class, mock_settings):
        """Test successful retrieval of site performance data with authentication"""
        # Mock authentication settings
        mock_settings.basic_auth_username = self.valid_username
        mock_settings.basic_auth_password = self.valid_password

        # Mock repository instance
        mock_repo = MagicMock()
        mock_repository_class.return_value = mock_repo

        # Mock repository methods
        mock_repo.validate_site_exists.return_value = True
        mock_repo.get_site_performance_data.return_value = self.sample_performance_data
        mock_repo.get_site_data_summary.return_value = self.sample_summary_data

        # Make API call with authentication
        response = self.client.get(
            f"/api/sites/{self.test_site_id}/performance",
            params={"start_date": self.test_start_date, "end_date": self.test_end_date},
            headers=self.get_valid_auth_headers(),
        )

        # Assertions
        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert data["site_id"] == self.test_site_id
        assert data["site_name"] == "Solar Farm Alpha"
        assert len(data["data_points"]) == 1
        assert data["data_points"][0]["poa_irradiance"] == 850.5
        assert data["summary"]["data_point_count"] == 1440

        # Verify repository methods were called
        mock_repo.validate_site_exists.assert_called_once_with(self.test_site_id)
        mock_repo.get_site_performance_data.assert_called_once()
        mock_repo.get_site_data_summary.assert_called_once()

    @patch("src.core.security.settings")
    @patch("src.api.routes.SitePerformanceRepository")
    def test_get_site_performance_site_not_found(
        self, mock_repository_class, mock_settings
    ):
        """Test API response when site doesn't exist"""
        # Mock authentication settings
        mock_settings.basic_auth_username = self.valid_username
        mock_settings.basic_auth_password = self.valid_password

        mock_repo = MagicMock()
        mock_repository_class.return_value = mock_repo
        mock_repo.validate_site_exists.return_value = False

        response = self.client.get(
            f"/api/sites/{self.test_site_id}/performance",
            params={"start_date": self.test_start_date, "end_date": self.test_end_date},
            headers=self.get_valid_auth_headers(),
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND
        data = response.json()
        assert data["detail"]["error"] == "SiteNotFound"
        assert self.test_site_id in data["detail"]["message"]

    @patch("src.core.security.settings")
    @patch("src.api.routes.SitePerformanceRepository")
    def test_get_site_performance_no_data_found(
        self, mock_repository_class, mock_settings
    ):
        """Test API response when no data exists for site/date range"""
        # Mock authentication settings
        mock_settings.basic_auth_username = self.valid_username
        mock_settings.basic_auth_password = self.valid_password

        mock_repo = MagicMock()
        mock_repository_class.return_value = mock_repo
        mock_repo.validate_site_exists.return_value = True
        mock_repo.get_site_performance_data.return_value = []  # No data

        response = self.client.get(
            f"/api/sites/{self.test_site_id}/performance",
            params={"start_date": self.test_start_date, "end_date": self.test_end_date},
            headers=self.get_valid_auth_headers(),
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND
        data = response.json()
        assert data["detail"]["error"] == "NoDataFound"
        assert "No performance data found" in data["detail"]["message"]

    @patch("src.core.security.settings")
    def test_get_site_performance_invalid_date_range(self, mock_settings):
        """Test API response with invalid date range"""
        # Mock authentication settings
        mock_settings.basic_auth_username = self.valid_username
        mock_settings.basic_auth_password = self.valid_password

        # End date before start date
        response = self.client.get(
            f"/api/sites/{self.test_site_id}/performance",
            params={
                "start_date": self.test_end_date,  # Later date
                "end_date": self.test_start_date,  # Earlier date
            },
            headers=self.get_valid_auth_headers(),
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert data["detail"]["error"] == "ValidationError"
        assert "end_date must be after start_date" in data["detail"]["message"]

    @patch("src.core.security.settings")
    def test_get_site_performance_future_dates(self, mock_settings):
        """Test API response with future dates"""
        # Mock authentication settings
        mock_settings.basic_auth_username = self.valid_username
        mock_settings.basic_auth_password = self.valid_password

        future_date = "2030-01-01T00:00:00"

        response = self.client.get(
            f"/api/sites/{self.test_site_id}/performance",
            params={"start_date": future_date, "end_date": "2030-01-31T23:59:59"},
            headers=self.get_valid_auth_headers(),
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert data["detail"]["error"] == "ValidationError"
        assert "Date cannot be in the future" in data["detail"]["message"]

    @patch("src.core.security.settings")
    def test_get_site_performance_missing_parameters(self, mock_settings):
        """Test API response with missing required parameters"""
        # Mock authentication settings
        mock_settings.basic_auth_username = self.valid_username
        mock_settings.basic_auth_password = self.valid_password

        # Missing start_date
        response = self.client.get(
            f"/api/sites/{self.test_site_id}/performance",
            params={"end_date": self.test_end_date},
            headers=self.get_valid_auth_headers(),
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

        # Missing end_date
        response = self.client.get(
            f"/api/sites/{self.test_site_id}/performance",
            params={"start_date": self.test_start_date},
            headers=self.get_valid_auth_headers(),
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_get_site_performance_invalid_site_id(self):
        """Test API response with empty site_id"""
        response = self.client.get(
            "/api/sites//performance",  # Empty site_id
            params={"start_date": self.test_start_date, "end_date": self.test_end_date},
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    @patch("src.core.security.settings")
    @patch("src.api.routes.SitePerformanceRepository")
    def test_get_site_performance_database_error(
        self, mock_repository_class, mock_settings
    ):
        """Test API response when database error occurs"""
        # Mock authentication settings
        mock_settings.basic_auth_username = self.valid_username
        mock_settings.basic_auth_password = self.valid_password

        mock_repo = MagicMock()
        mock_repository_class.return_value = mock_repo
        mock_repo.validate_site_exists.side_effect = Exception(
            "Database connection failed"
        )

        response = self.client.get(
            f"/api/sites/{self.test_site_id}/performance",
            params={"start_date": self.test_start_date, "end_date": self.test_end_date},
            headers=self.get_valid_auth_headers(),
        )

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        data = response.json()
        assert data["detail"]["error"] == "InternalServerError"
        assert "unexpected error occurred" in data["detail"]["message"]

    @patch("src.core.security.settings")
    @patch("src.api.routes.SitePerformanceRepository")
    def test_get_site_performance_without_summary(
        self, mock_repository_class, mock_settings
    ):
        """Test API response when summary data is not available"""
        # Mock authentication settings
        mock_settings.basic_auth_username = self.valid_username
        mock_settings.basic_auth_password = self.valid_password

        mock_repo = MagicMock()
        mock_repository_class.return_value = mock_repo

        mock_repo.validate_site_exists.return_value = True
        mock_repo.get_site_performance_data.return_value = self.sample_performance_data
        mock_repo.get_site_data_summary.return_value = None  # No summary

        response = self.client.get(
            f"/api/sites/{self.test_site_id}/performance",
            params={"start_date": self.test_start_date, "end_date": self.test_end_date},
            headers=self.get_valid_auth_headers(),
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["summary"] is None

    @patch("src.core.security.settings")
    def test_api_endpoint_url_structure(self, mock_settings):
        """Test that the API endpoint follows the correct URL structure"""
        # Mock authentication settings
        mock_settings.basic_auth_username = self.valid_username
        mock_settings.basic_auth_password = self.valid_password

        # Test with valid site_id format
        with patch("src.api.routes.SitePerformanceRepository") as mock_repo_class:
            mock_repo = MagicMock()
            mock_repo_class.return_value = mock_repo
            mock_repo.validate_site_exists.return_value = False  # Will return 404

            response = self.client.get(
                "/api/sites/SITE123/performance",
                params={
                    "start_date": self.test_start_date,
                    "end_date": self.test_end_date,
                },
                headers=self.get_valid_auth_headers(),
            )

            # Should reach the endpoint (even if it returns 404 for validation)
            assert response.status_code in [
                status.HTTP_404_NOT_FOUND,
                status.HTTP_200_OK,
            ]

    @patch("src.core.security.settings")
    def test_response_model_structure(self, mock_settings):
        """Test that the API response follows the expected model structure"""
        # Mock authentication settings
        mock_settings.basic_auth_username = self.valid_username
        mock_settings.basic_auth_password = self.valid_password

        with patch("src.api.routes.SitePerformanceRepository") as mock_repo_class:
            mock_repo = MagicMock()
            mock_repo_class.return_value = mock_repo

            mock_repo.validate_site_exists.return_value = True
            mock_repo.get_site_performance_data.return_value = (
                self.sample_performance_data
            )
            mock_repo.get_site_data_summary.return_value = self.sample_summary_data

            response = self.client.get(
                f"/api/sites/{self.test_site_id}/performance",
                params={
                    "start_date": self.test_start_date,
                    "end_date": self.test_end_date,
                },
                headers=self.get_valid_auth_headers(),
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()

            # Verify response structure matches SitePerformanceResponse model
            required_fields = ["site_id", "data_points", "site_name", "summary"]
            for field in required_fields:
                assert field in data

            # Verify data_points structure
            assert isinstance(data["data_points"], list)
            if data["data_points"]:
                data_point = data["data_points"][0]
                required_dp_fields = [
                    "timestamp",
                    "site_id",
                    "poa_irradiance",
                    "actual_power",
                    "expected_power",
                    "inverter_availability",
                ]
                for field in required_dp_fields:
                    assert field in data_point

            # Verify summary structure if present
            if data["summary"]:
                summary_fields = [
                    "data_point_count",
                    "avg_actual_power",
                    "avg_expected_power",
                    "avg_poa_irradiance",
                    "first_reading",
                    "last_reading",
                ]
                for field in summary_fields:
                    assert field in data["summary"]


class TestSitePerformanceAPIAuthentication:
    """Tests for site performance API authentication"""

    def setup_method(self):
        """Set up test fixtures"""
        self.client = TestClient(app)
        self.test_site_id = "SITE001"
        self.test_start_date = "2024-01-01T00:00:00"
        self.test_end_date = "2024-01-31T23:59:59"

        # Authentication credentials
        self.valid_username = "testuser"
        self.valid_password = "testpass"
        self.invalid_username = "wronguser"
        self.invalid_password = "wrongpass"

    def get_auth_headers(self, username: str, password: str) -> dict:
        """Helper method to create HTTP Basic Auth headers"""
        credentials = base64.b64encode(f"{username}:{password}".encode()).decode()
        return {"Authorization": f"Basic {credentials}"}

    def test_no_authentication_provided(self):
        """Test API response when no authentication is provided"""
        response = self.client.get(
            f"/api/sites/{self.test_site_id}/performance",
            params={"start_date": self.test_start_date, "end_date": self.test_end_date},
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @patch("src.core.security.settings")
    def test_invalid_authentication_credentials(self, mock_settings):
        """Test API response with invalid authentication credentials"""
        mock_settings.basic_auth_username = self.valid_username
        mock_settings.basic_auth_password = self.valid_password

        response = self.client.get(
            f"/api/sites/{self.test_site_id}/performance",
            params={"start_date": self.test_start_date, "end_date": self.test_end_date},
            headers=self.get_auth_headers(self.invalid_username, self.invalid_password),
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        data = response.json()
        assert data["detail"]["error"] == "AuthenticationFailed"
        assert "Invalid username or password" in data["detail"]["message"]

    @patch("src.core.security.settings")
    def test_missing_authentication_config(self, mock_settings):
        """Test API response when authentication is not configured"""
        mock_settings.basic_auth_username = None
        mock_settings.basic_auth_password = None

        response = self.client.get(
            f"/api/sites/{self.test_site_id}/performance",
            params={"start_date": self.test_start_date, "end_date": self.test_end_date},
            headers=self.get_auth_headers(self.valid_username, self.valid_password),
        )

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        data = response.json()
        assert data["detail"]["error"] == "AuthenticationConfigurationError"

    def test_malformed_authorization_header(self):
        """Test API response with malformed authorization header"""
        response = self.client.get(
            f"/api/sites/{self.test_site_id}/performance",
            params={"start_date": self.test_start_date, "end_date": self.test_end_date},
            headers={"Authorization": "Invalid header format"},
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_empty_authorization_header(self):
        """Test API response with empty authorization header"""
        response = self.client.get(
            f"/api/sites/{self.test_site_id}/performance",
            params={"start_date": self.test_start_date, "end_date": self.test_end_date},
            headers={"Authorization": ""},
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @patch("src.core.security.settings")
    def test_partial_credentials(self, mock_settings):
        """Test API response with partial credentials"""
        mock_settings.basic_auth_username = self.valid_username
        mock_settings.basic_auth_password = self.valid_password

        # Test with only username (no password)
        invalid_credentials = base64.b64encode(
            f"{self.valid_username}:".encode()
        ).decode()
        response = self.client.get(
            f"/api/sites/{self.test_site_id}/performance",
            params={"start_date": self.test_start_date, "end_date": self.test_end_date},
            headers={"Authorization": f"Basic {invalid_credentials}"},
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
