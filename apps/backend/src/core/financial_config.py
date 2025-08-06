"""
Financial Configuration Management
Handles sensitive PPA rates and financial settings securely
"""

import os
from typing import Dict, Optional
from functools import lru_cache
import json
from pathlib import Path


class FinancialConfig:
    """
    Manages financial configuration including sensitive PPA rates.
    Loads from environment variables or secure config sources.
    """
    
    def __init__(self):
        self._default_ppa_rate = None
        self._site_ppa_rates = {}
        self._rates_loaded = False
        self._load_config()
    
    def _load_config(self) -> None:
        """Load financial configuration from environment or config file."""
        # Try to load from environment variables first (production)
        default_rate = os.getenv('DEFAULT_PPA_RATE')
        if default_rate:
            try:
                self._default_ppa_rate = float(default_rate)
            except ValueError:
                self._default_ppa_rate = 50.0  # Fallback default
        else:
            self._default_ppa_rate = 50.0
        
        # Load site-specific rates from environment
        # Format: SITE_PPA_RATES='{"assembly_2": 48.50, "highland": 52.00}'
        site_rates_json = os.getenv('SITE_PPA_RATES')
        if site_rates_json:
            try:
                self._site_ppa_rates = json.loads(site_rates_json)
            except json.JSONDecodeError:
                self._site_ppa_rates = {}
        
        # Alternative: Load from secure config file (not in repo)
        config_path = Path(os.getenv('FINANCIAL_CONFIG_PATH', '/etc/rpm/financial.json'))
        if config_path.exists():
            try:
                with open(config_path, 'r') as f:
                    config = json.load(f)
                    self._default_ppa_rate = config.get('default_ppa_rate', self._default_ppa_rate)
                    self._site_ppa_rates.update(config.get('site_ppa_rates', {}))
            except Exception:
                pass  # Use defaults if config fails
        
        self._rates_loaded = True
    
    def get_ppa_rate(self, site_id: Optional[str] = None) -> float:
        """
        Get PPA rate for a specific site or default.
        
        Args:
            site_id: Optional site identifier
            
        Returns:
            PPA rate in $/MWh
        """
        if not self._rates_loaded:
            self._load_config()
        
        if site_id and site_id.lower() in self._site_ppa_rates:
            return float(self._site_ppa_rates[site_id.lower()])
        
        return self._default_ppa_rate
    
    def get_masked_rate(self, site_id: Optional[str] = None, show_full: bool = False) -> str:
        """
        Get PPA rate for display (masked unless authorized).
        
        Args:
            site_id: Optional site identifier
            show_full: Whether to show full value (requires authorization)
            
        Returns:
            Masked or full PPA rate string
        """
        rate = self.get_ppa_rate(site_id)
        
        if show_full:
            return f"${rate:.2f}/MWh"
        else:
            # Mask the rate for security
            rate_str = f"{rate:.2f}"
            if len(rate_str) > 4:
                masked = rate_str[0] + '*' * (len(rate_str) - 3) + rate_str[-2:]
                return f"${masked}/MWh"
            else:
                return "$**.**/MWh"
    
    def get_rates_summary(self, authorized: bool = False) -> Dict:
        """
        Get summary of all PPA rates for display.
        
        Args:
            authorized: Whether user is authorized to see full rates
            
        Returns:
            Dictionary with rate information
        """
        summary = {
            'default': self.get_masked_rate(show_full=authorized),
            'sites': {},
            'rates_configured': len(self._site_ppa_rates) > 0
        }
        
        for site_id in self._site_ppa_rates:
            summary['sites'][site_id] = self.get_masked_rate(site_id, show_full=authorized)
        
        return summary
    
    def calculate_revenue_impact(self, rmse: float, operational_hours: int = 720, 
                                site_id: Optional[str] = None) -> float:
        """
        Calculate revenue impact using appropriate PPA rate.
        
        Args:
            rmse: Root Mean Square Error in MW
            operational_hours: Hours of operation (default monthly)
            site_id: Optional site for specific PPA rate
            
        Returns:
            Revenue impact in dollars
        """
        ppa_rate = self.get_ppa_rate(site_id)
        return round(rmse * operational_hours * ppa_rate, 2)


# Singleton instance
_financial_config = None

def get_financial_config() -> FinancialConfig:
    """Get or create the financial configuration singleton."""
    global _financial_config
    if _financial_config is None:
        _financial_config = FinancialConfig()
    return _financial_config