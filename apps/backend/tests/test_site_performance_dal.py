import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime
from sqlalchemy.exc import SQLAlchemyError

from src.dal.site_performance import SitePerformanceRepository


class TestSitePerformanceRepository:
    """Tests for site performance data access layer"""

    def setup_method(self):
        """Set up test fixtures"""
        self.test_site_id = "SITE001"
        self.test_start_date = datetime(2024, 1, 1)
        self.test_end_date = datetime(2024, 1, 31)

    @patch("src.dal.site_performance.get_database_connection")
    def test_get_site_performance_data_success(self, mock_get_connection):
        """Test successful retrieval of site performance data"""
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
            "timestamp",
            "site_id",
            "poa_irradiance",
            "actual_power",
        ]
        mock_result.fetchall.return_value = [
            (datetime(2024, 1, 1, 12, 0), "SITE001", 800.0, 450.0),
            (datetime(2024, 1, 1, 13, 0), "SITE001", 850.0, 480.0),
        ]

        # Create repo after mocking
        repo = SitePerformanceRepository()

        # Execute test
        result = repo.get_site_performance_data(
            self.test_site_id, self.test_start_date, self.test_end_date
        )

        # Assertions
        assert len(result) == 2
        assert result[0]["site_id"] == "SITE001"
        assert result[0]["poa_irradiance"] == 800.0
        assert result[1]["actual_power"] == 480.0

        # Verify query was called with correct parameters
        mock_connection.execute.assert_called_once()
        call_args = mock_connection.execute.call_args
        assert "site_id" in call_args[0][1]
        assert call_args[0][1]["site_id"] == self.test_site_id

    @patch("src.dal.site_performance.get_database_connection")
    def test_get_site_performance_data_database_error(self, mock_get_connection):
        """Test database error handling"""
        mock_db_connection = MagicMock()
        mock_engine = MagicMock()
        mock_connection = MagicMock()

        mock_get_connection.return_value = mock_db_connection
        mock_db_connection.get_engine.return_value = mock_engine
        mock_engine.connect.return_value.__enter__.return_value = mock_connection
        mock_connection.execute.side_effect = SQLAlchemyError("Database error")

        # Create repo after mocking
        repo = SitePerformanceRepository()

        # Execute test and expect exception
        with pytest.raises(SQLAlchemyError):
            repo.get_site_performance_data(
                self.test_site_id, self.test_start_date, self.test_end_date
            )

    @patch("src.dal.site_performance.get_database_connection")
    def test_build_performance_query(self, mock_get_connection):
        """Test SQL query building"""
        mock_get_connection.return_value = MagicMock()
        repo = SitePerformanceRepository()

        query = repo._build_performance_query()

        # Verify query contains expected elements
        assert "SELECT" in query
        assert "inverter_telemetry" in query
        assert "sites" in query
        assert "inverter_availability = 1.0" in query
        assert "ORDER BY t.timestamp ASC" in query
        assert ":site_id" in query
        assert ":start_date" in query
        assert ":end_date" in query

    @patch("src.dal.site_performance.get_database_connection")
    def test_validate_site_exists_true(self, mock_get_connection):
        """Test site validation when site exists"""
        mock_db_connection = MagicMock()
        mock_engine = MagicMock()
        mock_connection = MagicMock()
        mock_result = MagicMock()

        mock_get_connection.return_value = mock_db_connection
        mock_db_connection.get_engine.return_value = mock_engine
        mock_engine.connect.return_value.__enter__.return_value = mock_connection
        mock_connection.execute.return_value = mock_result
        mock_result.fetchone.return_value = [1]  # Site exists

        # Create repo after mocking
        repo = SitePerformanceRepository()

        result = repo.validate_site_exists(self.test_site_id)

        assert result is True

    @patch("src.dal.site_performance.get_database_connection")
    def test_validate_site_exists_false(self, mock_get_connection):
        """Test site validation when site doesn't exist"""
        mock_db_connection = MagicMock()
        mock_engine = MagicMock()
        mock_connection = MagicMock()
        mock_result = MagicMock()

        mock_get_connection.return_value = mock_db_connection
        mock_db_connection.get_engine.return_value = mock_engine
        mock_engine.connect.return_value.__enter__.return_value = mock_connection
        mock_connection.execute.return_value = mock_result
        mock_result.fetchone.return_value = [0]  # Site doesn't exist

        # Create repo after mocking
        repo = SitePerformanceRepository()

        result = repo.validate_site_exists(self.test_site_id)

        assert result is False

    @patch("src.dal.site_performance.get_database_connection")
    def test_validate_site_exists_database_error(self, mock_get_connection):
        """Test site validation with database error"""
        mock_db_connection = MagicMock()
        mock_engine = MagicMock()
        mock_connection = MagicMock()

        mock_get_connection.return_value = mock_db_connection
        mock_db_connection.get_engine.return_value = mock_engine
        mock_engine.connect.return_value.__enter__.return_value = mock_connection
        mock_connection.execute.side_effect = SQLAlchemyError("Database error")

        # Create repo after mocking
        repo = SitePerformanceRepository()

        result = repo.validate_site_exists(self.test_site_id)

        assert result is False

    @patch("src.dal.site_performance.get_database_connection")
    def test_get_site_data_summary_success(self, mock_get_connection):
        """Test successful retrieval of site data summary"""
        mock_db_connection = MagicMock()
        mock_engine = MagicMock()
        mock_connection = MagicMock()
        mock_result = MagicMock()

        mock_get_connection.return_value = mock_db_connection
        mock_db_connection.get_engine.return_value = mock_engine
        mock_engine.connect.return_value.__enter__.return_value = mock_connection
        mock_connection.execute.return_value = mock_result

        # Mock summary data
        mock_result.keys.return_value = [
            "data_point_count",
            "avg_actual_power",
            "avg_expected_power",
        ]
        mock_result.fetchone.return_value = [100, 450.5, 475.2]

        # Create repo after mocking
        repo = SitePerformanceRepository()

        result = repo.get_site_data_summary(
            self.test_site_id, self.test_start_date, self.test_end_date
        )

        assert result is not None
        assert result["data_point_count"] == 100
        assert result["avg_actual_power"] == 450.5
        assert result["avg_expected_power"] == 475.2

    @patch("src.dal.site_performance.get_database_connection")
    def test_get_site_data_summary_no_data(self, mock_get_connection):
        """Test site data summary when no data exists"""
        mock_db_connection = MagicMock()
        mock_engine = MagicMock()
        mock_connection = MagicMock()
        mock_result = MagicMock()

        mock_get_connection.return_value = mock_db_connection
        mock_db_connection.get_engine.return_value = mock_engine
        mock_engine.connect.return_value.__enter__.return_value = mock_connection
        mock_connection.execute.return_value = mock_result

        # Mock no data
        mock_result.fetchone.return_value = [0, None, None]  # No data points

        # Create repo after mocking
        repo = SitePerformanceRepository()

        result = repo.get_site_data_summary(
            self.test_site_id, self.test_start_date, self.test_end_date
        )

        assert result is None
