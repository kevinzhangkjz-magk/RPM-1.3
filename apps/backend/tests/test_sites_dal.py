import pytest
from unittest.mock import patch, MagicMock
from sqlalchemy.exc import SQLAlchemyError

from src.dal.sites import SitesRepository


class TestSitesRepository:
    """Tests for sites data access layer"""

    def setup_method(self):
        """Set up test fixtures"""
        self.sample_sites_data = [
            {
                "site_id": "SITE001",
                "site_name": "Solar Farm Alpha",
                "location": "Arizona, USA",
                "capacity_kw": 5000.0,
                "installation_date": "2023-01-15",
                "status": "active",
            },
            {
                "site_id": "SITE002",
                "site_name": "Solar Farm Beta",
                "location": "California, USA",
                "capacity_kw": 3000.0,
                "installation_date": "2023-03-20",
                "status": "active",
            },
        ]

    @patch("src.dal.sites.get_database_connection")
    def test_get_all_sites_success(self, mock_get_connection):
        """Test successful retrieval of all sites"""
        # Mock database connection and results
        mock_db_connection = MagicMock()
        mock_engine = MagicMock()
        mock_connection = MagicMock()
        mock_result = MagicMock()

        mock_get_connection.return_value = mock_db_connection
        mock_db_connection.get_engine.return_value = mock_engine
        mock_engine.connect.return_value.__enter__.return_value = mock_connection
        mock_connection.execute.return_value = mock_result

        # Mock query results
        mock_result.keys.return_value = [
            "site_id",
            "site_name",
            "location",
            "capacity_kw",
            "installation_date",
            "status",
        ]
        mock_result.fetchall.return_value = [
            (
                "SITE001",
                "Solar Farm Alpha",
                "Arizona, USA",
                5000.0,
                "2023-01-15",
                "active",
            ),
            (
                "SITE002",
                "Solar Farm Beta",
                "California, USA",
                3000.0,
                "2023-03-20",
                "active",
            ),
        ]

        # Create repo after mocking
        repo = SitesRepository()

        # Execute test
        result = repo.get_all_sites()

        # Assertions
        assert len(result) == 2
        assert result[0]["site_id"] == "SITE001"
        assert result[0]["site_name"] == "Solar Farm Alpha"
        assert result[0]["location"] == "Arizona, USA"
        assert result[0]["capacity_kw"] == 5000.0
        assert result[1]["site_id"] == "SITE002"
        assert result[1]["site_name"] == "Solar Farm Beta"

        # Verify query was called
        mock_connection.execute.assert_called_once()

    @patch("src.dal.sites.get_database_connection")
    def test_get_all_sites_empty_result(self, mock_get_connection):
        """Test retrieval when no sites exist"""
        mock_db_connection = MagicMock()
        mock_engine = MagicMock()
        mock_connection = MagicMock()
        mock_result = MagicMock()

        mock_get_connection.return_value = mock_db_connection
        mock_db_connection.get_engine.return_value = mock_engine
        mock_engine.connect.return_value.__enter__.return_value = mock_connection
        mock_connection.execute.return_value = mock_result

        # Mock empty results
        mock_result.keys.return_value = []
        mock_result.fetchall.return_value = []

        repo = SitesRepository()
        result = repo.get_all_sites()

        assert result == []

    @patch("src.dal.sites.get_database_connection")
    def test_get_all_sites_database_error(self, mock_get_connection):
        """Test database error handling"""
        mock_db_connection = MagicMock()
        mock_engine = MagicMock()
        mock_connection = MagicMock()

        mock_get_connection.return_value = mock_db_connection
        mock_db_connection.get_engine.return_value = mock_engine
        mock_engine.connect.return_value.__enter__.return_value = mock_connection
        mock_connection.execute.side_effect = SQLAlchemyError("Database error")

        repo = SitesRepository()

        # Execute test and expect exception
        with pytest.raises(SQLAlchemyError):
            repo.get_all_sites()

    @patch("src.dal.sites.get_database_connection")
    def test_get_site_by_id_success(self, mock_get_connection):
        """Test successful retrieval of site by ID"""
        mock_db_connection = MagicMock()
        mock_engine = MagicMock()
        mock_connection = MagicMock()
        mock_result = MagicMock()

        mock_get_connection.return_value = mock_db_connection
        mock_db_connection.get_engine.return_value = mock_engine
        mock_engine.connect.return_value.__enter__.return_value = mock_connection
        mock_connection.execute.return_value = mock_result

        # Mock query results
        mock_result.keys.return_value = [
            "site_id",
            "site_name",
            "location",
            "capacity_kw",
            "installation_date",
            "status",
        ]
        mock_result.fetchone.return_value = (
            "SITE001",
            "Solar Farm Alpha",
            "Arizona, USA",
            5000.0,
            "2023-01-15",
            "active",
        )

        repo = SitesRepository()
        result = repo.get_site_by_id("SITE001")

        # Assertions
        assert result is not None
        assert result["site_id"] == "SITE001"
        assert result["site_name"] == "Solar Farm Alpha"
        assert result["location"] == "Arizona, USA"

        # Verify query was called with correct parameters
        mock_connection.execute.assert_called_once()
        call_args = mock_connection.execute.call_args
        assert "site_id" in call_args[0][1]
        assert call_args[0][1]["site_id"] == "SITE001"

    @patch("src.dal.sites.get_database_connection")
    def test_get_site_by_id_not_found(self, mock_get_connection):
        """Test retrieval when site doesn't exist"""
        mock_db_connection = MagicMock()
        mock_engine = MagicMock()
        mock_connection = MagicMock()
        mock_result = MagicMock()

        mock_get_connection.return_value = mock_db_connection
        mock_db_connection.get_engine.return_value = mock_engine
        mock_engine.connect.return_value.__enter__.return_value = mock_connection
        mock_connection.execute.return_value = mock_result

        # Mock no results
        mock_result.fetchone.return_value = None

        repo = SitesRepository()
        result = repo.get_site_by_id("NONEXISTENT")

        assert result is None

    @patch("src.dal.sites.get_database_connection")
    def test_get_site_by_id_database_error(self, mock_get_connection):
        """Test database error handling for get_site_by_id"""
        mock_db_connection = MagicMock()
        mock_engine = MagicMock()
        mock_connection = MagicMock()

        mock_get_connection.return_value = mock_db_connection
        mock_db_connection.get_engine.return_value = mock_engine
        mock_engine.connect.return_value.__enter__.return_value = mock_connection
        mock_connection.execute.side_effect = SQLAlchemyError("Database error")

        repo = SitesRepository()

        with pytest.raises(SQLAlchemyError):
            repo.get_site_by_id("SITE001")

    @patch("src.dal.sites.get_database_connection")
    def test_build_sites_query(self, mock_get_connection):
        """Test SQL query building for all sites"""
        mock_get_connection.return_value = MagicMock()
        repo = SitesRepository()

        query = repo._build_sites_query()

        # Verify query contains expected elements
        assert "SELECT" in query
        assert "sites" in query
        assert "status = 'active'" in query
        assert "ORDER BY site_name ASC" in query
        assert "site_id" in query
        assert "site_name" in query
        assert "location" in query
        assert "capacity_kw" in query

    @patch("src.dal.sites.get_database_connection")
    def test_build_site_by_id_query(self, mock_get_connection):
        """Test SQL query building for single site"""
        mock_get_connection.return_value = MagicMock()
        repo = SitesRepository()

        query = repo._build_site_by_id_query()

        # Verify query contains expected elements
        assert "SELECT" in query
        assert "sites" in query
        assert "WHERE site_id = :site_id" in query
        assert ":site_id" in query
