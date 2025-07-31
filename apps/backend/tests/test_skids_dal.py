import pytest
from datetime import datetime
from unittest.mock import patch, MagicMock
from sqlalchemy.exc import SQLAlchemyError

from src.dal.skids import SkidsRepository


class TestSkidsRepository:
    """Test cases for SkidsRepository DAL"""

    @pytest.fixture
    def repo(self):
        """Create repository instance"""
        return SkidsRepository()

    @pytest.fixture
    def mock_db_data(self):
        """Mock database response data"""
        return [
            {
                "skid_id": "SKID001",
                "skid_name": "SKID001",
                "avg_actual_power": 450.5,
                "avg_expected_power": 468.2,
                "deviation_percentage": -3.8,
                "data_point_count": 1440
            },
            {
                "skid_id": "SKID002", 
                "skid_name": "SKID002",
                "avg_actual_power": 520.1,
                "avg_expected_power": 500.8,
                "deviation_percentage": 3.9,
                "data_point_count": 1440
            }
        ]

    @patch('src.dal.skids.get_database_connection')
    def test_get_skids_performance_data_success(self, mock_db_conn, repo, mock_db_data):
        """Test successful retrieval of skids performance data"""
        # Setup mocks
        mock_engine = MagicMock()
        mock_connection = MagicMock()
        mock_result = MagicMock()
        
        mock_db_conn.return_value.get_engine.return_value = mock_engine
        mock_engine.connect.return_value.__enter__.return_value = mock_connection
        mock_connection.execute.return_value = mock_result
        mock_result.keys.return_value = ["skid_id", "skid_name", "avg_actual_power", "avg_expected_power", "deviation_percentage", "data_point_count"]
        mock_result.fetchall.return_value = [
            ("SKID001", "SKID001", 450.5, 468.2, -3.8, 1440),
            ("SKID002", "SKID002", 520.1, 500.8, 3.9, 1440)
        ]
        
        # Test
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 1, 31)
        result = repo.get_skids_performance_data("ASMB2", start_date, end_date)
        
        # Assertions
        assert len(result) == 2
        assert result[0]["skid_id"] == "SKID001"
        assert result[0]["avg_actual_power"] == 450.5
        assert result[1]["skid_id"] == "SKID002"
        
        # Verify query contains availability filter
        mock_connection.execute.assert_called_once()
        query_args = mock_connection.execute.call_args[0]
        assert "inverter_availability = 1" in str(query_args[0])

    @patch('src.dal.skids.get_database_connection')
    def test_get_skids_performance_data_database_error(self, mock_db_conn, repo):
        """Test handling of database errors"""
        # Setup mock to raise exception
        mock_db_conn.return_value.get_engine.side_effect = SQLAlchemyError("Connection failed")
        
        # Test
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 1, 31)
        
        with pytest.raises(SQLAlchemyError):
            repo.get_skids_performance_data("ASMB2", start_date, end_date)

    def test_build_skids_performance_query(self, repo):
        """Test SQL query building for skids performance"""
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 1, 31)
        
        query = repo._build_skids_performance_query("ASMB2", start_date, end_date)
        
        # Verify query structure
        assert "SELECT" in query
        assert "GROUP BY data.skid_id" in query
        assert "inverter_availability = 1" in query
        assert "desri_ASMB2_2024_01" in query
        assert "ORDER BY data.skid_id ASC" in query

    @patch('src.dal.skids.get_database_connection')
    def test_get_skids_performance_data_empty_result(self, mock_db_conn, repo):
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
        result = repo.get_skids_performance_data("ASMB2", start_date, end_date)
        
        # Assertions
        assert result == []
        
    def test_sql_injection_prevention(self, repo):
        """Test that SQL injection attempts are prevented"""
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 1, 31)
        
        # Test various SQL injection attempts
        malicious_site_ids = [
            "SITE001; DROP TABLE users;--",
            "SITE001' OR '1'='1",
            "SITE001/**/UNION/**/SELECT/**/1,2,3",
            "SITE001`; DELETE FROM data WHERE 1=1;--"
        ]
        
        for malicious_id in malicious_site_ids:
            with pytest.raises(ValueError) as exc_info:
                repo._build_skids_performance_query(malicious_id, start_date, end_date)
            assert "Invalid site_id format" in str(exc_info.value)