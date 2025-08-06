import json
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import openai
from openai import AsyncOpenAI
from ..core.config import settings
from ..dal.sites import SitesRepository
from ..dal.site_performance import SitePerformanceRepository
from ..dal.skids import SkidsRepository
from ..dal.inverters import InvertersRepository
import numpy as np
from scipy import stats
import pandas as pd


class AIServiceV2:
    """Advanced AI Service using OpenAI for natural language understanding and response generation."""
    
    def __init__(self, db=None):
        # Initialize OpenAI client
        api_key = settings.openai_api_key
        if not api_key or api_key == "your_openai_api_key_here":
            # For demo purposes, initialize without client but warn
            self.client = None
            self.ai_enabled = False
        else:
            self.client = AsyncOpenAI(api_key=api_key)
            self.ai_enabled = True
            
        self.model = settings.ai_model
        self.max_tokens = settings.ai_max_tokens
        
        # Initialize repositories
        self.sites_repo = SitesRepository()
        self.performance_repo = SitePerformanceRepository()
        self.skids_repo = SkidsRepository()
        self.inverters_repo = InvertersRepository()
    
    async def process_query(self, query: str) -> Dict[str, Any]:
        """
        Process a natural language query using AI to understand intent and generate responses.
        
        Args:
            query: Natural language query string
            
        Returns:
            Dictionary containing summary, data, and optional chart configuration
        """
        try:
            # Check if AI is enabled
            if not self.ai_enabled:
                return {
                    "summary": "🔧 **AI Assistant Setup Required**\n\nTo enable intelligent responses, please configure your OpenAI API key:\n\n1. Get an API key from https://platform.openai.com/api-keys\n2. Set OPENAI_API_KEY in your environment variables\n3. Restart the backend server\n\nUntil then, I can only provide this setup message. Your query was: \"" + query + "\"",
                    "data": None
                }
            
            # Step 1: Analyze the query with AI to understand intent and extract parameters
            query_analysis = await self._analyze_query_with_ai(query)
            
            # Step 2: Fetch relevant data based on AI analysis
            data_context = await self._fetch_relevant_data(query_analysis)
            
            # Step 3: Generate AI response with the data context
            response = await self._generate_ai_response(query, query_analysis, data_context)
            
            return response
            
        except Exception as e:
            # Fallback to error response
            return {
                "summary": f"I encountered an error processing your query: {str(e)}. Please try rephrasing your question.",
                "data": None
            }
    
    async def _analyze_query_with_ai(self, query: str) -> Dict[str, Any]:
        """Use AI to analyze the query and extract structured information."""
        
        system_prompt = """You are an AI assistant for a renewable energy asset management system. Analyze the user's query and extract structured information.

Available data types:
- Sites: Solar installation locations with 8760 expected power curves
- Site Performance: Actual vs predicted power generation with R-squared and RMSE metrics
- Skids: Groups of solar panels within a site
- Inverters: Individual power conversion units
- Financial: PPA rates and revenue impact calculations

Key metrics:
- R-squared (R²): Correlation between actual vs predicted (target > 0.8)
- RMSE: Root Mean Square Error in MW (target < 2.0 MW)
- Revenue Impact: Monthly revenue loss from underperformance

Respond with JSON containing:
{
    "intent": "underperformance_analysis|comparison|metrics|power_curve|financial_impact|general_info",
    "data_needed": ["sites", "performance", "skids", "inverters", "financial"],
    "site_names": ["Assembly 2", "Highland"] or null for all sites,
    "time_range": {"days": 30} or null for monthly analysis,
    "specific_components": ["skid_id", "inverter_id"] or null,
    "analysis_type": "underperformance|comparison|trends|metrics|financial",
    "metrics_requested": ["r_squared", "rmse", "revenue_impact", "capacity_factor"],
    "ranking_criteria": "r_squared|rmse|revenue_impact" or null,
    "top_n": 3 for "top 3 underperforming sites" queries,
    "chart_suggestion": "performance_metrics|financial_impact|scatter|bar|line" or null
}"""

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": query}
                ],
                max_tokens=300,
                temperature=0.1
            )
            
            # Parse AI response
            ai_response = response.choices[0].message.content.strip()
            
            # Try to parse as JSON, fallback to default structure
            try:
                analysis = json.loads(ai_response)
            except json.JSONDecodeError:
                # Fallback analysis for renewable energy queries
                query_lower = query.lower()
                if any(term in query_lower for term in ['underperform', 'worst', 'rmse', 'r-squared', 'financial']):
                    analysis = {
                        "intent": "underperformance_analysis",
                        "data_needed": ["sites", "performance", "financial"],
                        "site_names": None,
                        "time_range": {"days": 30},
                        "specific_components": None,
                        "analysis_type": "underperformance",
                        "metrics_requested": ["r_squared", "rmse", "revenue_impact"],
                        "ranking_criteria": "r_squared",
                        "top_n": 3 if "3 most" in query_lower or "top 3" in query_lower else 5,
                        "chart_suggestion": "performance_metrics"
                    }
                else:
                    analysis = {
                        "intent": "general_info",
                        "data_needed": ["sites", "performance"],
                        "site_names": None,
                        "time_range": {"days": 30},
                        "specific_components": None,
                        "analysis_type": "general",
                        "metrics_requested": [],
                        "ranking_criteria": None,
                        "top_n": None,
                        "chart_suggestion": None
                    }
            
            return analysis
            
        except Exception as e:
            # Fallback analysis for errors
            return {
                "intent": "general_info",
                "data_needed": ["sites", "performance"],
                "site_names": None,
                "time_range": {"days": 30},
                "specific_components": None,
                "analysis_type": "general",
                "chart_suggestion": None
            }
    
    async def _fetch_relevant_data(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Fetch data based on AI analysis requirements."""
        
        data_context = {}
        data_needed = analysis.get("data_needed", [])
        site_names = analysis.get("site_names")
        time_range = analysis.get("time_range", {"days": 30})
        
        # Calculate time range
        end_date = datetime.now()
        days = time_range.get("days", 30)
        start_date = end_date - timedelta(days=days)
        
        try:
            # Fetch sites data
            if "sites" in data_needed:
                if site_names:
                    data_context["sites"] = []
                    for site_name in site_names:
                        site_data = await self.sites_repo.get_sites_by_name(site_name)
                        if site_data:
                            data_context["sites"].extend(site_data)
                else:
                    # Get all sites
                    all_sites = await self.sites_repo.get_all_sites()
                    data_context["sites"] = all_sites.get("sites", [])[:10]  # Limit to 10 for performance
            
            # Fetch performance data
            if "performance" in data_needed and data_context.get("sites"):
                data_context["performance"] = {}
                for site in data_context["sites"][:5]:  # Limit to 5 sites for performance
                    site_id = site.get("site_id")
                    if site_id:
                        perf_data = await self.performance_repo.get_site_performance(
                            site_id, start_date.isoformat(), end_date.isoformat()
                        )
                        if perf_data and perf_data.get("data_points"):
                            data_context["performance"][site_id] = perf_data["data_points"]
            
            # Fetch skids data
            if "skids" in data_needed and data_context.get("sites"):
                data_context["skids"] = {}
                for site in data_context["sites"][:3]:  # Limit for performance
                    site_id = site.get("site_id")
                    if site_id:
                        skids_data = await self.skids_repo.get_site_skids(
                            site_id, start_date.isoformat(), end_date.isoformat()
                        )
                        if skids_data and skids_data.get("skids"):
                            data_context["skids"][site_id] = skids_data["skids"]
            
            # Fetch inverters data
            if "inverters" in data_needed and data_context.get("sites"):
                data_context["inverters"] = {}
                for site in data_context["sites"][:2]:  # Limit for performance
                    site_id = site.get("site_id")
                    if site_id:
                        inverters_data = await self.inverters_repo.get_site_inverters(
                            site_id, start_date.isoformat(), end_date.isoformat()
                        )
                        if inverters_data and inverters_data.get("inverters"):
                            data_context["inverters"][site_id] = inverters_data["inverters"]
        
        except Exception as e:
            # Add error context but don't fail completely
            data_context["fetch_errors"] = str(e)
        
        return data_context
    
    async def _generate_ai_response(self, original_query: str, analysis: Dict[str, Any], data_context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate AI response with the fetched data context."""
        
        # Check if this is an underperformance analysis query
        if analysis.get("analysis_type") == "underperformance" or analysis.get("intent") == "underperformance_analysis":
            # Use specialized underperformance analysis
            underperf_analysis = await self.analyze_underperformance(
                data_context, 
                top_n=analysis.get("top_n", 3)
            )
            
            # Format the response
            return {
                "summary": self._format_underperformance_summary(underperf_analysis, original_query),
                "data": underperf_analysis["sites"],
                "chart_type": "performance_metrics" if underperf_analysis["sites"] else None,
                "columns": ["site_name", "r_squared", "rmse", "revenue_impact"] if underperf_analysis["sites"] else None,
                "metrics": underperf_analysis["metrics"],
                "recommendations": underperf_analysis["recommendations"]
            }
        
        # Prepare data summary for AI
        data_summary = self._create_data_summary(data_context)
        
        system_prompt = """You are an expert renewable energy asset management analyst. The user asked about solar site performance, and you have access to real performance data with 8760 expected power curves.

Guidelines:
1. Focus on quantitative metrics: R-squared, RMSE, and financial impact
2. Use alert levels: 🚨 CRITICAL (R²<0.7), ⚠️ WARNING (R²<0.8), 📌 MONITOR (R²<0.9), ✅ GOOD (R²≥0.9)
3. Calculate revenue impact: RMSE × operational_hours × PPA_rate
4. Identify root causes: degradation, controller issues, reactive power, shading, soiling
5. Provide ROI for interventions when relevant
6. Use structured format for underperformance queries
7. Always provide actionable recommendations

Available chart types: performance_metrics, financial_impact, scatter, bar, line, multi-scatter

Respond with JSON:
{
    "summary": "Your detailed analysis with alert levels and metrics...",
    "data": [{"site_name": "...", "r_squared": 0.XX, "rmse": X.XX, "revenue_impact": XXXX, "root_cause": "..."}],
    "chart_type": "performance_metrics|financial_impact|scatter|bar" or null,
    "columns": ["site_name", "r_squared", "rmse", "revenue_impact"] or null,
    "metrics": {"total_sites": X, "avg_r_squared": 0.XX, "total_revenue_impact": XXXX, "sites_below_target": X},
    "recommendations": ["Action 1", "Action 2", "Action 3"]
}"""

        try:
            # Create context message
            context_message = f"""
User Query: "{original_query}"

Query Analysis: {json.dumps(analysis, indent=2)}

Available Data Summary:
{data_summary}

Please analyze this data and provide insights to answer the user's question.
"""

            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": context_message}
                ],
                max_tokens=self.max_tokens,
                temperature=0.3
            )
            
            ai_response = response.choices[0].message.content.strip()
            
            # Try to parse as JSON
            try:
                parsed_response = json.loads(ai_response)
                
                # Add actual data if chart is requested
                if parsed_response.get("chart_type") and data_context:
                    chart_data = self._prepare_chart_data(parsed_response["chart_type"], data_context, analysis)
                    parsed_response["data"] = chart_data
                
                return parsed_response
                
            except json.JSONDecodeError:
                # Fallback: treat as plain text summary
                return {
                    "summary": ai_response,
                    "data": None,
                    "chart_type": None,
                    "columns": None
                }
                
        except Exception as e:
            return {
                "summary": f"I found some data but encountered an issue generating the analysis: {str(e)}. Here's what I can tell you: {data_summary[:300]}...",
                "data": None,
                "chart_type": None,
                "columns": None
            }
    
    def _create_data_summary(self, data_context: Dict[str, Any]) -> str:
        """Create a human-readable summary of available data for AI context."""
        
        summary_parts = []
        
        # Sites summary
        if "sites" in data_context and data_context["sites"]:
            sites = data_context["sites"]
            site_names = [site.get("site_name", "Unknown") for site in sites]
            summary_parts.append(f"Sites available: {', '.join(site_names[:5])}")
            if len(sites) > 5:
                summary_parts.append(f"(and {len(sites) - 5} more)")
        
        # Performance data summary
        if "performance" in data_context:
            perf_data = data_context["performance"]
            sites_with_data = len(perf_data)
            if sites_with_data > 0:
                total_points = sum(len(points) for points in perf_data.values())
                summary_parts.append(f"Performance data: {sites_with_data} sites, {total_points} data points")
                
                # Sample performance metrics
                for site_id, points in list(perf_data.items())[:2]:
                    if points:
                        avg_actual = np.mean([p.get("actual_power", 0) for p in points])
                        avg_expected = np.mean([p.get("expected_power", 0) for p in points])
                        if avg_expected > 0:
                            performance_ratio = avg_actual / avg_expected
                            summary_parts.append(f"Site {site_id}: {performance_ratio:.1%} performance ratio")
        
        # Skids summary
        if "skids" in data_context:
            skids_data = data_context["skids"]
            total_skids = sum(len(skids) for skids in skids_data.values())
            if total_skids > 0:
                summary_parts.append(f"Skids data: {total_skids} skids across {len(skids_data)} sites")
        
        # Inverters summary
        if "inverters" in data_context:
            inverters_data = data_context["inverters"]
            total_inverters = sum(len(inverters) for inverters in inverters_data.values())
            if total_inverters > 0:
                summary_parts.append(f"Inverters data: {total_inverters} inverters across {len(inverters_data)} sites")
        
        # Error summary
        if "fetch_errors" in data_context:
            summary_parts.append(f"Note: Some data fetch errors occurred: {data_context['fetch_errors']}")
        
        return "\n".join(summary_parts) if summary_parts else "No data available"
    
    def calculate_performance_metrics(self, actual_values: List[float], predicted_values: List[float]) -> Dict[str, float]:
        """
        Calculate R-squared and RMSE for performance analysis.
        
        Args:
            actual_values: List of actual power generation values
            predicted_values: List of predicted/expected power generation values
            
        Returns:
            Dictionary with r_squared and rmse values
        """
        if not actual_values or not predicted_values or len(actual_values) != len(predicted_values):
            return {"r_squared": 0.0, "rmse": 0.0}
        
        actual = np.array(actual_values)
        predicted = np.array(predicted_values)
        
        # Filter out invalid values
        mask = ~(np.isnan(actual) | np.isnan(predicted) | np.isinf(actual) | np.isinf(predicted))
        actual = actual[mask]
        predicted = predicted[mask]
        
        if len(actual) < 2:
            return {"r_squared": 0.0, "rmse": 0.0}
        
        # Calculate R-squared
        try:
            slope, intercept, r_value, p_value, std_err = stats.linregress(predicted, actual)
            r_squared = r_value ** 2
        except:
            r_squared = 0.0
        
        # Calculate RMSE
        rmse = np.sqrt(np.mean((actual - predicted) ** 2))
        
        return {
            "r_squared": round(r_squared, 4),
            "rmse": round(rmse, 2)
        }
    
    def calculate_financial_impact(self, rmse: float, operational_hours: int = 720, ppa_rate: float = None, site_id: str = None) -> float:
        """
        Calculate monthly revenue impact from RMSE deviation.
        
        Args:
            rmse: Root Mean Square Error in MW
            operational_hours: Hours of operation per month (default 720)
            ppa_rate: Power Purchase Agreement rate in $/MWh (optional, uses config if not provided)
            site_id: Site identifier for site-specific PPA rates
            
        Returns:
            Monthly revenue impact in dollars
        """
        # Use provided rate or get from config
        if ppa_rate is None:
            from ..core.financial_config import get_financial_config
            config = get_financial_config()
            ppa_rate = config.get_ppa_rate(site_id)
        
        # Revenue impact = RMSE * operational_hours * PPA_rate
        revenue_impact = rmse * operational_hours * ppa_rate
        return round(revenue_impact, 2)
    
    def filter_data_quality(self, data_points: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Filter out bad data points (stuck sensors, communication failures).
        
        Args:
            data_points: List of data point dictionaries
            
        Returns:
            Filtered list of data points
        """
        if not data_points:
            return []
        
        filtered = []
        
        for point in data_points:
            # Skip negative irradiance values below -10
            if point.get("poa_irradiance", 0) < -10:
                continue
            
            # Skip obviously stuck values (detect by checking variance in a window)
            # This is simplified - in production would use more sophisticated detection
            if point.get("actual_power") is not None:
                filtered.append(point)
        
        # Additional filtering: remove periods with very low variance
        if len(filtered) > 24:  # At least a day's worth of hourly data
            df = pd.DataFrame(filtered)
            if 'actual_power' in df.columns:
                # Group by day and check variance
                df['date'] = pd.to_datetime(df.get('timestamp', pd.Timestamp.now()))
                df['day'] = df['date'].dt.date
                
                # Calculate daily variance
                daily_stats = df.groupby('day')['actual_power'].agg(['std', 'mean'])
                
                # Filter out days with very low variance (likely stuck data)
                valid_days = daily_stats[daily_stats['std'] > daily_stats['mean'] * 0.05].index
                
                # Keep only data from valid days
                filtered = df[df['day'].isin(valid_days)].to_dict('records')
        
        return filtered
    
    def _format_underperformance_summary(self, analysis: Dict[str, Any], query: str) -> str:
        """
        Format the underperformance analysis into a structured summary.
        
        Args:
            analysis: Analysis results from analyze_underperformance
            query: Original user query
            
        Returns:
            Formatted markdown summary
        """
        sites = analysis.get("sites", [])
        metrics = analysis.get("metrics", {})
        
        if not sites:
            return "No underperforming sites found based on available data. All sites appear to be operating within expected parameters."
        
        # Determine query type
        query_lower = query.lower()
        if "financial" in query_lower or "revenue" in query_lower:
            focus = "financial"
        elif "rmse" in query_lower:
            focus = "rmse"
        else:
            focus = "overall"
        
        # Build summary
        summary = []
        
        # Header
        summary.append(f"🎯 **TOP {len(sites)} UNDERPERFORMING SITES**")
        summary.append(f"*Analysis Period: Last 30 days*\n")
        
        # Site details
        for idx, site in enumerate(sites, 1):
            status_emoji = {
                "CRITICAL": "🚨",
                "WARNING": "⚠️",
                "MONITOR": "📌",
                "GOOD": "✅"
            }.get(site.get("status", ""), "")
            
            summary.append(f"**{idx}. {site['site_name']}** - {status_emoji} {site.get('status', '')}")
            summary.append(f"   • R²: {site['r_squared']:.3f} | RMSE: {site['rmse']:.2f} MW")
            
            if site.get('revenue_impact'):
                summary.append(f"   • Revenue Impact: ${site['revenue_impact']:,.0f}/month")
            
            if site.get('root_cause'):
                summary.append(f"   • Root Cause: {site['root_cause']}")
            
            summary.append("")  # Add spacing
        
        # Portfolio insights
        if metrics:
            summary.append("💡 **PORTFOLIO INSIGHTS:**")
            summary.append(f"• Total Sites Analyzed: {metrics.get('total_sites', 0)}")
            summary.append(f"• Average R²: {metrics.get('avg_r_squared', 0):.3f}")
            
            if metrics.get('total_revenue_impact'):
                summary.append(f"• Total Revenue at Risk: ${metrics.get('total_revenue_impact', 0):,.0f}/month")
            
            if metrics.get('sites_below_target'):
                summary.append(f"• Sites Below Target (R² < 0.8): {metrics.get('sites_below_target', 0)}")
        
        return "\n".join(summary)
    
    async def analyze_underperformance(self, data_context: Dict[str, Any], top_n: int = 3) -> Dict[str, Any]:
        """
        Analyze sites for underperformance using R-squared and RMSE metrics.
        
        Args:
            data_context: Context with performance data
            top_n: Number of top underperforming sites to return
            
        Returns:
            Analysis results with rankings and metrics
        """
        site_metrics = []
        
        if "performance" not in data_context:
            return {
                "sites": [],
                "metrics": {},
                "recommendations": ["No performance data available for analysis"]
            }
        
        # Calculate metrics for each site
        for site_id, points in data_context["performance"].items():
            if not points:
                continue
            
            # Filter data quality
            filtered_points = self.filter_data_quality(points)
            
            if len(filtered_points) < 10:  # Need minimum data points
                continue
            
            # Extract actual and predicted values
            actual_values = [p.get("actual_power", 0) for p in filtered_points]
            predicted_values = [p.get("expected_power", 0) for p in filtered_points]
            
            # Calculate metrics
            metrics = self.calculate_performance_metrics(actual_values, predicted_values)
            
            # Calculate financial impact with site-specific PPA rate
            revenue_impact = self.calculate_financial_impact(
                metrics["rmse"],
                operational_hours=len(filtered_points),  # Actual hours with data
                site_id=site_id  # Use site-specific PPA rate from config
            )
            
            # Determine status and root cause
            r_squared = metrics["r_squared"]
            if r_squared < 0.7:
                status = "CRITICAL"
                root_cause = "Severe underperformance - possible equipment failure or degradation"
            elif r_squared < 0.8:
                status = "WARNING"
                root_cause = "Significant deviation - check for controller issues or shading"
            elif r_squared < 0.9:
                status = "MONITOR"
                root_cause = "Moderate deviation - may need cleaning or minor adjustments"
            else:
                status = "GOOD"
                root_cause = "Operating within expected parameters"
            
            # Get site name from context
            site_name = site_id
            if "sites" in data_context:
                for site in data_context["sites"]:
                    if site.get("site_id") == site_id:
                        site_name = site.get("site_name", site_id)
                        break
            
            site_metrics.append({
                "site_id": site_id,
                "site_name": site_name,
                "r_squared": metrics["r_squared"],
                "rmse": metrics["rmse"],
                "revenue_impact": revenue_impact,
                "status": status,
                "root_cause": root_cause,
                "data_points": len(filtered_points)
            })
        
        # Sort by R-squared (ascending = worst first)
        site_metrics.sort(key=lambda x: x["r_squared"])
        
        # Get top N underperforming sites
        top_sites = site_metrics[:top_n]
        
        # Calculate portfolio metrics
        if site_metrics:
            avg_r_squared = np.mean([s["r_squared"] for s in site_metrics])
            total_revenue_impact = sum(s["revenue_impact"] for s in site_metrics)
            sites_below_target = sum(1 for s in site_metrics if s["r_squared"] < 0.8)
        else:
            avg_r_squared = 0
            total_revenue_impact = 0
            sites_below_target = 0
        
        # Generate recommendations
        recommendations = []
        if top_sites:
            if top_sites[0]["r_squared"] < 0.7:
                recommendations.append("Immediate inspection required for critical sites")
            if sites_below_target > len(site_metrics) * 0.3:
                recommendations.append("Portfolio-wide performance review recommended")
            if total_revenue_impact > 100000:
                recommendations.append("Consider O&M contract review for cost recovery")
            recommendations.append(f"Focus on top {min(3, len(top_sites))} underperforming sites for maximum ROI")
        
        return {
            "sites": top_sites,
            "metrics": {
                "total_sites": len(site_metrics),
                "avg_r_squared": round(avg_r_squared, 3),
                "total_revenue_impact": round(total_revenue_impact, 2),
                "sites_below_target": sites_below_target
            },
            "recommendations": recommendations
        }
    
    def _prepare_chart_data(self, chart_type: str, data_context: Dict[str, Any], analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Prepare data for charting based on the requested chart type."""
        
        chart_data = []
        
        try:
            if chart_type == "scatter" and "performance" in data_context:
                # Scatter plot: POA irradiance vs power
                for site_id, points in data_context["performance"].items():
                    for point in points[:50]:  # Limit points for performance
                        if point.get("poa_irradiance") and point.get("actual_power"):
                            chart_data.append({
                                "poa_irradiance": point.get("poa_irradiance", 0),
                                "actual_power": point.get("actual_power", 0),
                                "expected_power": point.get("expected_power", 0),
                                "site": site_id
                            })
            
            elif chart_type == "bar" and "skids" in data_context:
                # Bar chart: Component performance
                for site_id, skids in data_context["skids"].items():
                    for skid in skids[:10]:  # Limit for performance
                        actual = skid.get("avg_actual_power", 0)
                        expected = skid.get("avg_expected_power", 0)
                        performance_ratio = actual / expected if expected > 0 else 0
                        chart_data.append({
                            "component_name": skid.get("skid_id", "Unknown"),
                            "performance_ratio": performance_ratio,
                            "actual_power": actual,
                            "expected_power": expected
                        })
            
            elif chart_type == "multi-scatter" and "performance" in data_context:
                # Multi-scatter: Multiple series
                for site_id, points in list(data_context["performance"].items())[:3]:
                    for point in points[:30]:  # Limit points
                        if point.get("poa_irradiance"):
                            chart_data.append({
                                "poa_irradiance": point.get("poa_irradiance", 0),
                                "actual_power": point.get("actual_power", 0),
                                "expected_power": point.get("expected_power", 0),
                                "site": site_id
                            })
        
        except Exception as e:
            # Return empty data on error
            return []
        
        return chart_data