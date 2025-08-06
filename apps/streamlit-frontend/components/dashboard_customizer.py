"""
Dashboard Customization System for Renewable Energy Asset Management
Provides drag-and-drop widget arrangement and persistence
"""

import streamlit as st
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
import uuid

class DashboardCustomizer:
    """
    Manages dashboard layout customization and persistence.
    """
    
    def __init__(self):
        self.available_widgets = {
            'performance_leaderboard': {
                'name': 'Performance Leaderboard',
                'icon': '🏆',
                'default_size': 'medium',
                'description': 'Top and bottom performing sites'
            },
            'active_alerts': {
                'name': 'Active Alerts',
                'icon': '🚨',
                'default_size': 'medium',
                'description': 'Critical issues and warnings'
            },
            'power_curve': {
                'name': 'Power Curve Analysis',
                'icon': '📈',
                'default_size': 'large',
                'description': 'Power generation vs irradiance'
            },
            'kpi_summary': {
                'name': 'KPI Summary',
                'icon': '📊',
                'default_size': 'small',
                'description': 'Key performance indicators'
            },
            'site_comparison': {
                'name': 'Site Comparison',
                'icon': '🔄',
                'default_size': 'large',
                'description': 'Multi-site performance comparison'
            },
            'predictive_maintenance': {
                'name': 'Predictive Maintenance',
                'icon': '🛠️',
                'default_size': 'medium',
                'description': 'AI-driven maintenance recommendations'
            },
            'financial_impact': {
                'name': 'Financial Impact',
                'icon': '💰',
                'default_size': 'medium',
                'description': 'Revenue and cost analysis'
            },
            'weather_correlation': {
                'name': 'Weather Correlation',
                'icon': '🌤️',
                'default_size': 'medium',
                'description': 'Performance vs weather patterns'
            }
        }
        
        self.dashboard_templates = {
            'executive': {
                'name': 'Executive Dashboard',
                'description': 'High-level KPIs and financial metrics',
                'widgets': ['kpi_summary', 'financial_impact', 'performance_leaderboard'],
                'layout': [[['kpi_summary']], [['financial_impact', 'performance_leaderboard']]]
            },
            'operations': {
                'name': 'Operations Dashboard',
                'description': 'Real-time monitoring and alerts',
                'widgets': ['active_alerts', 'power_curve', 'site_comparison'],
                'layout': [[['active_alerts']], [['power_curve']], [['site_comparison']]]
            },
            'maintenance': {
                'name': 'Maintenance Dashboard',
                'description': 'Predictive maintenance and equipment health',
                'widgets': ['predictive_maintenance', 'active_alerts', 'performance_leaderboard'],
                'layout': [[['predictive_maintenance', 'active_alerts']], [['performance_leaderboard']]]
            },
            'custom': {
                'name': 'Custom Dashboard',
                'description': 'Build your own dashboard',
                'widgets': [],
                'layout': []
            }
        }
    
    def initialize_dashboard(self, user_id: str) -> Dict:
        """
        Initialize dashboard configuration for a user.
        
        Args:
            user_id: User identifier
            
        Returns:
            Dashboard configuration dictionary
        """
        if 'dashboard_config' not in st.session_state:
            st.session_state.dashboard_config = {
                'user_id': user_id,
                'template': 'executive',
                'widgets': self.dashboard_templates['executive']['widgets'].copy(),
                'layout': self.dashboard_templates['executive']['layout'].copy(),
                'preferences': {
                    'refresh_interval': 300,  # 5 minutes
                    'theme': 'dark',
                    'notifications': True
                },
                'last_modified': datetime.now().isoformat()
            }
        
        return st.session_state.dashboard_config
    
    def render_customization_panel(self) -> None:
        """
        Render the dashboard customization panel.
        """
        with st.expander("⚙️ Customize Dashboard", expanded=False):
            col1, col2, col3 = st.columns([2, 2, 1])
            
            with col1:
                # Template selection
                template = st.selectbox(
                    "Dashboard Template",
                    list(self.dashboard_templates.keys()),
                    format_func=lambda x: self.dashboard_templates[x]['name'],
                    key="dashboard_template"
                )
                
                if st.button("Apply Template"):
                    self.apply_template(template)
                    st.rerun()
            
            with col2:
                # Widget selection
                available = list(self.available_widgets.keys())
                current = st.session_state.dashboard_config.get('widgets', [])
                
                selected_widgets = st.multiselect(
                    "Active Widgets",
                    available,
                    default=current,
                    format_func=lambda x: f"{self.available_widgets[x]['icon']} {self.available_widgets[x]['name']}",
                    key="widget_selection"
                )
                
                if selected_widgets != current:
                    st.session_state.dashboard_config['widgets'] = selected_widgets
            
            with col3:
                # Preferences
                st.markdown("**Preferences**")
                
                refresh = st.select_slider(
                    "Refresh",
                    options=[60, 300, 600, 1800, 3600],
                    value=st.session_state.dashboard_config['preferences']['refresh_interval'],
                    format_func=lambda x: f"{x//60}min" if x < 3600 else f"{x//3600}hr",
                    key="refresh_interval"
                )
                
                st.session_state.dashboard_config['preferences']['refresh_interval'] = refresh
                
                notifications = st.checkbox(
                    "Notifications",
                    value=st.session_state.dashboard_config['preferences']['notifications'],
                    key="notifications_enabled"
                )
                
                st.session_state.dashboard_config['preferences']['notifications'] = notifications
            
            # Layout arrangement
            st.markdown("---")
            st.markdown("**Widget Layout**")
            
            # Simple grid-based layout
            self.render_layout_editor()
            
            # Save/Load buttons
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("💾 Save Layout", use_container_width=True):
                    self.save_dashboard_config()
                    st.success("Dashboard saved!")
            
            with col2:
                if st.button("📤 Export Layout", use_container_width=True):
                    self.export_dashboard_config()
            
            with col3:
                if st.button("📥 Import Layout", use_container_width=True):
                    self.import_dashboard_config()
    
    def render_layout_editor(self) -> None:
        """
        Render a simple layout editor for widget arrangement.
        """
        widgets = st.session_state.dashboard_config.get('widgets', [])
        
        if not widgets:
            st.info("No widgets selected. Choose widgets from the dropdown above.")
            return
        
        # Create a simple grid layout
        st.markdown("Drag widgets to reorder (simplified version):")
        
        # For MVP, use a simple reorderable list
        new_order = []
        for widget in widgets:
            col1, col2 = st.columns([3, 1])
            
            with col1:
                widget_info = self.available_widgets[widget]
                st.markdown(f"{widget_info['icon']} **{widget_info['name']}**")
            
            with col2:
                # Size selector
                size = st.selectbox(
                    "Size",
                    ['small', 'medium', 'large'],
                    index=['small', 'medium', 'large'].index(widget_info['default_size']),
                    key=f"size_{widget}",
                    label_visibility="collapsed"
                )
            
            new_order.append(widget)
        
        # Update layout
        self.update_layout(new_order)
    
    def apply_template(self, template_name: str) -> None:
        """
        Apply a dashboard template.
        
        Args:
            template_name: Name of the template to apply
        """
        template = self.dashboard_templates[template_name]
        
        st.session_state.dashboard_config.update({
            'template': template_name,
            'widgets': template['widgets'].copy(),
            'layout': template['layout'].copy(),
            'last_modified': datetime.now().isoformat()
        })
    
    def update_layout(self, widget_order: List[str]) -> None:
        """
        Update the dashboard layout based on widget order.
        
        Args:
            widget_order: Ordered list of widget IDs
        """
        # Create simple row-based layout
        layout = []
        row = []
        
        for widget in widget_order:
            widget_info = self.available_widgets[widget]
            size = st.session_state.get(f"size_{widget}", widget_info['default_size'])
            
            if size == 'large' and row:
                layout.append([row])
                row = []
            
            row.append(widget)
            
            if size == 'large' or len(row) >= 2:
                layout.append([row])
                row = []
        
        if row:
            layout.append([row])
        
        st.session_state.dashboard_config['layout'] = layout
    
    def save_dashboard_config(self) -> None:
        """
        Save dashboard configuration to persistent storage.
        """
        config = st.session_state.dashboard_config
        config['last_modified'] = datetime.now().isoformat()
        
        # In production, save to database
        # For now, save to session state
        st.session_state[f"saved_dashboard_{config['user_id']}"] = config
    
    def load_dashboard_config(self, user_id: str) -> Optional[Dict]:
        """
        Load dashboard configuration for a user.
        
        Args:
            user_id: User identifier
            
        Returns:
            Dashboard configuration or None
        """
        # In production, load from database
        # For now, load from session state
        return st.session_state.get(f"saved_dashboard_{user_id}")
    
    def export_dashboard_config(self) -> None:
        """
        Export dashboard configuration as JSON.
        """
        config = st.session_state.dashboard_config
        
        # Create download button
        json_str = json.dumps(config, indent=2)
        
        st.download_button(
            label="Download Configuration",
            data=json_str,
            file_name=f"dashboard_config_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json"
        )
    
    def import_dashboard_config(self) -> None:
        """
        Import dashboard configuration from JSON.
        """
        uploaded_file = st.file_uploader(
            "Choose a configuration file",
            type=['json'],
            key="config_upload"
        )
        
        if uploaded_file is not None:
            try:
                config = json.load(uploaded_file)
                
                # Validate configuration
                if 'widgets' in config and 'layout' in config:
                    st.session_state.dashboard_config.update(config)
                    st.success("Configuration imported successfully!")
                    st.rerun()
                else:
                    st.error("Invalid configuration file")
            except Exception as e:
                st.error(f"Error importing configuration: {str(e)}")
    
    def render_dashboard(self, api_client) -> None:
        """
        Render the dashboard based on current configuration.
        
        Args:
            api_client: API client for data fetching
        """
        layout = st.session_state.dashboard_config.get('layout', [])
        
        if not layout:
            st.info("No widgets configured. Use the customization panel to add widgets.")
            return
        
        # Import widget rendering functions
        from components.ai_widgets import (
            render_performance_leaderboard,
            render_active_alerts,
            render_power_curve_widget,
            render_kpi_summary,
            render_site_comparison,
            render_predictive_maintenance
        )
        
        widget_renderers = {
            'performance_leaderboard': render_performance_leaderboard,
            'active_alerts': render_active_alerts,
            'power_curve': render_power_curve_widget,
            'kpi_summary': render_kpi_summary,
            'site_comparison': render_site_comparison,
            'predictive_maintenance': render_predictive_maintenance
        }
        
        # Render layout
        for row_config in layout:
            for row in row_config:
                if len(row) == 1:
                    # Full width widget
                    widget_id = row[0]
                    if widget_id in widget_renderers:
                        with st.container():
                            widget_renderers[widget_id](api_client)
                else:
                    # Multiple widgets in row
                    cols = st.columns(len(row))
                    for idx, widget_id in enumerate(row):
                        with cols[idx]:
                            if widget_id in widget_renderers:
                                widget_renderers[widget_id](api_client)