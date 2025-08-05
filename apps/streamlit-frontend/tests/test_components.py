"""
Tests for Streamlit components
"""

import pytest
import pandas as pd
import numpy as np
from unittest.mock import Mock, patch, MagicMock
import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from components.charts import (
    render_power_curve,
    render_performance_scatter,
    render_time_series,
    render_performance_heatmap,
    render_comparison_bar_chart
)


class TestChartComponents:
    """Test suite for chart components"""
    
    @pytest.fixture
    def sample_performance_data(self):
        """Create sample performance data for testing"""
        return {
            'data': [
                {
                    'timestamp': '2024-01-01T12:00:00',
                    'irradiance': 500,
                    'power_output': 450,
                    'expected_power': 475,
                    'availability': 100,
                    'performance_ratio': 95
                },
                {
                    'timestamp': '2024-01-01T13:00:00',
                    'irradiance': 750,
                    'power_output': 680,
                    'expected_power': 712,
                    'availability': 98,
                    'performance_ratio': 95.5
                },
                {
                    'timestamp': '2024-01-01T14:00:00',
                    'irradiance': 1000,
                    'power_output': 920,
                    'expected_power': 950,
                    'availability': 100,
                    'performance_ratio': 96.8
                }
            ],
            'performance_ratio': 95.8,
            'availability': 99.3
        }
    
    @pytest.fixture
    def sample_sites_data(self):
        """Create sample sites data for testing"""
        return [
            {
                'site_id': 'site1',
                'site_name': 'Solar Farm A',
                'performance_ratio': 96.5,
                'capacity_kw': 5000
            },
            {
                'site_id': 'site2',
                'site_name': 'Solar Farm B',
                'performance_ratio': 94.2,
                'capacity_kw': 3000
            },
            {
                'site_id': 'site3',
                'site_name': 'Solar Farm C',
                'performance_ratio': 97.8,
                'capacity_kw': 7000
            }
        ]
    
    @patch('streamlit.plotly_chart')
    @patch('streamlit.warning')
    def test_render_power_curve_with_data(self, mock_warning, mock_plotly, sample_performance_data):
        """Test power curve rendering with valid data"""
        render_power_curve(sample_performance_data, availability_filter=False)
        
        # Should call plotly_chart to render
        assert mock_plotly.called
        # Should not show warning
        assert not mock_warning.called
        
        # Get the figure that was passed to plotly_chart
        fig = mock_plotly.call_args[0][0]
        assert fig is not None
        assert len(fig.data) >= 2  # At least actual and expected traces
    
    @patch('streamlit.warning')
    def test_render_power_curve_no_data(self, mock_warning):
        """Test power curve handling with no data"""
        render_power_curve({}, availability_filter=False)
        
        # Should show warning
        assert mock_warning.called
        assert "No performance data available" in mock_warning.call_args[0][0]
    
    @patch('streamlit.plotly_chart')
    def test_render_power_curve_with_filter(self, mock_plotly, sample_performance_data):
        """Test power curve with availability filter enabled"""
        render_power_curve(sample_performance_data, availability_filter=True)
        
        assert mock_plotly.called
        fig = mock_plotly.call_args[0][0]
        
        # Should have filtered data
        assert fig is not None
    
    @patch('streamlit.plotly_chart')
    def test_render_time_series(self, mock_plotly, sample_performance_data):
        """Test time series chart rendering"""
        render_time_series(
            sample_performance_data,
            metrics=['power_output', 'performance_ratio'],
            date_range=None
        )
        
        assert mock_plotly.called
        fig = mock_plotly.call_args[0][0]
        assert fig is not None
        assert len(fig.data) == 2  # Two metrics
    
    @patch('streamlit.plotly_chart')
    def test_render_performance_heatmap(self, mock_plotly, sample_performance_data):
        """Test performance heatmap rendering"""
        # Add more data for heatmap
        data = sample_performance_data['data']
        for i in range(24):
            for j in range(7):
                data.append({
                    'timestamp': f'2024-01-0{j+1}T{i:02d}:00:00',
                    'performance_ratio': 90 + np.random.rand() * 10
                })
        
        render_performance_heatmap(
            {'data': data},
            aggregate_by='hour_day'
        )
        
        assert mock_plotly.called
        fig = mock_plotly.call_args[0][0]
        assert fig is not None
        assert fig.data[0].type == 'heatmap'
    
    @patch('streamlit.plotly_chart')
    def test_render_comparison_bar_chart(self, mock_plotly, sample_sites_data):
        """Test comparison bar chart rendering"""
        render_comparison_bar_chart(
            sample_sites_data,
            metric='performance_ratio',
            top_n=3
        )
        
        assert mock_plotly.called
        fig = mock_plotly.call_args[0][0]
        assert fig is not None
        assert fig.data[0].type == 'bar'
        assert len(fig.data[0].x) <= 3  # Top 3 sites


class TestSessionState:
    """Test suite for session state management"""
    
    @patch('streamlit.session_state', new_callable=dict)
    def test_initialize_session_state(self, mock_session_state):
        """Test session state initialization"""
        from lib.session_state import initialize_session_state
        
        initialize_session_state()
        
        # Check default values are set
        assert 'user_id' in mock_session_state
        assert 'selected_site' in mock_session_state
        assert 'dashboard_layout' in mock_session_state
        assert 'chat_history' in mock_session_state
    
    @patch('streamlit.session_state', new_callable=dict)
    def test_update_navigation_context(self, mock_session_state):
        """Test navigation context updates"""
        from lib.session_state import update_navigation_context
        
        mock_session_state['navigation_history'] = []
        
        update_navigation_context(
            site_id='site1',
            skid_id='skid1',
            inverter_id=None
        )
        
        assert mock_session_state['selected_site'] == 'site1'
        assert mock_session_state['selected_skid'] == 'skid1'
        assert len(mock_session_state['navigation_history']) == 1
    
    @patch('streamlit.session_state', new_callable=dict)
    def test_add_chat_message(self, mock_session_state):
        """Test adding chat messages"""
        from lib.session_state import add_chat_message
        
        mock_session_state['chat_history'] = []
        
        add_chat_message('user', 'Test message', {'test': 'metadata'})
        
        assert len(mock_session_state['chat_history']) == 1
        assert mock_session_state['chat_history'][0]['role'] == 'user'
        assert mock_session_state['chat_history'][0]['content'] == 'Test message'
        assert 'metadata' in mock_session_state['chat_history'][0]
    
    @patch('streamlit.session_state', new_callable=dict)
    def test_cache_data(self, mock_session_state):
        """Test data caching functionality"""
        from lib.session_state import cache_data, get_cached_data
        
        mock_session_state['cached_data'] = {}
        
        test_data = {'test': 'data'}
        cache_data('test_key', test_data, ttl=300)
        
        # Should be able to retrieve cached data
        result = get_cached_data('test_key')
        assert result == test_data


if __name__ == "__main__":
    pytest.main([__file__])