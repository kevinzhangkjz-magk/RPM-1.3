import pytest
from datetime import datetime
from unittest.mock import patch, MagicMock
from sqlalchemy.exc import SQLAlchemyError

from src.dal.inverters import InvertersRepository


class TestInvertersRepository:
    """Test cases for InvertersRepository DAL"""

    @pytest.fixture
    def repo(self):
        """Create repository instance"""
        return InvertersRepository()

    @pytest.fixture
    def mock_db_data(self):
        """Mock database response data"""
        return [
            {
                "inverter_id": "INV001",
                "inverter_name": "INV001",
                "avg_actual_power": 45.5,
                "avg_expected_power": 46.8,
                "deviation_percentage": -2.8,
                "availability": 1.0,
                "data_point_count": 1440
            },
            {
                "inverter_id": "INV002",
                "inverter_name": "INV002",
                "avg_actual_power": 47.2,
                "avg_expected_power": 46.8,
                "deviation_percentage": 0.9,
                "availability": 1.0,
                "data_point_count": 1440
            }
        ]

    @patch('src.dal.inverters.get_database_connection')
    def test_get_inverters_performance_data_success(self, mock_db_conn, repo, mock_db_data):
        """Test successful retrieval of inverters performance data"""
        # Setup mocks
        mock_engine = MagicMock()
        mock_connection = MagicMock()
        mock_result = MagicMock()
        
        mock_db_conn.return_value.get_engine.return_value = mock_engine
        mock_engine.connect.return_value.__enter__.return_value = mock_connection
        mock_connection.execute.return_value = mock_result
        mock_result.keys.return_value = ["inverter_id", "inverter_name", "avg_actual_power", "avg_expected_power", "deviation_percentage", "availability", "data_point_count"]
        mock_result.fetchall.return_value = [
            ("INV001", "INV001", 45.5, 46.8, -2.8, 1.0, 1440),
            ("INV002", "INV002", 47.2, 46.8, 0.9, 1.0, 1440)
        ]
        
        # Test
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 1, 31)
        result = repo.get_inverters_performance_data("SKID001", start_date, end_date)
        
        # Assertions
        assert len(result) == 2
        assert result[0]["inverter_id"] == "INV001"
        assert result[0]["avg_actual_power"] == 45.5
        assert result[0]["availability"] == 1.0
        assert result[1]["inverter_id"] == "INV002"
        
        # Verify query contains availability filter
        mock_connection.execute.assert_called_once()
        query_args = mock_connection.execute.call_args[0]
        assert "inverter_availability = 1" in str(query_args[0])

    @patch('src.dal.inverters.get_database_connection')
    def test_get_inverters_performance_data_database_error(self, mock_db_conn, repo):
        """Test handling of database errors"""
        # Setup mock to raise exception
        mock_db_conn.return_value.get_engine.side_effect = SQLAlchemyError("Connection failed")
        
        # Test
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 1, 31)
        
        with pytest.raises(SQLAlchemyError):
            repo.get_inverters_performance_data("SKID001", start_date, end_date)

    def test_build_inverters_performance_query(self, repo):
        """Test SQL query building for inverters performance"""
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 1, 31)
        
        query = repo._build_inverters_performance_query("SKID001", start_date, end_date)
        
        # Verify query structure
        assert "SELECT" in query
        assert "GROUP BY data.inverter_id" in query
        assert "inverter_availability = 1" in query
        assert "data.skid_id = :skid_id" in query
        assert "desri_ASMB2_2024_01" in query  # Default site extraction
        assert "ORDER BY data.inverter_id ASC" in query

    @patch('src.dal.inverters.get_database_connection')
    def test_get_inverters_performance_data_empty_result(self, mock_db_conn, repo):
        """Test handling of empty results"""
        # Setup mocks for empty result
        mock_engine = MagicMock()
        mock_connection = MagicMock()
        mock_result = MagicMock()
        
        mock_db_conn.return_value.get_engine.return_value = mock_engine
        mock_engine.connect.return_value.__enter__.return_value = mock_connection
        mock_connection.execute.return_value = mock_result
        mock_result.keys.return_value = []
        mock_result.fetchall.return_value = []
        
        # Test
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 1, 31)
        result = repo.get_inverters_performance_data("SKID001", start_date, end_date)
        
        # Assertions
        assert result == []

    def test_site_id_extraction_from_skid_id(self, repo):
        """Test extraction of site_id from skid_id"""
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 1, 31)
        
        # Test with underscore format
        query = repo._build_inverters_performance_query("SITE001_SKID001", start_date, end_date)
        assert "desri_SITE001_2024_01" in query
        
        # Test without underscore (default to ASMB2)
        query = repo._build_inverters_performance_query("SKID001", start_date, end_date)
        assert "desri_ASMB2_2024_01" in query
        
    def test_sql_injection_prevention(self, repo):
        """Test that SQL injection attempts are prevented"""
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 1, 31)
        
        # Test various SQL injection attempts
        malicious_skid_ids = [
            "SKID001; DROP TABLE users;--",
            "SKID001' OR '1'='1",
            "SKID001/**/UNION/**/SELECT/**/1,2,3",
            "SITE001_SKID001`; DELETE FROM data WHERE 1=1;--"
        ]
        
        for malicious_id in malicious_skid_ids:
            with pytest.raises(ValueError) as exc_info:
                repo._build_inverters_performance_query(malicious_id, start_date, end_date)
            assert "Invalid" in str(exc_info.value)