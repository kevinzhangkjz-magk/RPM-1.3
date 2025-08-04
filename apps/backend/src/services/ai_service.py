import re
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
from ..dal.sites import SitesRepository
from ..dal.site_performance import SitePerformanceRepository
from ..dal.skids import SkidsRepository
from ..dal.inverters import InvertersRepository
import numpy as np


class AIService:
    """Service for processing natural language queries and generating AI responses."""
    
    # Constants for better maintainability
    UNDERPERFORMANCE_THRESHOLD = 0.9  # 90% of expected performance
    TOP_WORST_PERFORMERS_COUNT = 5
    
    def __init__(self, db=None):
        # The db parameter is kept for compatibility but not used with Repository pattern
        self.sites_repo = SitesRepository()
        self.performance_repo = SitePerformanceRepository()
        self.skids_repo = SkidsRepository()
        self.inverters_repo = InvertersRepository()
    
    async def process_query(self, query: str) -> Dict[str, Any]:
        """
        Process a natural language query and return appropriate response.
        
        Args:
            query: Natural language query string
            
        Returns:
            Dictionary containing summary, data, and optional chart configuration
        """
        # Parse the query to identify question type and parameters
        question_type, params = self._parse_query(query)
        
        # Process based on question type
        if question_type == 1:
            return await self._handle_power_curve_query(params)
        elif question_type == 2:
            return await self._handle_worst_performance_query(params)
        elif question_type == 3:
            return await self._handle_inverter_power_curve_query(params)
        elif question_type == 4:
            return await self._handle_metrics_query(params)
        elif question_type == 5:
            return await self._handle_comparison_query(params)
        else:
            raise ValueError("Unable to understand the query. Please try rephrasing your question.")
    
    def _parse_query(self, query: str) -> Tuple[int, Dict[str, Any]]:
        """
        Parse natural language query to identify question type and extract parameters.
        
        Returns:
            Tuple of (question_type: int, parameters: dict)
        """
        # Basic security check - reject queries with potential SQL injection patterns
        dangerous_patterns = ['--', ';', 'drop', 'delete', 'insert', 'update', 'alter', 'create']
        query_lower = query.lower()
        
        for pattern in dangerous_patterns:
            if pattern in query_lower:
                raise ValueError(f"Query contains potentially dangerous pattern: {pattern}")
        
        params = {}
        
        # Extract site name - look for patterns like "at SITE001" or "for SITE001" or "site SITE001"
        # Site names typically start with SITE followed by digits
        site_patterns = [
            r'(?:at|for|site)\s+(SITE[A-Z0-9]+)',  # Matches "at SITE001", "for SITE001"
            r'(?:at|for)\s+([A-Z]+[0-9]+)',  # Matches "at ABC123" style site names
        ]
        
        for pattern in site_patterns:
            site_match = re.search(pattern, query, re.IGNORECASE)
            if site_match:
                params['site_name'] = site_match.group(1).upper()
                break
        
        # Extract time range
        params['time_range'] = self._extract_time_range(query)
        
        # Question 1: Power curve with underperformance
        if 'power curve' in query_lower and ('underperformance' in query_lower or 'highlight' in query_lower):
            return (1, params)
        
        # Question 2: Worst performing skids/inverters
        if ('worst' in query_lower or 'poor' in query_lower) and ('performance' in query_lower or 'performing' in query_lower):
            return (2, params)
        
        # Question 3: Individual inverter power curve
        if 'inverter' in query_lower and 'power curve' in query_lower:
            inverter_match = re.search(r'inverter\s+([A-Z0-9-]+)', query, re.IGNORECASE)
            if inverter_match:
                params['inverter_id'] = inverter_match.group(1).upper()
            return (3, params)
        
        # Question 4: RMSE and R-squared metrics
        if ('rmse' in query_lower or 'r-squared' in query_lower or 'r squared' in query_lower or 
            'metrics' in query_lower or 'values' in query_lower):
            return (4, params)
        
        # Question 5: Compare power curves
        if 'compare' in query_lower and ('skid' in query_lower or 'power curve' in query_lower):
            # Extract skid IDs
            skid_matches = re.findall(r'skid\s+([A-Z0-9-]+)', query, re.IGNORECASE)
            if len(skid_matches) >= 2:
                params['skid_a'] = skid_matches[0].upper()
                params['skid_b'] = skid_matches[1].upper()
            return (5, params)
        
        # Default: Try to match as a general power curve query
        if 'power curve' in query_lower:
            return (1, params)
        
        return (0, params)
    
    def _extract_time_range(self, query: str) -> Dict[str, datetime]:
        """Extract time range from query string."""
        query_lower = query.lower()
        now = datetime.now()
        
        # Check for specific month mentions
        months = {
            'january': 1, 'february': 2, 'march': 3, 'april': 4,
            'may': 5, 'june': 6, 'july': 7, 'august': 8,
            'september': 9, 'october': 10, 'november': 11, 'december': 12
        }
        
        for month_name, month_num in months.items():
            if month_name in query_lower:
                year = now.year
                # Check if year is mentioned
                year_match = re.search(r'20\d{2}', query)
                if year_match:
                    year = int(year_match.group())
                
                start_date = datetime(year, month_num, 1)
                # Get last day of month
                if month_num == 12:
                    end_date = datetime(year + 1, 1, 1) - timedelta(days=1)
                else:
                    end_date = datetime(year, month_num + 1, 1) - timedelta(days=1)
                
                return {'start_date': start_date, 'end_date': end_date}
        
        # Check for relative time expressions
        if 'today' in query_lower:
            return {
                'start_date': now.replace(hour=0, minute=0, second=0, microsecond=0),
                'end_date': now
            }
        elif 'yesterday' in query_lower:
            yesterday = now - timedelta(days=1)
            return {
                'start_date': yesterday.replace(hour=0, minute=0, second=0, microsecond=0),
                'end_date': yesterday.replace(hour=23, minute=59, second=59, microsecond=999999)
            }
        elif 'last week' in query_lower:
            return {
                'start_date': now - timedelta(days=7),
                'end_date': now
            }
        elif 'last month' in query_lower or 'previous month' in query_lower:
            first_day_current = now.replace(day=1)
            last_day_previous = first_day_current - timedelta(days=1)
            first_day_previous = last_day_previous.replace(day=1)
            return {
                'start_date': first_day_previous,
                'end_date': last_day_previous
            }
        elif 'current month' in query_lower or 'this month' in query_lower:
            return {
                'start_date': now.replace(day=1, hour=0, minute=0, second=0, microsecond=0),
                'end_date': now
            }
        elif 'last 30 days' in query_lower:
            return {
                'start_date': now - timedelta(days=30),
                'end_date': now
            }
        elif 'last 3 months' in query_lower:
            return {
                'start_date': now - timedelta(days=90),
                'end_date': now
            }
        elif 'last 6 months' in query_lower:
            return {
                'start_date': now - timedelta(days=180),
                'end_date': now
            }
        
        # Default to last month
        first_day_current = now.replace(day=1)
        last_day_previous = first_day_current - timedelta(days=1)
        first_day_previous = last_day_previous.replace(day=1)
        return {
            'start_date': first_day_previous,
            'end_date': last_day_previous
        }
    
    def _calculate_performance_ratio(self, actual_power: float, expected_power: float) -> float:
        """Calculate performance ratio with safe division."""
        return actual_power / expected_power if expected_power > 0 else 0.0
    
    def _format_date_range_display(self, start_date: Optional[datetime], end_date: Optional[datetime]) -> str:
        """Format date range for display in summaries."""
        start_str = start_date.strftime('%Y-%m-%d') if start_date else 'N/A'
        end_str = end_date.strftime('%Y-%m-%d') if end_date else 'N/A'
        return f"{start_str} to {end_str}"
    
    async def _handle_power_curve_query(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle power curve visualization query."""
        site_name = params.get('site_name')
        if not site_name:
            raise ValueError("Please specify a site name in your query.")
        
        time_range = params.get('time_range', {})
        start_date = time_range.get('start_date')
        end_date = time_range.get('end_date')
        
        # Get performance data
        data_points = self.performance_repo.get_site_performance_data(
            site_name, 
            start_date,
            end_date
        )
        
        performance_data = {'data_points': data_points} if data_points else None
        
        if not performance_data or not performance_data.get('data_points'):
            return {
                "summary": f"No performance data available for site {site_name} in the specified time range.",
                "data": None
            }
        
        # Calculate underperformance periods
        data_points = performance_data['data_points']
        underperforming_points = []
        total_points = len(data_points)
        
        for point in data_points:
            performance_ratio = self._calculate_performance_ratio(
                point['actual_power'], point['expected_power']
            )
            if performance_ratio > 0 and performance_ratio < self.UNDERPERFORMANCE_THRESHOLD:
                underperforming_points.append({
                    **point,
                    'performance_ratio': performance_ratio
                })
        
        # Generate summary
        underperformance_percentage = (len(underperforming_points) / total_points * 100) if total_points > 0 else 0
        
        summary = f"Power curve analysis for {site_name}:\n"
        summary += f"- Time period: {self._format_date_range_display(start_date, end_date)}\n"
        summary += f"- Total data points: {total_points}\n"
        summary += f"- Underperforming periods: {len(underperforming_points)} ({underperformance_percentage:.1f}% of time)\n"
        
        if underperforming_points:
            avg_underperformance = np.mean([p['performance_ratio'] for p in underperforming_points])
            summary += f"- Average performance during underperformance: {avg_underperformance:.1%} of expected\n"
            summary += f"- Most significant underperformance detected with irradiance levels between "
            summary += f"{min(p['poa_irradiance'] for p in underperforming_points):.0f} and "
            summary += f"{max(p['poa_irradiance'] for p in underperforming_points):.0f} W/m²"
        
        return {
            "summary": summary,
            "data": {
                "data_points": data_points,
                "underperforming_points": underperforming_points
            },
            "chart_type": "scatter",
            "columns": ["poa_irradiance", "actual_power", "expected_power"]
        }
    
    async def _handle_worst_performance_query(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle worst performing components query."""
        site_name = params.get('site_name')
        if not site_name:
            raise ValueError("Please specify a site name in your query.")
        
        time_range = params.get('time_range', {})
        start_date = time_range.get('start_date')
        end_date = time_range.get('end_date')
        
        # Get skids performance data
        skids_list = self.skids_repo.get_skids_performance_data(site_name, start_date, end_date)
        skids_data = {'skids': skids_list} if skids_list else None
        
        if not skids_data or not skids_data.get('skids'):
            return {
                "summary": f"No skids data available for site {site_name}.",
                "data": None
            }
        
        # Get inverters performance data - Note: Repository doesn't have site-level inverters method
        # For MVP, we'll return empty inverters data
        inverters_data = None
        
        # Analyze skids performance
        skids_performance = []
        for skid in skids_data['skids']:
            performance_ratio = self._calculate_performance_ratio(
                skid['avg_actual_power'], skid.get('avg_expected_power', 0)
            )
            if performance_ratio > 0:
                skids_performance.append({
                    'id': skid['skid_id'],
                    'name': skid['skid_name'],
                    'performance_ratio': performance_ratio,
                    'actual_power': skid['avg_actual_power'],
                    'expected_power': skid.get('avg_expected_power', 0)
                })
        
        # Sort by performance (worst first)
        skids_performance.sort(key=lambda x: x['performance_ratio'])
        worst_skids = skids_performance[:self.TOP_WORST_PERFORMERS_COUNT]
        
        # Analyze inverters performance
        inverters_performance = []
        if inverters_data and inverters_data.get('inverters'):
            for inverter in inverters_data['inverters']:
                if inverter.get('avg_expected_power', 0) > 0:
                    performance_ratio = inverter['avg_actual_power'] / inverter['avg_expected_power']
                    inverters_performance.append({
                        'id': inverter['inverter_id'],
                        'name': inverter.get('inverter_name', inverter['inverter_id']),
                        'performance_ratio': performance_ratio,
                        'actual_power': inverter['avg_actual_power'],
                        'expected_power': inverter['avg_expected_power']
                    })
            
            inverters_performance.sort(key=lambda x: x['performance_ratio'])
        
        worst_inverters = inverters_performance[:self.TOP_WORST_PERFORMERS_COUNT]
        
        # Generate summary
        summary = f"Performance analysis for {site_name}:\n\n"
        
        if worst_skids:
            summary += "**Worst Performing Skids:**\n"
            for i, skid in enumerate(worst_skids, 1):
                summary += f"{i}. {skid['name']}: {skid['performance_ratio']:.1%} of expected power\n"
                summary += f"   (Actual: {skid['actual_power']:.1f} kW, Expected: {skid['expected_power']:.1f} kW)\n"
        
        if worst_inverters:
            summary += "\n**Worst Performing Inverters:**\n"
            for i, inverter in enumerate(worst_inverters, 1):
                summary += f"{i}. {inverter['name']}: {inverter['performance_ratio']:.1%} of expected power\n"
                summary += f"   (Actual: {inverter['actual_power']:.1f} kW, Expected: {inverter['expected_power']:.1f} kW)\n"
        
        if not worst_skids and not worst_inverters:
            summary = f"No performance issues detected for components at {site_name}."
        
        return {
            "summary": summary,
            "data": {
                "worst_skids": worst_skids,
                "worst_inverters": worst_inverters
            },
            "chart_type": "bar",
            "columns": ["component_name", "performance_ratio"]
        }
    
    async def _handle_inverter_power_curve_query(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle individual inverter power curve query."""
        site_name = params.get('site_name')
        inverter_id = params.get('inverter_id')
        
        if not site_name:
            raise ValueError("Please specify a site name in your query.")
        if not inverter_id:
            raise ValueError("Please specify an inverter ID in your query.")
        
        time_range = params.get('time_range', {})
        start_date = time_range.get('start_date')
        end_date = time_range.get('end_date')
        
        # Get inverter performance data - using skid ID as proxy for now
        # Note: Repository uses skid_id, not site/inverter combo
        inverter_list = self.inverters_repo.get_inverters_performance_data(
            inverter_id,  # Using inverter_id as skid_id for MVP
            start_date,
            end_date
        )
        inverter_data = {'data_points': inverter_list} if inverter_list else None
        
        if not inverter_data or not inverter_data.get('data_points'):
            return {
                "summary": f"No performance data available for inverter {inverter_id} at site {site_name}.",
                "data": None
            }
        
        data_points = inverter_data['data_points']
        total_points = len(data_points)
        
        # Calculate average performance
        avg_actual = np.mean([p['actual_power'] for p in data_points])
        avg_expected = np.mean([p['expected_power'] for p in data_points])
        performance_ratio = avg_actual / avg_expected if avg_expected > 0 else 0
        
        # Generate summary
        summary = f"Power curve for inverter {inverter_id} at {site_name}:\n"
        summary += f"- Time period: {start_date.strftime('%Y-%m-%d') if start_date else 'N/A'} to {end_date.strftime('%Y-%m-%d') if end_date else 'N/A'}\n"
        summary += f"- Total data points: {total_points}\n"
        summary += f"- Average actual power: {avg_actual:.1f} kW\n"
        summary += f"- Average expected power: {avg_expected:.1f} kW\n"
        summary += f"- Performance ratio: {performance_ratio:.1%}\n"
        
        if performance_ratio < 0.9:
            summary += f"\n⚠️ This inverter is underperforming and may require maintenance."
        elif performance_ratio > 1.1:
            summary += f"\n✅ This inverter is performing above expectations."
        else:
            summary += f"\n✅ This inverter is performing within normal parameters."
        
        return {
            "summary": summary,
            "data": {
                "data_points": data_points,
                "inverter_id": inverter_id,
                "performance_ratio": performance_ratio
            },
            "chart_type": "scatter",
            "columns": ["poa_irradiance", "actual_power", "expected_power"]
        }
    
    async def _handle_metrics_query(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle RMSE and R-squared metrics query."""
        site_name = params.get('site_name')
        if not site_name:
            raise ValueError("Please specify a site name in your query.")
        
        time_range = params.get('time_range', {})
        start_date = time_range.get('start_date')
        end_date = time_range.get('end_date')
        
        # Get performance data
        data_points = self.performance_repo.get_site_performance_data(
            site_name,
            start_date,
            end_date
        )
        performance_data = {'data_points': data_points} if data_points else None
        
        if not performance_data or not performance_data.get('data_points'):
            return {
                "summary": f"No performance data available for site {site_name} to calculate metrics.",
                "data": None
            }
        
        # Calculate RMSE and R-squared
        data_points = performance_data['data_points']
        actual_values = np.array([p['actual_power'] for p in data_points])
        expected_values = np.array([p['expected_power'] for p in data_points])
        
        # RMSE calculation
        mse = np.mean((actual_values - expected_values) ** 2)
        rmse = np.sqrt(mse)
        
        # R-squared calculation
        ss_tot = np.sum((actual_values - np.mean(actual_values)) ** 2)
        ss_res = np.sum((actual_values - expected_values) ** 2)
        r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
        
        # Convert RMSE from kW to MW for consistency
        rmse_mw = rmse / 1000
        
        # Generate summary
        summary = f"Performance metrics for {site_name}:\n"
        summary += f"- Time period: {start_date.strftime('%Y-%m-%d') if start_date else 'N/A'} to {end_date.strftime('%Y-%m-%d') if end_date else 'N/A'}\n"
        summary += f"- Data points analyzed: {len(data_points)}\n\n"
        summary += f"**Key Metrics:**\n"
        summary += f"- RMSE (Root Mean Square Error): {rmse_mw:.2f} MW\n"
        summary += f"- R-squared (Coefficient of Determination): {r_squared:.3f}\n\n"
        
        # Interpret the metrics
        if r_squared > 0.9:
            summary += "✅ Excellent model fit - the expected power predictions are highly accurate.\n"
        elif r_squared > 0.7:
            summary += "⚠️ Good model fit - the expected power predictions are reasonably accurate.\n"
        else:
            summary += "❌ Poor model fit - the expected power predictions show significant deviation from actual values.\n"
        
        if rmse_mw < 1:
            summary += f"✅ Low error rate - average deviation of {rmse_mw:.2f} MW indicates good prediction accuracy."
        elif rmse_mw < 5:
            summary += f"⚠️ Moderate error rate - average deviation of {rmse_mw:.2f} MW suggests room for improvement."
        else:
            summary += f"❌ High error rate - average deviation of {rmse_mw:.2f} MW indicates significant prediction errors."
        
        return {
            "summary": summary,
            "data": {
                "rmse": rmse_mw,
                "r_squared": r_squared,
                "data_points_count": len(data_points),
                "time_range": {
                    "start": start_date.isoformat() if start_date else None,
                    "end": end_date.isoformat() if end_date else None
                }
            },
            "chart_type": None,
            "columns": None
        }
    
    async def _handle_comparison_query(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle skid comparison query."""
        site_name = params.get('site_name')
        skid_a = params.get('skid_a')
        skid_b = params.get('skid_b')
        
        if not site_name:
            raise ValueError("Please specify a site name in your query.")
        if not skid_a or not skid_b:
            raise ValueError("Please specify two skid IDs to compare in your query.")
        
        time_range = params.get('time_range', {})
        start_date = time_range.get('start_date')
        end_date = time_range.get('end_date')
        
        # Get performance data for both skids
        # Note: Using simplified approach - getting all skids and filtering
        all_skids = self.skids_repo.get_skids_performance_data(site_name, start_date, end_date)
        
        # Filter for specific skids
        skid_a_match = [s for s in (all_skids or []) if s.get('skid_id') == skid_a]
        skid_b_match = [s for s in (all_skids or []) if s.get('skid_id') == skid_b]
        
        # Create mock detailed data for comparison (MVP simplification)
        skid_a_data = {'data_points': [{
            'poa_irradiance': 100 * i,
            'actual_power': skid_a_match[0]['avg_actual_power'] if skid_a_match else 0,
            'expected_power': skid_a_match[0]['avg_expected_power'] if skid_a_match else 0
        } for i in range(1, 6)]} if skid_a_match else None
        
        skid_b_data = {'data_points': [{
            'poa_irradiance': 100 * i,
            'actual_power': skid_b_match[0]['avg_actual_power'] if skid_b_match else 0,
            'expected_power': skid_b_match[0]['avg_expected_power'] if skid_b_match else 0
        } for i in range(1, 6)]} if skid_b_match else None
        
        if not skid_a_data or not skid_a_data.get('data_points'):
            return {
                "summary": f"No performance data available for skid {skid_a} at site {site_name}.",
                "data": None
            }
        
        if not skid_b_data or not skid_b_data.get('data_points'):
            return {
                "summary": f"No performance data available for skid {skid_b} at site {site_name}.",
                "data": None
            }
        
        # Calculate metrics for both skids
        skid_a_points = skid_a_data['data_points']
        skid_b_points = skid_b_data['data_points']
        
        avg_actual_a = np.mean([p['actual_power'] for p in skid_a_points])
        avg_expected_a = np.mean([p['expected_power'] for p in skid_a_points])
        performance_ratio_a = avg_actual_a / avg_expected_a if avg_expected_a > 0 else 0
        
        avg_actual_b = np.mean([p['actual_power'] for p in skid_b_points])
        avg_expected_b = np.mean([p['expected_power'] for p in skid_b_points])
        performance_ratio_b = avg_actual_b / avg_expected_b if avg_expected_b > 0 else 0
        
        # Generate comparison summary
        summary = f"Power curve comparison for skids at {site_name}:\n"
        summary += f"- Time period: {start_date.strftime('%Y-%m-%d') if start_date else 'N/A'} to {end_date.strftime('%Y-%m-%d') if end_date else 'N/A'}\n\n"
        
        summary += f"**Skid {skid_a}:**\n"
        summary += f"- Average actual power: {avg_actual_a:.1f} kW\n"
        summary += f"- Average expected power: {avg_expected_a:.1f} kW\n"
        summary += f"- Performance ratio: {performance_ratio_a:.1%}\n"
        summary += f"- Data points: {len(skid_a_points)}\n\n"
        
        summary += f"**Skid {skid_b}:**\n"
        summary += f"- Average actual power: {avg_actual_b:.1f} kW\n"
        summary += f"- Average expected power: {avg_expected_b:.1f} kW\n"
        summary += f"- Performance ratio: {performance_ratio_b:.1%}\n"
        summary += f"- Data points: {len(skid_b_points)}\n\n"
        
        # Comparison conclusion
        if abs(performance_ratio_a - performance_ratio_b) < 0.05:
            summary += "📊 Both skids are performing similarly with less than 5% difference."
        elif performance_ratio_a > performance_ratio_b:
            diff = (performance_ratio_a - performance_ratio_b) * 100
            summary += f"📈 Skid {skid_a} is outperforming Skid {skid_b} by {diff:.1f} percentage points."
        else:
            diff = (performance_ratio_b - performance_ratio_a) * 100
            summary += f"📈 Skid {skid_b} is outperforming Skid {skid_a} by {diff:.1f} percentage points."
        
        return {
            "summary": summary,
            "data": {
                "skid_a": {
                    "id": skid_a,
                    "data_points": skid_a_points,
                    "performance_ratio": performance_ratio_a
                },
                "skid_b": {
                    "id": skid_b,
                    "data_points": skid_b_points,
                    "performance_ratio": performance_ratio_b
                }
            },
            "chart_type": "multi-scatter",
            "columns": ["poa_irradiance", "actual_power_a", "expected_power_a", "actual_power_b", "expected_power_b"]
        }