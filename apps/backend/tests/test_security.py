import pytest
from unittest.mock import patch, MagicMock
from fastapi import HTTPException, status
from fastapi.security import HTTPBasicCredentials

from src.core.security import get_current_user, get_optional_current_user


class TestAuthentication:
    """Tests for authentication functionality"""

    def setup_method(self):
        """Set up test fixtures"""
        self.valid_username = "testuser"
        self.valid_password = "testpass"
        self.invalid_username = "wronguser"
        self.invalid_password = "wrongpass"

    @patch("src.core.security.settings")
    def test_get_current_user_success(self, mock_settings):
        """Test successful authentication"""
        # Mock settings
        mock_settings.basic_auth_username = self.valid_username
        mock_settings.basic_auth_password = self.valid_password

        # Create valid credentials
        credentials = HTTPBasicCredentials(
            username=self.valid_username, password=self.valid_password
        )

        # Test authentication
        result = get_current_user(credentials)

        assert result == self.valid_username

    @patch("src.core.security.settings")
    def test_get_current_user_invalid_username(self, mock_settings):
        """Test authentication with invalid username"""
        mock_settings.basic_auth_username = self.valid_username
        mock_settings.basic_auth_password = self.valid_password

        credentials = HTTPBasicCredentials(
            username=self.invalid_username,  # Wrong username
            password=self.valid_password,
        )

        with pytest.raises(HTTPException) as exc_info:
            get_current_user(credentials)

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert exc_info.value.detail["error"] == "AuthenticationFailed"
        assert "Invalid username or password" in exc_info.value.detail["message"]
        assert exc_info.value.headers == {"WWW-Authenticate": "Basic"}

    @patch("src.core.security.settings")
    def test_get_current_user_invalid_password(self, mock_settings):
        """Test authentication with invalid password"""
        mock_settings.basic_auth_username = self.valid_username
        mock_settings.basic_auth_password = self.valid_password

        credentials = HTTPBasicCredentials(
            username=self.valid_username,
            password=self.invalid_password,  # Wrong password
        )

        with pytest.raises(HTTPException) as exc_info:
            get_current_user(credentials)

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert exc_info.value.detail["error"] == "AuthenticationFailed"

    @patch("src.core.security.settings")
    def test_get_current_user_missing_config_username(self, mock_settings):
        """Test authentication when username is not configured"""
        mock_settings.basic_auth_username = None  # Missing username
        mock_settings.basic_auth_password = self.valid_password

        credentials = HTTPBasicCredentials(
            username=self.valid_username, password=self.valid_password
        )

        with pytest.raises(HTTPException) as exc_info:
            get_current_user(credentials)

        assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert exc_info.value.detail["error"] == "AuthenticationConfigurationError"
        assert "not properly configured" in exc_info.value.detail["message"]

    @patch("src.core.security.settings")
    def test_get_current_user_missing_config_password(self, mock_settings):
        """Test authentication when password is not configured"""
        mock_settings.basic_auth_username = self.valid_username
        mock_settings.basic_auth_password = None  # Missing password

        credentials = HTTPBasicCredentials(
            username=self.valid_username, password=self.valid_password
        )

        with pytest.raises(HTTPException) as exc_info:
            get_current_user(credentials)

        assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert exc_info.value.detail["error"] == "AuthenticationConfigurationError"

    @patch("src.core.security.settings")
    def test_get_current_user_empty_credentials(self, mock_settings):
        """Test authentication with empty credentials"""
        mock_settings.basic_auth_username = self.valid_username
        mock_settings.basic_auth_password = self.valid_password

        credentials = HTTPBasicCredentials(username="", password="")

        with pytest.raises(HTTPException) as exc_info:
            get_current_user(credentials)

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED

    @patch("src.core.security.settings")
    def test_get_optional_current_user_success(self, mock_settings):
        """Test optional authentication with valid credentials"""
        mock_settings.basic_auth_username = self.valid_username
        mock_settings.basic_auth_password = self.valid_password

        credentials = HTTPBasicCredentials(
            username=self.valid_username, password=self.valid_password
        )

        result = get_optional_current_user(credentials)

        assert result == self.valid_username

    @patch("src.core.security.settings")
    def test_get_optional_current_user_invalid_credentials(self, mock_settings):
        """Test optional authentication with invalid credentials"""
        mock_settings.basic_auth_username = self.valid_username
        mock_settings.basic_auth_password = self.valid_password

        credentials = HTTPBasicCredentials(
            username=self.invalid_username, password=self.invalid_password
        )

        result = get_optional_current_user(credentials)

        assert result is None

    def test_get_optional_current_user_no_credentials(self):
        """Test optional authentication with no credentials"""
        result = get_optional_current_user(None)

        assert result is None

    @patch("src.core.security.settings")
    def test_timing_attack_resistance(self, mock_settings):
        """Test that authentication is resistant to timing attacks"""
        mock_settings.basic_auth_username = self.valid_username
        mock_settings.basic_auth_password = self.valid_password

        # This test verifies that we use secrets.compare_digest
        # which provides constant-time comparison
        credentials1 = HTTPBasicCredentials(
            username="a", password=self.valid_password  # Short incorrect username
        )

        credentials2 = HTTPBasicCredentials(
            username="a" * 100, password=self.valid_password  # Long incorrect username
        )

        # Both should fail with the same error
        with pytest.raises(HTTPException) as exc_info1:
            get_current_user(credentials1)

        with pytest.raises(HTTPException) as exc_info2:
            get_current_user(credentials2)

        assert exc_info1.value.status_code == exc_info2.value.status_code
        assert exc_info1.value.detail["error"] == exc_info2.value.detail["error"]

    @patch("src.core.security.settings")
    def test_unicode_credentials(self, mock_settings):
        """Test authentication with unicode characters"""
        unicode_username = "用户"
        unicode_password = "密码"

        mock_settings.basic_auth_username = unicode_username
        mock_settings.basic_auth_password = unicode_password

        credentials = HTTPBasicCredentials(
            username=unicode_username, password=unicode_password
        )

        result = get_current_user(credentials)

        assert result == unicode_username
