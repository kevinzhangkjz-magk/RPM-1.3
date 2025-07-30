import pytest
from unittest.mock import patch, MagicMock
from sqlalchemy.exc import SQLAlchemyError

from src.core.database import DatabaseConnection, get_database_connection


class TestDatabaseConnection:
    """Tests for database connection functionality"""

    def test_get_connection_string_success(self):
        """Test successful connection string generation"""
        db = DatabaseConnection()

        with patch("src.core.database.settings") as mock_settings:
            mock_settings.redshift_host = "test-host"
            mock_settings.redshift_port = 5439
            mock_settings.redshift_database = "test-db"
            mock_settings.redshift_user = "test-user"
            mock_settings.redshift_password = "test-pass"
            mock_settings.redshift_ssl = True

            connection_string = db.get_connection_string()

            expected = (
                "postgresql://test-user:test-pass@test-host:5439/"
                "test-db?sslmode=require"
            )
            assert connection_string == expected

    def test_get_connection_string_missing_params(self):
        """Test connection string generation with missing parameters"""
        db = DatabaseConnection()

        with patch("src.core.database.settings") as mock_settings:
            mock_settings.redshift_host = None
            mock_settings.redshift_database = "test-db"
            mock_settings.redshift_user = "test-user"
            mock_settings.redshift_password = "test-pass"

            with pytest.raises(
                ValueError, match="Missing required Redshift connection parameters"
            ):
                db.get_connection_string()

    def test_get_connection_string_ssl_disabled(self):
        """Test connection string with SSL disabled"""
        db = DatabaseConnection()

        with patch("src.core.database.settings") as mock_settings:
            mock_settings.redshift_host = "test-host"
            mock_settings.redshift_port = 5439
            mock_settings.redshift_database = "test-db"
            mock_settings.redshift_user = "test-user"
            mock_settings.redshift_password = "test-pass"
            mock_settings.redshift_ssl = False

            connection_string = db.get_connection_string()

            assert "sslmode=disable" in connection_string

    @patch("src.core.database.create_engine")
    def test_get_engine(self, mock_create_engine):
        """Test database engine creation"""
        mock_engine = MagicMock()
        mock_create_engine.return_value = mock_engine

        db = DatabaseConnection()

        with patch.object(
            db, "get_connection_string", return_value="test-connection-string"
        ):
            engine = db.get_engine()

            assert engine == mock_engine
            mock_create_engine.assert_called_once()

    @patch("src.core.database.create_engine")
    def test_test_connection_success(self, mock_create_engine):
        """Test successful database connection test"""
        mock_engine = MagicMock()
        mock_connection = MagicMock()
        mock_result = MagicMock()
        mock_result.fetchone.return_value = [1]
        mock_connection.execute.return_value = mock_result
        mock_engine.connect.return_value.__enter__.return_value = mock_connection
        mock_create_engine.return_value = mock_engine

        db = DatabaseConnection()

        with patch.object(
            db, "get_connection_string", return_value="test-connection-string"
        ):
            result = db.test_connection()

            assert result is True

    @patch("src.core.database.create_engine")
    def test_test_connection_failure(self, mock_create_engine):
        """Test database connection test failure"""
        mock_engine = MagicMock()
        mock_engine.connect.side_effect = SQLAlchemyError("Connection failed")
        mock_create_engine.return_value = mock_engine

        db = DatabaseConnection()

        with patch.object(
            db, "get_connection_string", return_value="test-connection-string"
        ):
            result = db.test_connection()

            assert result is False

    def test_get_database_connection(self):
        """Test global database connection getter"""
        connection = get_database_connection()
        assert isinstance(connection, DatabaseConnection)

    @patch("src.core.database.create_engine")
    def test_close_connection(self, mock_create_engine):
        """Test database connection closing"""
        mock_engine = MagicMock()
        mock_create_engine.return_value = mock_engine

        db = DatabaseConnection()

        with patch.object(
            db, "get_connection_string", return_value="test-connection-string"
        ):
            # Create engine first
            db.get_engine()

            # Close connection
            db.close()

            mock_engine.dispose.assert_called_once()
            assert db._engine is None
