"""
Financial Settings Component for Managing PPA Rates
Provides interface for viewing and updating PPA rate configuration
"""

import streamlit as st
import pandas as pd
from typing import Dict, Optional
import json
import os


class FinancialSettings:
    """Manages financial configuration including PPA rates."""
    
    def __init__(self):
        self.load_config()
    
    def load_config(self) -> None:
        """Load current financial configuration."""
        # Initialize from session state or environment
        if 'financial_config' not in st.session_state:
            st.session_state.financial_config = {
                'default_ppa_rate': float(os.getenv('DEFAULT_PPA_RATE', 50.0)),
                'site_ppa_rates': {}
            }
            
            # Try to load site-specific rates
            site_rates_json = os.getenv('SITE_PPA_RATES', '{}')
            try:
                st.session_state.financial_config['site_ppa_rates'] = json.loads(site_rates_json)
            except json.JSONDecodeError:
                st.session_state.financial_config['site_ppa_rates'] = {}
    
    def get_ppa_rate(self, site_id: Optional[str] = None) -> float:
        """
        Get PPA rate for a specific site or default.
        
        Args:
            site_id: Optional site identifier
            
        Returns:
            PPA rate in $/MWh
        """
        config = st.session_state.financial_config
        
        if site_id and site_id.lower() in config['site_ppa_rates']:
            return float(config['site_ppa_rates'][site_id.lower()])
        
        return float(config['default_ppa_rate'])
    
    def render_settings_panel(self, api_client) -> None:
        """
        Render the financial settings panel.
        
        Args:
            api_client: API client for fetching site data
        """
        st.subheader("💰 Financial Configuration")
        
        # Default PPA Rate
        st.markdown("### Default PPA Rate")
        default_rate = st.number_input(
            "Default Rate ($/MWh)",
            min_value=0.0,
            max_value=500.0,
            value=st.session_state.financial_config['default_ppa_rate'],
            step=0.50,
            help="Default Power Purchase Agreement rate for all sites"
        )
        
        if default_rate != st.session_state.financial_config['default_ppa_rate']:
            st.session_state.financial_config['default_ppa_rate'] = default_rate
            st.success(f"Default rate updated to ${default_rate:.2f}/MWh")
        
        # Site-specific rates
        st.markdown("### Site-Specific PPA Rates")
        st.markdown("Override default rate for specific sites:")
        
        # Get available sites
        try:
            sites = api_client.get_sites()
            site_names = [s['site_name'] for s in sites]
            site_ids = [s['site_id'] for s in sites]
        except:
            site_names = ['Assembly 2', 'Highland', 'Big River']
            site_ids = ['ASMB2', 'HIGH', 'BGRV']
        
        # Create a dataframe for editing
        site_rates_data = []
        for site_id, site_name in zip(site_ids, site_names):
            current_rate = st.session_state.financial_config['site_ppa_rates'].get(
                site_id.lower(),
                st.session_state.financial_config['default_ppa_rate']
            )
            site_rates_data.append({
                'Site': site_name,
                'Site ID': site_id,
                'PPA Rate ($/MWh)': current_rate,
                'Use Default': site_id.lower() not in st.session_state.financial_config['site_ppa_rates']
            })
        
        df = pd.DataFrame(site_rates_data)
        
        # Display editable table
        edited_df = st.data_editor(
            df,
            column_config={
                'Site': st.column_config.TextColumn('Site', disabled=True),
                'Site ID': st.column_config.TextColumn('Site ID', disabled=True),
                'PPA Rate ($/MWh)': st.column_config.NumberColumn(
                    'PPA Rate ($/MWh)',
                    min_value=0.0,
                    max_value=500.0,
                    step=0.50,
                    format="$%.2f"
                ),
                'Use Default': st.column_config.CheckboxColumn('Use Default Rate')
            },
            use_container_width=True,
            hide_index=True
        )
        
        # Update configuration based on edits
        if st.button("💾 Save Site Rates", type="primary"):
            new_site_rates = {}
            for _, row in edited_df.iterrows():
                if not row['Use Default']:
                    site_id = row['Site ID'].lower()
                    rate = float(row['PPA Rate ($/MWh)'])
                    if rate != st.session_state.financial_config['default_ppa_rate']:
                        new_site_rates[site_id] = rate
            
            st.session_state.financial_config['site_ppa_rates'] = new_site_rates
            st.success("Site-specific rates saved successfully!")
            
            # Show summary
            st.markdown("#### Current Configuration:")
            st.json(st.session_state.financial_config)
        
        # Export/Import configuration
        st.markdown("### Configuration Management")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📤 Export Configuration"):
                config_json = json.dumps(st.session_state.financial_config, indent=2)
                st.download_button(
                    "Download Config",
                    data=config_json,
                    file_name="ppa_rates_config.json",
                    mime="application/json"
                )
        
        with col2:
            uploaded_file = st.file_uploader(
                "📥 Import Configuration",
                type=['json'],
                key="ppa_config_upload"
            )
            
            if uploaded_file:
                try:
                    config = json.load(uploaded_file)
                    if 'default_ppa_rate' in config:
                        st.session_state.financial_config = config
                        st.success("Configuration imported successfully!")
                        st.rerun()
                except Exception as e:
                    st.error(f"Error importing configuration: {str(e)}")
        
        # Show revenue impact examples
        st.markdown("### Revenue Impact Calculator")
        st.markdown("See how PPA rates affect revenue calculations:")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            test_rmse = st.number_input("RMSE (MW)", value=2.5, min_value=0.0, step=0.1)
        
        with col2:
            test_hours = st.number_input("Hours", value=720, min_value=1, step=1)
        
        with col3:
            test_site = st.selectbox("Site", ["Default"] + site_names)
        
        # Calculate impact
        if test_site == "Default":
            rate = st.session_state.financial_config['default_ppa_rate']
            site_id = None
        else:
            idx = site_names.index(test_site)
            site_id = site_ids[idx].lower()
            rate = self.get_ppa_rate(site_id)
        
        revenue_impact = test_rmse * test_hours * rate
        
        st.info(f"""
        **Calculation:**
        - RMSE: {test_rmse:.2f} MW
        - Hours: {test_hours}
        - PPA Rate: ${rate:.2f}/MWh
        - **Revenue Impact: ${revenue_impact:,.2f}**
        """)


def render_financial_settings(api_client) -> None:
    """
    Render the financial settings interface.
    
    Args:
        api_client: API client for fetching site data
    """
    settings = FinancialSettings()
    settings.render_settings_panel(api_client)