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
def format_conversational_response(summary: str, data: Any, metrics: dict, recommendations: list, query_type: str) -> str:
    """
    Format response in a conversational, technical manner with integrated data.
    
    Args:
        summary: Original summary from API
        data: Performance data
        metrics: Performance metrics (R-squared, RMSE, etc.)
        recommendations: List of recommendations
        query_type: Type of query for context
    
    Returns:
        Conversational response string
    """
    response_parts = []
    
    # Start with analysis context - check for various underperformance queries
    query_lower = query_type.lower()
    is_underperformance = any(term in query_lower for term in [
        'underperform', 'worst', 'bottom', 'poor', '3 most', 'three most'
    ])
    
    if is_underperformance and data and isinstance(data, list) and len(data) > 0:
            num_sites = len(data)
            
            # Opening analysis
            response_parts.append(f"Based on my analysis of your renewable energy portfolio, I've identified {num_sites} sites that require attention due to performance deviations from their 8760 model predictions.\n")
            
            # Detailed site analysis
            for idx, site in enumerate(data[:3], 1):  # Focus on top 3
                site_name = site.get('site_name', f'Site {idx}')
                r_squared = site.get('r_squared', 0)
                rmse = site.get('rmse', 0)
                revenue_impact = site.get('revenue_impact', 0)
                root_cause = site.get('root_cause', '')
                
                if idx == 1:
                    response_parts.append(f"\nThe most concerning is **{site_name}**, which is exhibiting an R² of {r_squared:.3f} and an RMSE of {rmse:.2f} MW. ")
                    if revenue_impact > 0:
                        response_parts.append(f"This performance degradation translates to approximately ${revenue_impact:,.0f} in monthly revenue at risk. ")
                    if root_cause:
                        response_parts.append(f"The primary issue appears to be {root_cause.lower()}. ")
                elif idx == 2:
                    response_parts.append(f"\n\n**{site_name}** is the second site requiring immediate attention, with an R² of {r_squared:.3f} and RMSE of {rmse:.2f} MW")
                    if revenue_impact > 0:
                        response_parts.append(f", representing a potential revenue impact of ${revenue_impact:,.0f} per month")
                    response_parts.append(". ")
                    if root_cause:
                        response_parts.append(f"Analysis indicates {root_cause.lower()}. ")
                else:
                    response_parts.append(f"\n\n**{site_name}** rounds out the top three underperformers with an R² of {r_squared:.3f} and RMSE of {rmse:.2f} MW")
                    if revenue_impact > 0:
                        response_parts.append(f" (${revenue_impact:,.0f}/month at risk)")
                    response_parts.append(". ")
                    if root_cause:
                        response_parts.append(f"The system shows signs of {root_cause.lower()}. ")
            
            # Portfolio-level insights
            if metrics:
                response_parts.append("\n\nFrom a portfolio perspective, ")
                insights = []
                if 'avg_r_squared' in metrics:
                    avg_r2 = metrics['avg_r_squared']
                    if avg_r2 < 0.8:
                        insights.append(f"the average R² across all sites is {avg_r2:.3f}, which is below the target threshold of 0.8")
                    else:
                        insights.append(f"the portfolio maintains an average R² of {avg_r2:.3f}")
                
                if 'total_revenue_impact' in metrics and metrics['total_revenue_impact'] > 0:
                    insights.append(f"with total revenue exposure of ${metrics['total_revenue_impact']:,.0f} per month")
                
                if 'sites_below_target' in metrics and metrics['sites_below_target'] > 0:
                    insights.append(f"and {metrics['sites_below_target']} sites operating below target performance")
                
                if insights:
                    response_parts.append(", ".join(insights))
                    response_parts.append(".")
            
            # Technical recommendations
            if recommendations and len(recommendations) > 0:
                response_parts.append("\n\nBased on this analysis, I recommend the following immediate actions: ")
                response_parts.append(", ".join(recommendations[:3]).lower())
                response_parts.append(". These interventions should be prioritized based on revenue impact and operational feasibility.")
    
    elif "rmse" in query_type.lower():
        if data and isinstance(data, list) and len(data) > 0:
            threshold = 2.0  # MW threshold
            sites_above = [s for s in data if s.get('rmse', 0) > threshold]
            
            response_parts.append(f"I've completed an RMSE analysis across your portfolio. ")
            response_parts.append(f"{len(sites_above)} sites are currently operating with RMSE values exceeding {threshold} MW, ")
            response_parts.append("indicating significant deviation from predicted power output.\n\n")
            
            for site in sites_above[:3]:
                site_name = site.get('site_name')
                rmse = site.get('rmse', 0)
                response_parts.append(f"**{site_name}** shows an RMSE of {rmse:.2f} MW, ")
                if site.get('revenue_impact'):
                    response_parts.append(f"with associated revenue risk of ${site['revenue_impact']:,.0f}/month. ")
    
    else:
        # Handle all other cases - prioritize using summary if available
        if summary and summary.strip():
            response_parts.append(summary)
        elif data and isinstance(data, list) and len(data) > 0:
            # Format data conversationally
            response_parts.append("Based on my analysis of the portfolio:\n\n")
            for idx, site in enumerate(data[:3], 1):
                if isinstance(site, dict):
                    site_name = site.get('site_name', f'Site {idx}')
                    r_squared = site.get('r_squared', 0)
                    rmse = site.get('rmse', 0)
                    revenue_impact = site.get('revenue_impact', 0)
                    
                    response_parts.append(f"**{site_name}**: R²={r_squared:.3f}, RMSE={rmse:.2f} MW")
                    if revenue_impact > 0:
                        response_parts.append(f" (Revenue impact: ${revenue_impact:,.0f}/month)")
                    response_parts.append("\n")
    
    # Always return something meaningful
    if response_parts:
        return "".join(response_parts)
    else:
        return "I need more information to provide a comprehensive analysis. Could you please specify which metrics or sites you'd like me to analyze?"

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

# Remove the visualization function as data will be integrated in responses

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
    
    # Make sure chat history is initialized
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    
    # Add user message to history immediately and ensure it persists
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
        
        # Debug: Show what we got from API (only if in debug mode)
        if st.session_state.get('debug_mode', False):
            with st.expander("Debug - API Response"):
                st.json(response)
        
        # Extract response components
        summary = response.get('summary', '')
        data = response.get('data', [])
        chart_type = response.get('chart_type')
        metrics = response.get('metrics', {})
        recommendations = response.get('recommendations', [])
        
        # Format conversational response
        response_text = format_conversational_response(
            summary=summary,
            data=data,
            metrics=metrics,
            recommendations=recommendations,
            query_type=sanitized_query
        )
        
        # Add the response to chat history
        if response_text:
            add_chat_message("assistant", response_text)
        
        # Don't show separate visualizations - data is integrated in the response
        if chart_type and data:
            # Handle other chart types
            with st.container():
                st.markdown("---")
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
    
    except Exception as e:
        error_msg = f"I encountered an error processing your query: {str(e)}. Please try rephrasing your question."
        add_chat_message("assistant", error_msg)
        st.error(f"Error: {str(e)}")
        # Debug: Show the error (only if in debug mode)
        if st.session_state.get('debug_mode', False):
            import traceback
            with st.expander("Debug - Error Details"):
                st.write(f"Error: {str(e)}")
                st.code(traceback.format_exc())
    finally:
        # Don't clear any state here to preserve the chat
        pass

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
            Welcome. I'm your AI Diagnostic Assistant specializing in renewable energy asset performance analysis.
            
            I provide technical analysis of:
            - **Performance deviations** from 8760 model predictions using R² and RMSE metrics
            - **Financial impact quantification** of underperformance in monthly revenue terms
            - **Root cause identification** for operational issues affecting power generation
            - **Portfolio-level insights** including comparative analysis and trend identification
            
            Ask me about specific sites, performance thresholds, or portfolio-wide metrics. For example: "Which sites are underperforming?" or "Show me sites with RMSE above 2.0 MW."
            """)
    else:
        # Display chat history
        for message in st.session_state.chat_history:
            with st.chat_message(message['role'], avatar="🤖" if message['role'] == "assistant" else "👤"):
                st.markdown(message['content'])

# No separate visualization needed - all data is in the conversational response

# Input area with enhanced UI
st.markdown("---")

# Use a container for input without causing widget conflicts
user_input_container = st.container()

with user_input_container:
    col1, col2 = st.columns([5, 1])
    
    with col1:
        # Check if we should clear the input
        default_value = "" if st.session_state.get('clear_input', False) else None
        user_input = st.text_area(
            "Ask a question about your solar assets:",
            placeholder="E.g., Which sites are underperforming today?",
            label_visibility="collapsed",
            height=100,
            key="ai_query_input_main",
            value=default_value
        )
    
    with col2:
        st.write("")  # Spacer
        st.write("")  # Spacer
        send_button = st.button("🚀 Send", type="primary", use_container_width=True)
        voice_button = st.button("🎙️ Voice", use_container_width=True)

# Handle send button
if send_button and user_input and user_input.strip():
    # Immediately add user message to chat
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    
    st.session_state.chat_history.append({
        'role': 'user',
        'content': user_input
    })
    
    # Process API call
    try:
        # Call AI API
        response = api_client.query_ai_assistant(user_input)
        
        # Get the summary or generate response text
        summary = response.get('summary', '')
        data = response.get('data', [])
        
        # Create conversational response based on query type
        query_lower = user_input.lower()
        
        # If we have a summary from the AI, prioritize using it
        if summary and not summary.startswith('🎯 TOP'):  # Not the default underperformance summary
            response_text = summary
            # Add data details if available
            if data and isinstance(data, list) and len(data) > 0:
                response_text += "\n\n**Data Details:**\n"
                for item in data[:5]:
                    if isinstance(item, dict):
                        site_name = item.get('site_name', 'Unknown')
                        r_squared = item.get('r_squared', 0)
                        rmse = item.get('rmse', 0)
                        response_text += f"• {site_name}: R²={r_squared:.3f}, RMSE={rmse:.2f} MW\n"
        
        # Check for RMSE threshold queries
        elif 'rmse' in query_lower and ('above' in query_lower or 'over' in query_lower or 'greater' in query_lower):
            # Extract threshold if mentioned
            import re
            numbers = re.findall(r'\d+(?:\.\d+)?', user_input)
            threshold = float(numbers[0]) if numbers else 2.0
            
            # Filter data for sites above RMSE threshold
            if data:
                filtered_sites = [site for site in data if site.get('rmse', 0) > threshold]
                
                if filtered_sites:
                    response_text = f"Based on my analysis, {len(filtered_sites)} sites have RMSE above {threshold} MW:\n\n"
                    for site in filtered_sites:
                        site_name = site.get('site_name', 'Unknown')
                        rmse = site.get('rmse', 0)
                        r_squared = site.get('r_squared', 0)
                        revenue = site.get('revenue_impact', 0)
                        
                        response_text += f"**{site_name}**\n"
                        response_text += f"• RMSE: {rmse:.2f} MW (exceeds threshold by {rmse - threshold:.2f} MW)\n"
                        response_text += f"• R²: {r_squared:.3f}\n"
                        if revenue > 0:
                            response_text += f"• Revenue Impact: ${revenue:,.0f}/month\n"
                        response_text += "\n"
                    
                    response_text += f"These sites require immediate attention due to significant deviation from predicted performance."
                else:
                    response_text = f"Good news! No sites currently have RMSE above {threshold} MW. All sites are operating within acceptable deviation limits."
            else:
                response_text = summary if summary else "Unable to retrieve performance data at this time."
        
        # Check for R-squared queries
        elif 'r' in query_lower and ('squared' in query_lower or 'r2' in query_lower or 'r²' in query_lower):
            if 'below' in query_lower or 'less' in query_lower or 'under' in query_lower:
                # Extract threshold
                numbers = re.findall(r'0?\.\d+|\d+', user_input)
                threshold = float(numbers[0]) if numbers else 0.8
                if threshold > 1:
                    threshold = threshold / 100  # Convert percentage to decimal
                
                if data:
                    filtered_sites = [site for site in data if site.get('r_squared', 1) < threshold]
                    
                    if filtered_sites:
                        response_text = f"Sites with R² below {threshold}:\n\n"
                        for site in filtered_sites:
                            site_name = site.get('site_name', 'Unknown')
                            r_squared = site.get('r_squared', 0)
                            response_text += f"**{site_name}**: R²={r_squared:.3f}\n"
                    else:
                        response_text = f"All sites have R² above {threshold}, indicating good model correlation."
                else:
                    response_text = summary if summary else "Unable to retrieve R² data."
            else:
                response_text = summary if summary else "Please specify a threshold for R² analysis."
        
        # Default to summary for other queries
        else:
            response_text = summary if summary else "Based on my analysis:\n\n"
            if not summary and data:
                for idx, item in enumerate(data[:3], 1):
                    if isinstance(item, dict):
                        site_name = item.get('site_name', f'Site {idx}')
                        r_squared = item.get('r_squared', 0)
                        rmse = item.get('rmse', 0)
                        revenue = item.get('revenue_impact', 0)
                        response_text += f"**{site_name}**: R²={r_squared:.3f}, RMSE={rmse:.2f} MW"
                        if revenue > 0:
                            response_text += f" (${revenue:,.0f}/month)"
                        response_text += "\n"
        
        # Add assistant response to chat
        st.session_state.chat_history.append({
            'role': 'assistant',
            'content': response_text
        })
        
    except Exception as e:
        st.session_state.chat_history.append({
            'role': 'assistant',
            'content': f"Error: {str(e)}"
        })
    
    # Clear input and rerun
    st.session_state['clear_input'] = True
    st.rerun()
elif send_button:
    st.warning("Please enter a question before clicking Send.")

if voice_button:
    st.info("Voice input will be implemented")

# Reset the clear flag after the page loads
if st.session_state.get('clear_input', False):
    st.session_state['clear_input'] = False

# Process query from sidebar if one was selected
if query_to_process:
    # Initialize chat history if needed
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    
    # Add user message
    st.session_state.chat_history.append({
        'role': 'user',
        'content': query_to_process
    })
    
    # Process API call
    try:
        response = api_client.query_ai_assistant(query_to_process)
        summary = response.get('summary', '')
        data = response.get('data', [])
        
        # Use same logic as main query processing
        query_lower = query_to_process.lower()
        
        # Prioritize AI summary if available
        if summary and not summary.startswith('🎯 TOP'):
            response_text = summary
        # Check for RMSE queries
        elif 'rmse' in query_lower and 'above' in query_lower:
            import re
            numbers = re.findall(r'\d+(?:\.\d+)?', query_to_process)
            threshold = float(numbers[0]) if numbers else 2.0
            
            if data:
                filtered_sites = [site for site in data if site.get('rmse', 0) > threshold]
                if filtered_sites:
                    response_text = f"{len(filtered_sites)} sites have RMSE above {threshold} MW:\n\n"
                    for site in filtered_sites:
                        response_text += f"**{site.get('site_name')}**: RMSE={site.get('rmse'):.2f} MW\n"
                else:
                    response_text = f"No sites have RMSE above {threshold} MW."
            else:
                response_text = summary if summary else "Unable to retrieve data."
        else:
            response_text = summary if summary else "Unable to process query."
        
        st.session_state.chat_history.append({
            'role': 'assistant',
            'content': response_text
        })
    except Exception as e:
        st.session_state.chat_history.append({
            'role': 'assistant',
            'content': f"Error: {str(e)}"
        })
    
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