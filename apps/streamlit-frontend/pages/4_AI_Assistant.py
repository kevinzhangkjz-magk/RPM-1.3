"""
AI Assistant Page - Natural language interface for diagnostics
Uses real API endpoint for AI queries with visualization support
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
import json
import re
import sys
from pathlib import Path
from typing import Any

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import from helper
try:
    from import_helper import (
        initialize_session_state,
        add_chat_message,
        get_session_value,
        get_api_client,
        check_and_redirect_auth,
        input_sanitizer,
        render_breadcrumb,
        theme
    )
except ImportError:
    # Fallback: Add path and try again
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from import_helper import (
        initialize_session_state,
        add_chat_message,
        get_session_value,
        get_api_client,
        check_and_redirect_auth,
        input_sanitizer,
        render_breadcrumb,
        theme
    )

# Import chart function directly (not in import_helper yet)
try:
    from components.charts import render_performance_scatter
except ImportError:
    try:
        import charts
        render_performance_scatter = charts.render_performance_scatter
    except ImportError:
        # Last resort: load directly from file
        import importlib.util
        charts_path = Path(__file__).parent.parent / 'components' / 'charts.py'
        spec = importlib.util.spec_from_file_location("charts", charts_path)
        if spec and spec.loader:
            charts = importlib.util.module_from_spec(spec)
            sys.modules["charts"] = charts
            spec.loader.exec_module(charts)
            render_performance_scatter = charts.render_performance_scatter

# Page config
st.set_page_config(
    page_title="AI Assistant - RPM",
    page_icon="🤖",
    layout="wide"
)

# Initialize session state
initialize_session_state()

# Apply theme
theme.apply_custom_theme()

# Check authentication
check_and_redirect_auth()

# Get API client
api_client = get_api_client()

# Define functions before using them
def format_underperformance_response(summary: str, data: Any, metrics: dict, recommendations: list) -> str:
    """
    Format response for underperformance queries with structured output.
    
    Args:
        summary: Original summary from API
        data: Performance data
        metrics: Performance metrics (R-squared, RMSE, etc.)
        recommendations: List of recommendations
    
    Returns:
        Formatted response string
    """
    formatted = []
    
    # Add summary if not empty
    if summary and summary.strip():
        formatted.append(summary + "\n")
    
    # Format sites data if available
    if data and isinstance(data, list) and len(data) > 0:
        formatted.append("\n📊 **Performance Metrics:**\n")
        
        for idx, site in enumerate(data[:5], 1):  # Top 5 sites
            site_name = site.get('site_name', f'Site {idx}')
            r_squared = site.get('r_squared', 'N/A')
            rmse = site.get('rmse', 'N/A')
            revenue_impact = site.get('revenue_impact', 'N/A')
            status = site.get('status', 'REVIEW')
            
            # Determine alert level
            if isinstance(r_squared, (int, float)):
                if r_squared < 0.7:
                    alert = "🚨 CRITICAL"
                elif r_squared < 0.8:
                    alert = "⚠️ WARNING"
                elif r_squared < 0.9:
                    alert = "📌 MONITOR"
                else:
                    alert = "✅ GOOD"
            else:
                alert = status
            
            formatted.append(f"\n**{idx}. {site_name}** - {alert}")
            
            # Format metrics
            if isinstance(r_squared, (int, float)):
                formatted.append(f"   • R²: {r_squared:.3f}")
            else:
                formatted.append(f"   • R²: {r_squared}")
            
            if isinstance(rmse, (int, float)):
                formatted.append(f"   • RMSE: {rmse:.2f} MW")
            else:
                formatted.append(f"   • RMSE: {rmse}")
            
            if revenue_impact != 'N/A':
                if isinstance(revenue_impact, (int, float)):
                    formatted.append(f"   • Revenue Impact: ${revenue_impact:,.0f}/month")
                else:
                    formatted.append(f"   • Revenue Impact: {revenue_impact}")
            
            # Add root cause if available
            root_cause = site.get('root_cause')
            if root_cause:
                formatted.append(f"   • Root Cause: {root_cause}")
    
    # Add portfolio insights
    if metrics:
        formatted.append("\n💡 **Portfolio Insights:**\n")
        
        if 'total_sites' in metrics:
            formatted.append(f"• Total Sites Analyzed: {metrics['total_sites']}")
        if 'avg_r_squared' in metrics:
            formatted.append(f"• Average R²: {metrics['avg_r_squared']:.3f}")
        if 'total_revenue_impact' in metrics:
            formatted.append(f"• Total Revenue at Risk: ${metrics['total_revenue_impact']:,.0f}/month")
        if 'sites_below_target' in metrics:
            formatted.append(f"• Sites Below Target: {metrics['sites_below_target']}")
    
    # Add recommendations
    if recommendations:
        formatted.append("\n📋 **Recommended Actions:**\n")
        for idx, rec in enumerate(recommendations[:5], 1):
            formatted.append(f"{idx}. {rec}")
    
    return "\n".join(formatted)

def build_conversational_context() -> dict:
    """
    Build conversational context from chat history for AI assistant.
    
    Returns:
        Dictionary containing previous queries and context
    """
    context = {
        "previous_queries": [],
        "session_id": st.session_state.get("session_id", ""),
        "user_id": st.session_state.get("user_id", ""),
        "selected_sites": st.session_state.get("selected_sites", []),
        "time_range": st.session_state.get("time_range", {})
    }
    
    # Extract previous queries from chat history
    if 'chat_history' in st.session_state:
        for msg in st.session_state.chat_history[-5:]:  # Last 5 messages for context
            if msg['role'] == 'user':
                context['previous_queries'].append(msg['content'])
    
    return context

def validate_and_sanitize_query(query: str) -> str:
    """
    Validate and sanitize user query to prevent injection attacks.
    
    Args:
        query: User input query
        
    Returns:
        Sanitized query string
    """
    # Remove potential SQL injection patterns
    dangerous_patterns = [
        'DROP', 'DELETE', 'INSERT', 'UPDATE', 'ALTER', 'CREATE',
        'EXEC', 'EXECUTE', '--', '/*', '*/', 'xp_', 'sp_'
    ]
    
    sanitized = query
    for pattern in dangerous_patterns:
        sanitized = sanitized.replace(pattern, '')
        sanitized = sanitized.replace(pattern.lower(), '')
    
    # Limit query length
    max_length = 1000
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length]
    
    return sanitized.strip()

def process_user_query(query: str, api_client) -> None:
    """
    Process user query through AI API and display response.
    Handles both standard queries and specialized renewable energy asset management queries.
    
    Args:
        query: User's natural language query
        api_client: API client for AI endpoint
    """
    # Validate and sanitize query
    sanitized_query = validate_and_sanitize_query(query)
    
    # Add user message to history
    add_chat_message("user", sanitized_query)
    
    # Build conversational context from history
    context = build_conversational_context()
    
    try:
        # Detect query type for enhanced processing
        query_lower = sanitized_query.lower()
        is_underperformance_query = any(term in query_lower for term in [
            'underperform', 'worst', 'bottom', 'low r', 'rmse', 'poor perform',
            'financial impact', 'revenue impact', 'need attention'
        ])
        
        # Call AI API with enhanced context for asset management queries
        with st.spinner("Analyzing portfolio performance..." if is_underperformance_query else "Thinking..."):
            # Try context-aware query first
            if hasattr(api_client, 'query_ai_assistant_with_context'):
                response = api_client.query_ai_assistant_with_context(sanitized_query, context)
            else:
                # Fallback to standard query
                response = api_client.query_ai_assistant(sanitized_query)
        
        # Debug: Show what we got from API
        st.write("Debug - API Response:", response)
        
        # Process response based on query type
        if is_underperformance_query and response:
            # Extract components for enhanced formatting
            summary = response.get('summary', '')
            data = response.get('data', [])
            
            # Check if summary contains JSON data (backend sometimes returns data in summary)
            if not data and summary and '```json' in summary:
                try:
                    # Extract JSON from markdown code block
                    import re
                    json_match = re.search(r'```json\n(.*?)\n```', summary, re.DOTALL)
                    if json_match:
                        json_str = json_match.group(1)
                        parsed_response = json.loads(json_str)
                        summary = parsed_response.get('summary', summary)
                        data = parsed_response.get('data', [])
                        if 'metrics' in parsed_response:
                            response['metrics'] = parsed_response['metrics']
                        if 'recommendations' in parsed_response:
                            response['recommendations'] = parsed_response['recommendations']
                except:
                    pass  # If parsing fails, continue with original data
            
            # Generate performance metrics (use from response if available)
            metrics = response.get('metrics', {})
            recommendations = response.get('recommendations', [])
            
            if data and isinstance(data, list):
                # Calculate portfolio-level metrics
                metrics['total_sites'] = len(data)
                
                r_squared_values = [site.get('r_squared', 0) for site in data 
                                   if isinstance(site.get('r_squared'), (int, float))]
                if r_squared_values:
                    metrics['avg_r_squared'] = sum(r_squared_values) / len(r_squared_values)
                    metrics['sites_below_target'] = len([r for r in r_squared_values if r < 0.8])
                
                revenue_impacts = [site.get('revenue_impact', 0) for site in data 
                                  if isinstance(site.get('revenue_impact'), (int, float))]
                if revenue_impacts:
                    metrics['total_revenue_impact'] = sum(revenue_impacts)
                
                # Generate recommendations based on data
                if metrics.get('sites_below_target', 0) > 2:
                    recommendations.append("Schedule immediate maintenance review for critical sites")
                if metrics.get('avg_r_squared', 1) < 0.8:
                    recommendations.append("Implement portfolio-wide performance optimization program")
                if metrics.get('total_revenue_impact', 0) > 100000:
                    recommendations.append("Prioritize high-impact sites for rapid resolution")
                
                # Add specific site recommendations
                for site in data[:3]:  # Top 3 worst performers
                    if site.get('r_squared', 1) < 0.7:
                        recommendations.append(f"Critical: Investigate {site.get('site_name', 'site')} immediately")
            
            # Format enhanced response
            formatted_response = format_underperformance_response(summary, data, metrics, recommendations)
            add_chat_message("assistant", formatted_response)
        else:
            # Standard response handling
            summary = response.get('summary', 'I encountered an issue processing your query.')
            add_chat_message("assistant", summary)
            
            # Handle visualizations if present
            if response.get('chart_type') and response.get('data'):
                chart_type = response['chart_type']
                data = response['data']
                
                # Create appropriate visualization
                if chart_type == 'scatter' and isinstance(data, list):
                    df = pd.DataFrame(data)
                    if 'actual' in df.columns and 'predicted' in df.columns:
                        fig = render_performance_scatter(df)
                        st.plotly_chart(fig, use_container_width=True)
                elif chart_type == 'bar' and isinstance(data, list):
                    df = pd.DataFrame(data)
                    if not df.empty:
                        first_numeric = df.select_dtypes(include=['number']).columns[0] if len(df.select_dtypes(include=['number']).columns) > 0 else None
                        first_string = df.select_dtypes(include=['object']).columns[0] if len(df.select_dtypes(include=['object']).columns) > 0 else None
                        
                        if first_numeric and first_string:
                            fig = px.bar(df, x=first_string, y=first_numeric, 
                                       title=f"{first_numeric} by {first_string}")
                            st.plotly_chart(fig, use_container_width=True)
                
                # Display data table if available
                if isinstance(data, list) and data:
                    with st.expander("📊 View Data Table"):
                        st.dataframe(pd.DataFrame(data))
    
    except Exception as e:
        error_msg = f"I encountered an error processing your query: {str(e)}. Please try rephrasing your question."
        add_chat_message("assistant", error_msg)
        st.error(f"Error: {str(e)}")
        # Debug: Show the error
        st.write(f"Debug - Error occurred: {str(e)}")
        import traceback
        st.write(f"Debug - Traceback: {traceback.format_exc()}")

# Header
st.title("🤖 AI Diagnostic Assistant")
st.markdown("Ask questions about your solar assets in natural language")

# Render breadcrumb
render_breadcrumb()

# Create a placeholder for processing queries from sidebar
query_to_process = None

# Sidebar with predefined questions and controls
with st.sidebar:
    st.markdown("### 💡 Example Questions")
    
    # Categorized questions for better UX
    st.markdown("#### 📊 Performance Analysis")
    performance_questions = [
        "Give me the 3 most underperforming sites",
        "Which sites have RMSE above 2.0 MW?",
        "Show me sites with less than 80% R-squared",
        "What's the financial impact of our worst performers?",
        "Compare Q3 vs Q4 performance",
    ]
    
    for question in performance_questions:
        if st.button(question, key=f"perf_{question[:20]}", use_container_width=True):
            query_to_process = question
    
    st.markdown("#### 🔍 Site Diagnostics")
    diagnostic_questions = [
        "Show the power curve for Assembly 2",
        "What's the performance ratio for Highland?",
        "Analyze inverter efficiency at Assembly 2",
        "Compare actual vs expected at Big River",
        "Which inverters are underperforming at Assembly 2?"
    ]
    
    for question in diagnostic_questions:
        if st.button(question, key=f"diag_{question[:20]}", use_container_width=True):
            query_to_process = question
    
    st.markdown("#### 📈 Trends & Metrics")
    trend_questions = [
        "Show monthly energy production trends",
        "What's the average PR across all sites?",
        "Which sites improved the most this month?",
        "Show capacity factor by site",
        "What's our portfolio efficiency?"
    ]
    
    for question in trend_questions:
        if st.button(question, key=f"trend_{question[:20]}", use_container_width=True):
            query_to_process = question
    
    st.divider()
    
    # Clear chat button
    if st.button("🗑️ Clear Chat History", use_container_width=True):
        # Clear chat history from session state
        if 'chat_history' in st.session_state:
            st.session_state.chat_history = []
        st.rerun()
    
    # Export chat button
    if st.button("📥 Export Chat", use_container_width=True):
        if 'chat_history' in st.session_state and st.session_state.chat_history:
            chat_export = json.dumps(st.session_state.chat_history, indent=2, default=str)
            st.download_button(
                label="Download Chat History",
                data=chat_export,
                file_name=f"chat_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )

# Chat history display
chat_container = st.container()

with chat_container:
    # Display chat history
    if 'chat_history' not in st.session_state or not st.session_state.chat_history:
        # Welcome message
        with st.chat_message("assistant", avatar="🤖"):
            st.markdown("""
            👋 Hello! I'm your AI Diagnostic Assistant for renewable energy asset management.
            
            I can help you:
            - **Identify underperforming sites** using R² and RMSE metrics
            - **Calculate financial impact** of performance issues
            - **Analyze power curves** and performance trends
            - **Compare sites** and track improvements
            
            Try asking: **"Give me the 3 most underperforming sites"** or select a question from the sidebar.
            """)
    else:
        # Display chat history
        for message in st.session_state.chat_history:
            with st.chat_message(message['role'], avatar="🤖" if message['role'] == "assistant" else "👤"):
                st.markdown(message['content'])

# Input area with enhanced UI
st.markdown("---")

# Initialize input state
if 'ai_input' not in st.session_state:
    st.session_state.ai_input = ""

# Query input - don't use value parameter when using key that's in session state
user_input = st.text_area(
    "Ask a question about your solar assets:",
    placeholder="E.g., Which sites are underperforming today?",
    key="ai_input",  # This will automatically sync with session state
    label_visibility="collapsed",
    height=100
)

col1, col2, col3 = st.columns([1, 1, 4])

with col1:
    if st.button("🚀 Send", type="primary", use_container_width=True):
        # Get the current value from session state
        current_input = st.session_state.get('ai_input', '')
        st.write(f"Debug - Input value: '{current_input}'")  # Debug line
        
        if current_input and current_input.strip():
            st.write("Debug - Processing query...")  # Debug line
            try:
                # Process the query
                process_user_query(current_input, api_client)
            except Exception as e:
                st.error(f"Error processing query: {e}")
                import traceback
                st.write(traceback.format_exc())
            # Don't clear or rerun yet - let's see what happens
        else:
            st.warning("Please enter a question before clicking Send.")

with col2:
    if st.button("🎙️ Voice Input", use_container_width=True):
        st.info("Voice input will be implemented")

# Process query from sidebar if one was selected
if query_to_process:
    process_user_query(query_to_process, api_client)
    st.rerun()

# Help section in expander
with st.expander("ℹ️ Help & Capabilities"):
    st.markdown("""
    ### What I can do:
    
    **🎯 Performance Analysis**
    - Identify underperforming sites using R² and RMSE metrics
    - Rank sites by performance deviation from 8760 predictions
    - Calculate financial impact of underperformance
    - Compare quarterly and monthly performance trends
    - Detect sites needing immediate attention
    
    **📊 Quantitative Metrics**
    - **R-squared (R²)**: Correlation between actual vs predicted power (target: >0.8)
    - **RMSE**: Root Mean Square Error in MW (target: <2.0 MW)
    - **Capacity Factor**: Actual vs expected capacity utilization
    - **Revenue Impact**: Monthly revenue at risk from underperformance
    - **Availability Factor**: Operational uptime percentage
    
    **💰 Financial Impact**
    - Calculate revenue loss from RMSE deviations
    - Project annual revenue impact
    - ROI analysis for intervention strategies
    - Payback period calculations
    
    **🔍 Root Cause Analysis**
    - Detect equipment degradation patterns
    - Identify power plant controller issues
    - Spot reactive power problems
    - Find shading or soiling impacts
    - Detect communication failures
    
    **📈 Portfolio Management**
    - Monthly portfolio performance reports
    - Peer benchmarking across sites
    - Trend analysis and forecasting
    - Alert prioritization by financial impact
    
    ### Example Queries:
    - "Give me the 3 most underperforming sites"
    - "Which sites have RMSE above 2.0 MW?"
    - "Show me sites with R² below 0.8"
    - "What's the financial impact of underperformance?"
    - "Compare Assembly 2 and Assembly 3 performance"
    - "Which sites need immediate O&M attention?"
    - "Show me the monthly trend for Highland"
    
    ### Alert Levels:
    - 🚨 **CRITICAL**: R² < 0.7 or RMSE > 3.0 MW
    - ⚠️ **WARNING**: R² < 0.8 or RMSE > 2.0 MW  
    - 📌 **MONITOR**: R² < 0.9 or RMSE > 1.5 MW
    - ✅ **GOOD**: R² ≥ 0.9 and RMSE ≤ 1.5 MW
    """)