import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch
from src.services.ai_service import AIService


@pytest.fixture
def ai_service():
    """Create an AI service instance with mocked dependencies."""
    service = AIService()
    # Mock the Repository instances
    service.sites_repo = MagicMock()
    service.performance_repo = MagicMock()
    service.skids_repo = MagicMock()
    service.inverters_repo = MagicMock()
    return service


class TestAIServiceQueryParsing:
    """Test query parsing functionality."""
    
    def test_parse_power_curve_query(self, ai_service):
        """Test parsing of power curve with underperformance query."""
        query = "Show me the power curve for SITE001 for last month and highlight periods of significant underperformance."
        question_type, params = ai_service._parse_query(query)
        
        assert question_type == 1
        assert params['site_name'] == 'SITE001'
        assert 'time_range' in params
    
    def test_parse_worst_performance_query(self, ai_service):
        """Test parsing of worst performance query."""
        query = "Which skids and inverters at SITE002 showed the worst performance against the model last week?"
        question_type, params = ai_service._parse_query(query)
        
        assert question_type == 2
        assert params['site_name'] == 'SITE002'
        assert 'time_range' in params
    
    def test_parse_inverter_power_curve_query(self, ai_service):
        """Test parsing of individual inverter power curve query."""
        query = "Generate the individual power curve for inverter INV-001 at SITE003 for the current month."
        question_type, params = ai_service._parse_query(query)
        
        assert question_type == 3
        assert params['site_name'] == 'SITE003'
        assert params['inverter_id'] == 'INV-001'
        assert 'time_range' in params
    
    def test_parse_metrics_query(self, ai_service):
        """Test parsing of RMSE and R-squared metrics query."""
        query = "What were the RMSE and R-squared values between the actual and expected power for SITE004 last month?"
        question_type, params = ai_service._parse_query(query)
        
        assert question_type == 4
        assert params['site_name'] == 'SITE004'
        assert 'time_range' in params
    
    def test_parse_comparison_query(self, ai_service):
        """Test parsing of skid comparison query."""
        query = "Compare the power curves for skid SKID-A and skid SKID-B at SITE005 for last 30 days."
        question_type, params = ai_service._parse_query(query)
        
        assert question_type == 5
        assert params['site_name'] == 'SITE005'
        assert params['skid_a'] == 'SKID-A'
        assert params['skid_b'] == 'SKID-B'
        assert 'time_range' in params


class TestAIServiceTimeRangeExtraction:
    """Test time range extraction functionality."""
    
    def test_extract_specific_month(self, ai_service):
        """Test extraction of specific month."""
        query = "Show data for January 2024"
        time_range = ai_service._extract_time_range(query)
        
        assert time_range['start_date'].month == 1
        assert time_range['start_date'].year == 2024
        assert time_range['end_date'].month == 1
        assert time_range['end_date'].year == 2024
    
    def test_extract_last_month(self, ai_service):
        """Test extraction of last month."""
        query = "Show data for last month"
        time_range = ai_service._extract_time_range(query)
        
        now = datetime.now()
        expected_month = now.month - 1 if now.month > 1 else 12
        expected_year = now.year if now.month > 1 else now.year - 1
        
        assert time_range['start_date'].month == expected_month
        assert time_range['start_date'].year == expected_year
    
    def test_extract_current_month(self, ai_service):
        """Test extraction of current month."""
        query = "Show data for this month"
        time_range = ai_service._extract_time_range(query)
        
        now = datetime.now()
        assert time_range['start_date'].month == now.month
        assert time_range['start_date'].year == now.year
        assert time_range['start_date'].day == 1
    
    def test_extract_last_n_days(self, ai_service):
        """Test extraction of last N days."""
        query = "Show data for last 30 days"
        time_range = ai_service._extract_time_range(query)
        
        now = datetime.now()
        expected_start = now - timedelta(days=30)
        
        # Check dates are approximately correct (within 1 day due to time differences)
        diff = abs((time_range['start_date'] - expected_start).days)
        assert diff <= 1


@pytest.mark.asyncio
class TestAIServiceQueryHandlers:
    """Test query handler methods."""
    
    async def test_handle_power_curve_query(self, ai_service):
        """Test power curve query handler."""
        # Mock performance data
        ai_service.performance_repo.get_site_performance_data.return_value = [
            {'poa_irradiance': 100, 'actual_power': 150, 'expected_power': 160, 'timestamp': '2024-01-01T10:00:00'},
            {'poa_irradiance': 200, 'actual_power': 250, 'expected_power': 300, 'timestamp': '2024-01-01T11:00:00'},
            {'poa_irradiance': 300, 'actual_power': 450, 'expected_power': 460, 'timestamp': '2024-01-01T12:00:00'},
        ]
        
        params = {
            'site_name': 'SITE001',
            'time_range': {
                'start_date': datetime(2024, 1, 1),
                'end_date': datetime(2024, 1, 31)
            }
        }
        
        result = await ai_service._handle_power_curve_query(params)
        
        assert 'summary' in result
        assert 'data' in result
        assert 'Power curve analysis for SITE001' in result['summary']
        assert result['chart_type'] == 'scatter'
        assert len(result['data']['data_points']) == 3
    
    async def test_handle_worst_performance_query(self, ai_service):
        """Test worst performance query handler."""
        # Mock skids data
        ai_service.skids_repo.get_skids_performance_data.return_value = [
            {'skid_id': 'SKID001', 'skid_name': 'Skid 1', 'avg_actual_power': 800, 'avg_expected_power': 1000},
            {'skid_id': 'SKID002', 'skid_name': 'Skid 2', 'avg_actual_power': 900, 'avg_expected_power': 1000},
            {'skid_id': 'SKID003', 'skid_name': 'Skid 3', 'avg_actual_power': 700, 'avg_expected_power': 1000},
        ]
        
        params = {
            'site_name': 'SITE001',
            'time_range': {
                'start_date': datetime(2024, 1, 1),
                'end_date': datetime(2024, 1, 31)
            }
        }
        
        result = await ai_service._handle_worst_performance_query(params)
        
        assert 'summary' in result
        assert 'data' in result
        assert 'Worst Performing Skids' in result['summary']
        assert result['chart_type'] == 'bar'
        assert len(result['data']['worst_skids']) <= 5
    
    async def test_handle_metrics_query(self, ai_service):
        """Test metrics query handler."""
        # Mock performance data
        ai_service.performance_repo.get_site_performance_data.return_value = [
            {'poa_irradiance': 100, 'actual_power': 150, 'expected_power': 160},
            {'poa_irradiance': 200, 'actual_power': 300, 'expected_power': 310},
            {'poa_irradiance': 300, 'actual_power': 450, 'expected_power': 460},
        ]
        
        params = {
            'site_name': 'SITE001',
            'time_range': {
                'start_date': datetime(2024, 1, 1),
                'end_date': datetime(2024, 1, 31)
            }
        }
        
        result = await ai_service._handle_metrics_query(params)
        
        assert 'summary' in result
        assert 'data' in result
        assert 'RMSE' in result['summary']
        assert 'R-squared' in result['summary']
        assert 'rmse' in result['data']
        assert 'r_squared' in result['data']
        assert result['chart_type'] is None
    
    async def test_handle_comparison_query(self, ai_service):
        """Test skid comparison query handler."""
        # Mock skids data
        ai_service.skids_repo.get_skids_performance_data.return_value = [
            {'skid_id': 'SKID-A', 'skid_name': 'Skid A', 'avg_actual_power': 225, 'avg_expected_power': 235},
            {'skid_id': 'SKID-B', 'skid_name': 'Skid B', 'avg_actual_power': 210, 'avg_expected_power': 235},
        ]
        
        params = {
            'site_name': 'SITE001',
            'skid_a': 'SKID-A',
            'skid_b': 'SKID-B',
            'time_range': {
                'start_date': datetime(2024, 1, 1),
                'end_date': datetime(2024, 1, 31)
            }
        }
        
        result = await ai_service._handle_comparison_query(params)
        
        assert 'summary' in result
        assert 'data' in result
        assert 'Power curve comparison' in result['summary']
        assert result['chart_type'] == 'multi-scatter'
        assert 'skid_a' in result['data']
        assert 'skid_b' in result['data']


@pytest.mark.asyncio
class TestAIServiceProcessQuery:
    """Test the main process_query method."""
    
    async def test_process_valid_query(self, ai_service):
        """Test processing a valid query."""
        # Mock performance data
        ai_service.performance_repo.get_site_performance_data.return_value = [
            {'poa_irradiance': 100, 'actual_power': 150, 'expected_power': 160, 'timestamp': '2024-01-01T10:00:00'},
        ]
        
        query = "What were the RMSE and R-squared values for SITE001 last month?"
        result = await ai_service.process_query(query)
        
        assert 'summary' in result
        assert 'Performance metrics for SITE001' in result['summary']
    
    async def test_process_invalid_query(self, ai_service):
        """Test processing an invalid/unrecognized query."""
        query = "What is the weather like today?"
        
        with pytest.raises(ValueError) as exc_info:
            await ai_service.process_query(query)
        
        assert "Unable to understand the query" in str(exc_info.value)
    
    async def test_process_query_missing_site(self, ai_service):
        """Test processing a query with missing site name."""
        query = "Show me the power curve for last month"
        
        with pytest.raises(ValueError) as exc_info:
            await ai_service.process_query(query)
        
        assert "Please specify a site name" in str(exc_info.value)


class TestAIServiceHelperMethods:
    """Test helper methods for better code coverage."""
    
    def test_calculate_performance_ratio(self, ai_service):
        """Test performance ratio calculation."""
        # Normal case
        ratio = ai_service._calculate_performance_ratio(90, 100)
        assert ratio == 0.9
        
        # Zero expected power case
        ratio = ai_service._calculate_performance_ratio(50, 0)
        assert ratio == 0.0
        
        # Negative values
        ratio = ai_service._calculate_performance_ratio(-10, 100)
        assert ratio == -0.1
    
    def test_format_date_range_display(self, ai_service):
        """Test date range formatting."""
        from datetime import datetime
        
        start = datetime(2024, 1, 1)
        end = datetime(2024, 1, 31)
        formatted = ai_service._format_date_range_display(start, end)
        assert formatted == "2024-01-01 to 2024-01-31"
        
        # Test with None values
        formatted = ai_service._format_date_range_display(None, None)
        assert formatted == "N/A to N/A"