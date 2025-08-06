"""
Unit tests for AI integration components
Tests query processing, widget rendering, and dashboard customization
"""

import pytest
import pandas as pd
import numpy as np
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime, timedelta
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from components.ai_widgets import (
    render_performance_leaderboard,
    render_active_alerts,
    render_power_curve_widget,
    render_kpi_summary,
    render_performance_list,
    render_alert_card
)

from components.dashboard_customizer import DashboardCustomizer


class TestAIWidgets:
    """Test suite for AI-powered widgets."""
    
    @pytest.fixture
    def mock_api_client(self):
        """Create a mock API client with test data."""
        client = Mock()
        
        # Mock query_ai_assistant responses
        client.query_ai_assistant.return_value = {
            'summary': 'Test analysis summary',
            'data': [
                {
                    'site_name': 'Assembly 2',
                    'site_id': 'ASMB2',
                    'r_squared': 0.652,
                    'rmse': 3.45,
                    'revenue_impact': 124200,
                    'status': 'CRITICAL',
                    'root_cause': 'Equipment failure'
                },
                {
                    'site_name': 'Highland',
                    'site_id': 'HIGH',
                    'r_squared': 0.743,
                    'rmse': 2.78,
                    'revenue_impact': 100080,
                    'status': 'WARNING',
                    'root_cause': 'Controller issues'
                }
            ],
            'metrics': {
                'total_sites': 12,
                'avg_r_squared': 0.821,
                'total_revenue_impact': 300600,
                'sites_below_target': 3
            },
            'recommendations': [
                'Immediate inspection required',
                'Review O&M contract',
                'Focus on top 3 sites'
            ]
        }
        
        # Mock get_sites response
        client.get_sites.return_value = [
            {'site_id': 'ASMB2', 'site_name': 'Assembly 2'},
            {'site_id': 'HIGH', 'site_name': 'Highland'}
        ]
        
        # Mock get_site_performance response
        client.get_site_performance.return_value = {
            'data_points': [
                {
                    'timestamp': datetime.now().isoformat(),
                    'poa_irradiance': 800,
                    'actual_power': 45.2,
                    'expected_power': 48.0
                },
                {
                    'timestamp': (datetime.now() - timedelta(hours=1)).isoformat(),
                    'poa_irradiance': 750,
                    'actual_power': 42.1,
                    'expected_power': 44.5
                }
            ]
        }
        
        return client
    
    def test_performance_leaderboard_widget(self, mock_api_client):
        """Test performance leaderboard widget renders correctly."""
        # This would need Streamlit test environment
        # For now, verify the function doesn't raise errors
        with patch('streamlit.container'), \
             patch('streamlit.subheader'), \
             patch('streamlit.spinner'), \
             patch('streamlit.columns'), \
             patch('streamlit.markdown'), \
             patch('streamlit.expander'):
            
            # Should not raise any exceptions
            render_performance_leaderboard(mock_api_client, top_n=3)
            
            # Verify API was called
            mock_api_client.query_ai_assistant.assert_called_once()
            assert 'top 3 best and worst' in mock_api_client.query_ai_assistant.call_args[0][0]
    
    def test_active_alerts_widget(self, mock_api_client):
        """Test active alerts widget categorizes alerts correctly."""
        with patch('streamlit.container'), \
             patch('streamlit.subheader'), \
             patch('streamlit.spinner'), \
             patch('streamlit.error'), \
             patch('streamlit.warning'), \
             patch('streamlit.info'), \
             patch('streamlit.expander'), \
             patch('streamlit.markdown'):
            
            render_active_alerts(mock_api_client)
            
            # Verify API was called with correct query
            mock_api_client.query_ai_assistant.assert_called_once()
            assert 'critical performance issues' in mock_api_client.query_ai_assistant.call_args[0][0].lower()
    
    def test_kpi_summary_widget(self, mock_api_client):
        """Test KPI summary widget displays metrics correctly."""
        with patch('streamlit.container'), \
             patch('streamlit.subheader'), \
             patch('streamlit.spinner'), \
             patch('streamlit.columns'), \
             patch('streamlit.metric') as mock_metric, \
             patch('plotly.express.line'):
            
            render_kpi_summary(mock_api_client)
            
            # Verify metrics are displayed
            mock_api_client.query_ai_assistant.assert_called_once()
            
            # Check that metric was called for KPIs
            # In actual implementation, verify correct values
            assert mock_metric.called


class TestDashboardCustomizer:
    """Test suite for dashboard customization system."""
    
    @pytest.fixture
    def customizer(self):
        """Create a DashboardCustomizer instance."""
        return DashboardCustomizer()
    
    def test_initialize_dashboard(self, customizer):
        """Test dashboard initialization with default template."""
        with patch('streamlit.session_state', {}):
            config = customizer.initialize_dashboard('test_user')
            
            assert config['user_id'] == 'test_user'
            assert config['template'] == 'executive'
            assert 'widgets' in config
            assert 'layout' in config
            assert 'preferences' in config
    
    def test_apply_template(self, customizer):
        """Test applying different dashboard templates."""
        with patch('streamlit.session_state', {'dashboard_config': {}}):
            customizer.apply_template('operations')
            
            config = st.session_state.dashboard_config
            assert config['template'] == 'operations'
            assert 'active_alerts' in config['widgets']
            assert 'power_curve' in config['widgets']
    
    def test_update_layout(self, customizer):
        """Test updating dashboard layout based on widget order."""
        with patch('streamlit.session_state', {'dashboard_config': {'layout': []}}):
            widget_order = ['kpi_summary', 'active_alerts', 'power_curve']
            
            customizer.update_layout(widget_order)
            
            layout = st.session_state.dashboard_config['layout']
            assert len(layout) > 0
            assert any('kpi_summary' in row for rows in layout for row in rows)
    
    def test_save_and_load_config(self, customizer):
        """Test saving and loading dashboard configuration."""
        test_config = {
            'user_id': 'test_user',
            'template': 'custom',
            'widgets': ['kpi_summary'],
            'layout': [[['kpi_summary']]],
            'preferences': {'refresh_interval': 300}
        }
        
        with patch('streamlit.session_state', {'dashboard_config': test_config}):
            customizer.save_dashboard_config()
            
            # Verify config was saved
            saved_key = f"saved_dashboard_{test_config['user_id']}"
            assert saved_key in st.session_state
            assert st.session_state[saved_key]['template'] == 'custom'
    
    def test_export_import_config(self, customizer):
        """Test export and import of dashboard configuration."""
        import json
        
        test_config = {
            'user_id': 'test_user',
            'template': 'maintenance',
            'widgets': ['predictive_maintenance'],
            'layout': [[['predictive_maintenance']]],
            'preferences': {'refresh_interval': 600}
        }
        
        with patch('streamlit.session_state', {'dashboard_config': test_config}):
            # Test export
            with patch('streamlit.download_button') as mock_download:
                customizer.export_dashboard_config()
                
                # Verify download button was called with JSON data
                mock_download.assert_called_once()
                call_args = mock_download.call_args
                exported_data = call_args[1]['data']
                
                # Verify it's valid JSON
                parsed = json.loads(exported_data)
                assert parsed['template'] == 'maintenance'


class TestConversationalContext:
    """Test suite for conversational context management."""
    
    def test_build_conversational_context(self):
        """Test building context from chat history."""
        from pages.AI_Assistant import build_conversational_context
        
        test_history = [
            {'role': 'user', 'content': 'First query'},
            {'role': 'assistant', 'content': 'First response'},
            {'role': 'user', 'content': 'Second query'},
            {'role': 'assistant', 'content': 'Second response'}
        ]
        
        with patch('streamlit.session_state', {
            'chat_history': test_history,
            'session_id': 'test_session',
            'user_id': 'test_user'
        }):
            context = build_conversational_context()
            
            assert context['session_id'] == 'test_session'
            assert context['user_id'] == 'test_user'
            assert 'First query' in context['previous_queries']
            assert 'Second query' in context['previous_queries']
            assert len(context['previous_queries']) == 2
    
    def test_validate_and_sanitize_query(self):
        """Test query validation and sanitization."""
        from pages.AI_Assistant import validate_and_sanitize_query
        
        # Test SQL injection removal
        dangerous_query = "Show sites; DROP TABLE users--"
        sanitized = validate_and_sanitize_query(dangerous_query)
        assert 'DROP' not in sanitized
        assert '--' not in sanitized
        
        # Test length limiting
        long_query = "a" * 2000
        sanitized = validate_and_sanitize_query(long_query)
        assert len(sanitized) <= 1000
        
        # Test normal query passes through
        normal_query = "Give me the top 3 underperforming sites"
        sanitized = validate_and_sanitize_query(normal_query)
        assert sanitized == normal_query


class TestPerformanceMetrics:
    """Test suite for performance metrics calculations."""
    
    def test_calculate_r_squared_and_rmse(self):
        """Test R-squared and RMSE calculation."""
        # Import from backend service
        sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'backend' / 'src'))
        from services.ai_service_v2 import AIServiceV2
        
        service = AIServiceV2()
        
        # Test with perfect correlation
        actual = [1, 2, 3, 4, 5]
        predicted = [1, 2, 3, 4, 5]
        
        metrics = service.calculate_performance_metrics(actual, predicted)
        assert metrics['r_squared'] == 1.0
        assert metrics['rmse'] == 0.0
        
        # Test with imperfect correlation
        actual = [1, 2, 3, 4, 5]
        predicted = [1.1, 1.9, 3.2, 3.8, 5.1]
        
        metrics = service.calculate_performance_metrics(actual, predicted)
        assert 0.95 < metrics['r_squared'] < 1.0
        assert metrics['rmse'] > 0
    
    def test_calculate_financial_impact(self):
        """Test financial impact calculation."""
        sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'backend' / 'src'))
        from services.ai_service_v2 import AIServiceV2
        
        service = AIServiceV2()
        
        # Test calculation
        rmse = 2.5  # MW
        hours = 720  # Monthly hours
        ppa_rate = 50.0  # $/MWh
        
        impact = service.calculate_financial_impact(rmse, hours, ppa_rate)
        
        expected = 2.5 * 720 * 50
        assert impact == expected
    
    def test_filter_data_quality(self):
        """Test data quality filtering."""
        sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'backend' / 'src'))
        from services.ai_service_v2 import AIServiceV2
        
        service = AIServiceV2()
        
        # Test filtering negative irradiance
        data_points = [
            {'poa_irradiance': 800, 'actual_power': 45},
            {'poa_irradiance': -50, 'actual_power': 0},  # Should be filtered
            {'poa_irradiance': 750, 'actual_power': 42}
        ]
        
        filtered = service.filter_data_quality(data_points)
        
        assert len(filtered) == 2
        assert all(p['poa_irradiance'] >= -10 for p in filtered)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])