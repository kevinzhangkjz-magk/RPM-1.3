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
            import traceback
            print(f"ERROR in process_query: {str(e)}")
            print(f"Traceback: {traceback.format_exc()}")
            return {
                "summary": f"I encountered an error processing your query: {str(e)}. Please try rephrasing your question.",
                "data": None,
                "chart_type": None,
                "columns": None
            }
    
    async def _analyze_query_with_ai(self, query: str) -> Dict[str, Any]:
        """Use AI to analyze the query and extract structured information."""
        
        system_prompt = """You are an AI assistant for a solar power plant analytics system. Analyze the user's query and extract structured information.

Available data types:
- Sites: Solar installation locations (e.g., SITE001, SITE002)
- Site Performance: Power generation data over time
- Skids: Groups of solar panels within a site
- Inverters: Individual power conversion units

Respond with JSON containing:
{
    "intent": "performance_analysis|comparison|metrics|power_curve|general_info",
    "data_needed": ["sites", "performance", "skids", "inverters"],
    "site_names": ["SITE001", "SITE002"] or null for all sites,
    "time_range": {"days": 30} or null for default range,
    "specific_components": ["skid_id", "inverter_id"] or null,
    "analysis_type": "underperformance|comparison|trends|metrics",
    "chart_suggestion": "scatter|bar|line|multi-scatter" or null
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
                # Fallback analysis
                analysis = {
                    "intent": "general_info",
                    "data_needed": ["sites", "performance"],
                    "site_names": None,
                    "time_range": {"days": 30},
                    "specific_components": None,
                    "analysis_type": "general",
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
        time_range = analysis.get("time_range") or {"days": 30}
        
        # Calculate time range
        end_date = datetime.now()
        days = time_range.get("days", 30) if time_range else 30
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
                    print(f"DEBUG: Fetched {len(data_context.get('sites', []))} sites from database")
            
            # Fetch performance data - SIMPLIFIED FOR NOW
            if "performance" in data_needed and data_context.get("sites"):
                data_context["performance"] = {}
                # For now, skip detailed performance queries as they're too slow
                # Just use site metadata to generate insights
                for site in data_context["sites"][:5]:  # Limit to 5 sites for performance
                    site_id = site.get("site_id")
                    if site_id:
                        # Mock performance data based on site metadata
                        data_context["performance"][site_id] = [{
                            "site_id": site_id,
                            "site_name": site.get("site_name"),
                            "capacity_kw": site.get("capacity_kw", 0),
                            "status": site.get("connectivity_status", "unknown"),
                            "performance_ratio": 0.85 if site.get("connectivity_status") == "connected" else 0.0
                        }]
            
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
        
        # Prepare data summary for AI
        data_summary = self._create_data_summary(data_context)
        
        system_prompt = """You are an expert solar power plant analyst. The user asked a question about their solar installations, and you have access to real performance data.

Guidelines:
1. Provide clear, actionable insights based on the actual data
2. Use specific numbers and metrics when available
3. Highlight performance issues, trends, or notable findings
4. If suggesting a chart, explain why that visualization is best
5. Keep responses concise but informative (max 500 words)
6. Use bullet points for key findings
7. End with a recommendation or next step if appropriate

Available chart types: scatter, bar, line, multi-scatter

Respond with JSON:
{
    "summary": "Your detailed analysis and insights...",
    "data": [...] or null,
    "chart_type": "scatter|bar|line|multi-scatter" or null,
    "columns": ["col1", "col2", "col3"] or null
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
            site_details = []
            for site in sites[:10]:
                site_id = site.get("site_id", "Unknown")
                site_name = site.get("site_name", "Unknown")
                capacity = site.get("capacity_kw", 0)
                status = site.get("connectivity_status", "unknown")
                site_details.append(f"{site_name} ({site_id}): {capacity:.0f} kW, status={status}")
            summary_parts.append(f"Sites data retrieved: {len(sites)} total")
            summary_parts.extend(site_details)
        
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