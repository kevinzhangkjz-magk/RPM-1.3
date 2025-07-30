import pytest
from datetime import date
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from fastapi import status
import base64

from main import app
from src.models.site_performance import SiteDetails, SitesListResponse


class TestSitesAPI:
    """Tests for sites API endpoints"""

    def setup_method(self):
        """Set up test fixtures"""
        self.client = TestClient(app)

        # Authentication credentials
        self.valid_username = "testuser"
        self.valid_password = "testpass"
        self.invalid_username = "wronguser"
        self.invalid_password = "wrongpass"

        # Sample sites data
        self.sample_sites_data = [
            {
                "site_id": "SITE001",
                "site_name": "Solar Farm Alpha",
                "location": "Arizona, USA",
                "capacity_kw": 5000.0,
                "installation_date": date(2023, 1, 15),
                "status": "active",
            },
            {
                "site_id": "SITE002",
                "site_name": "Solar Farm Beta",
                "location": "California, USA",
                "capacity_kw": 3000.0,
                "installation_date": date(2023, 3, 20),
                "status": "active",
            },
        ]

    def get_auth_headers(self, username: str, password: str) -> dict:
        """Helper method to create HTTP Basic Auth headers"""
        credentials = base64.b64encode(f"{username}:{password}".encode()).decode()
        return {"Authorization": f"Basic {credentials}"}

    def get_valid_auth_headers(self) -> dict:
        """Get valid authentication headers"""
        return self.get_auth_headers(self.valid_username, self.valid_password)

    @patch("src.core.security.settings")
    @patch("src.api.routes.SitesRepository")
    def test_list_sites_success(self, mock_repository_class, mock_settings):
        """Test successful retrieval of sites list"""
        # Mock authentication settings
        mock_settings.basic_auth_username = self.valid_username
        mock_settings.basic_auth_password = self.valid_password

        # Mock repository instance
        mock_repo = MagicMock()
        mock_repository_class.return_value = mock_repo

        # Mock repository method
        mock_repo.get_all_sites.return_value = self.sample_sites_data

        # Make API call
        response = self.client.get("/api/sites/", headers=self.get_valid_auth_headers())

        # Assertions
        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert "sites" in data
        assert "total_count" in data
        assert data["total_count"] == 2
        assert len(data["sites"]) == 2

        # Check first site data
        site1 = data["sites"][0]
        assert site1["site_id"] == "SITE001"
        assert site1["site_name"] == "Solar Farm Alpha"
        assert site1["location"] == "Arizona, USA"
        assert site1["capacity_kw"] == 5000.0
        assert site1["status"] == "active"

        # Check second site data
        site2 = data["sites"][1]
        assert site2["site_id"] == "SITE002"
        assert site2["site_name"] == "Solar Farm Beta"

        # Verify repository method was called
        mock_repo.get_all_sites.assert_called_once()

    @patch("src.core.security.settings")
    @patch("src.api.routes.SitesRepository")
    def test_list_sites_empty_result(self, mock_repository_class, mock_settings):
        """Test API response when no sites exist"""
        # Mock authentication settings
        mock_settings.basic_auth_username = self.valid_username
        mock_settings.basic_auth_password = self.valid_password

        # Mock repository instance
        mock_repo = MagicMock()
        mock_repository_class.return_value = mock_repo

        # Mock empty result
        mock_repo.get_all_sites.return_value = []

        # Make API call
        response = self.client.get("/api/sites/", headers=self.get_valid_auth_headers())

        # Assertions
        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert data["total_count"] == 0
        assert len(data["sites"]) == 0

    def test_list_sites_no_authentication(self):
        """Test API response when no authentication is provided"""
        response = self.client.get("/api/sites/")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @patch("src.core.security.settings")
    def test_list_sites_invalid_authentication(self, mock_settings):
        """Test API response with invalid authentication credentials"""
        mock_settings.basic_auth_username = self.valid_username
        mock_settings.basic_auth_password = self.valid_password

        response = self.client.get(
            "/api/sites/",
            headers=self.get_auth_headers(self.invalid_username, self.invalid_password),
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        data = response.json()
        assert data["detail"]["error"] == "AuthenticationFailed"

    @patch("src.core.security.settings")
    @patch("src.api.routes.SitesRepository")
    def test_list_sites_database_error(self, mock_repository_class, mock_settings):
        """Test API response when database error occurs"""
        # Mock authentication settings
        mock_settings.basic_auth_username = self.valid_username
        mock_settings.basic_auth_password = self.valid_password

        # Mock repository instance
        mock_repo = MagicMock()
        mock_repository_class.return_value = mock_repo

        # Mock database error
        mock_repo.get_all_sites.side_effect = Exception("Database connection failed")

        # Make API call
        response = self.client.get("/api/sites/", headers=self.get_valid_auth_headers())

        # Assertions
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        data = response.json()
        assert data["detail"]["error"] == "InternalServerError"
        assert "unexpected error occurred" in data["detail"]["message"]

    @patch("src.core.security.settings")
    @patch("src.api.routes.SitesRepository")
    def test_list_sites_response_model_structure(
        self, mock_repository_class, mock_settings
    ):
        """Test that the API response follows the expected model structure"""
        # Mock authentication settings
        mock_settings.basic_auth_username = self.valid_username
        mock_settings.basic_auth_password = self.valid_password

        # Mock repository instance
        mock_repo = MagicMock()
        mock_repository_class.return_value = mock_repo
        mock_repo.get_all_sites.return_value = self.sample_sites_data

        # Make API call
        response = self.client.get("/api/sites/", headers=self.get_valid_auth_headers())

        # Assertions
        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Verify response structure matches SitesListResponse model
        required_fields = ["sites", "total_count"]
        for field in required_fields:
            assert field in data

        # Verify sites array structure
        assert isinstance(data["sites"], list)
        if data["sites"]:
            site = data["sites"][0]
            required_site_fields = [
                "site_id",
                "site_name",
                "location",
                "capacity_kw",
                "installation_date",
                "status",
            ]
            for field in required_site_fields:
                assert field in site

        # Verify total_count is integer
        assert isinstance(data["total_count"], int)
        assert data["total_count"] >= 0

    @patch("src.core.security.settings")
    @patch("src.api.routes.SitesRepository")
    def test_list_sites_data_validation(self, mock_repository_class, mock_settings):
        """Test that API properly validates and converts site data"""
        # Mock authentication settings
        mock_settings.basic_auth_username = self.valid_username
        mock_settings.basic_auth_password = self.valid_password

        # Mock repository instance
        mock_repo = MagicMock()
        mock_repository_class.return_value = mock_repo

        # Mock data with string date (should be converted)
        mock_data = [
            {
                "site_id": "SITE001",
                "site_name": "Solar Farm Alpha",
                "location": "Arizona, USA",
                "capacity_kw": 5000.0,
                "installation_date": "2023-01-15",  # String date
                "status": "active",
            }
        ]
        mock_repo.get_all_sites.return_value = mock_data

        # Make API call
        response = self.client.get("/api/sites/", headers=self.get_valid_auth_headers())

        # Assertions
        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Verify date was properly handled
        site = data["sites"][0]
        assert site["installation_date"] == "2023-01-15"

    @patch("src.core.security.settings")
    @patch("src.api.routes.SitesRepository")
    def test_list_sites_endpoint_url(self, mock_repository_class, mock_settings):
        """Test that the API endpoint is accessible at the correct URL"""
        # Mock authentication settings
        mock_settings.basic_auth_username = self.valid_username
        mock_settings.basic_auth_password = self.valid_password

        # Mock repository instance
        mock_repo = MagicMock()
        mock_repository_class.return_value = mock_repo
        mock_repo.get_all_sites.return_value = []

        # Test various URL formats
        urls_to_test = ["/api/sites/", "/api/sites"]

        for url in urls_to_test:
            response = self.client.get(url, headers=self.get_valid_auth_headers())

            # Should be successful or redirect, not 404
            assert response.status_code in [
                status.HTTP_200_OK,
                status.HTTP_307_TEMPORARY_REDIRECT,
                status.HTTP_308_PERMANENT_REDIRECT,
            ]
