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

# Header
st.title("🤖 AI Diagnostic Assistant")
st.markdown("Ask questions about your solar assets in natural language")

# Render breadcrumb
render_breadcrumb()

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
        "Which sites need immediate attention?"
    ]
    
    for question in performance_questions:
        if st.button(question, key=f"perf_{question[:20]}", use_container_width=True):
            st.session_state.ai_input = question
            st.rerun()
    
    st.markdown("#### 🔍 Diagnostics")
    diagnostic_questions = [
        "What's causing the performance drop at Site A?",
        "Show me the power curve for sites with low PR",
        "Identify sites with clipping issues",
        "Show me sites with communication errors",
        "Which inverters need maintenance?"
    ]
    
    for question in diagnostic_questions:
        if st.button(question, key=f"diag_{question[:20]}", use_container_width=True):
            st.session_state.ai_input = question
            st.rerun()
    
    st.markdown("#### 📈 Portfolio Overview")
    portfolio_questions = [
        "What's the total portfolio generation today?",
        "Show availability trends for the past week",
        "Compare inverter efficiency across all sites",
        "Monthly performance report",
        "Year-over-year comparison"
    ]
    
    predefined_questions = portfolio_questions
    
    for question in predefined_questions:
        if st.button(question, key=f"port_{question[:20]}", use_container_width=True):
            st.session_state.ai_input = question
            st.rerun()
    
    st.markdown("---")
    
    if st.button("🗑️ Clear Chat History", use_container_width=True):
        # Clear chat history from session state
        if 'chat_history' in st.session_state:
            st.session_state.chat_history = []
        st.rerun()
    
    st.markdown("---")
    
    st.markdown("### ⚙️ Settings")
    
    show_visualizations = st.checkbox("Show visualizations", value=True)
    show_raw_data = st.checkbox("Show raw data", value=False)
    auto_refresh = st.checkbox("Auto-refresh responses", value=False)

# Main chat interface
st.markdown("---")

# Chat history display
chat_container = st.container()

with chat_container:
    # Display chat history
    if 'chat_history' not in st.session_state or not st.session_state.chat_history:
        # Welcome message
        with st.chat_message("assistant", avatar="🤖"):
            st.markdown("""
            Hello! I'm your AI Diagnostic Assistant. I can help you:
            
            - 🔍 Analyze performance issues
            - 📊 Generate visualizations
            - 🏭 Compare site metrics
            - ⚡ Identify underperforming assets
            - 🛠️ Suggest maintenance actions
            
            Ask me anything about your solar portfolio!
            """)
    else:
        # Display chat history
        for message in st.session_state.chat_history:
            with st.chat_message(message['role'], avatar="🤖" if message['role'] == "assistant" else "👤"):
                st.markdown(message['content'])
                
                # Display visualizations if present in metadata
                if message.get('metadata') and show_visualizations:
                    metadata = message['metadata']
                    
                    # Check for chart data
                    if 'chart_type' in metadata and 'data' in metadata:
                        render_ai_visualization(
                            metadata['data'],
                            metadata['chart_type'],
                            metadata.get('columns', [])
                        )
                    
                    # Show raw data if requested
                    if show_raw_data and 'data' in metadata:
                        with st.expander("📋 View Raw Data"):
                            df = pd.DataFrame(metadata['data'])
                            st.dataframe(df, use_container_width=True)

# Input area
st.markdown("---")

# Use text input with session state
if 'ai_input' not in st.session_state:
    st.session_state.ai_input = ""

user_input = st.text_input(
    "Ask a question...",
    value=st.session_state.ai_input,
    placeholder="E.g., Which sites are underperforming today?",
    key="user_query",
    label_visibility="collapsed"
)

col1, col2, col3 = st.columns([1, 1, 4])

with col1:
    if st.button("🚀 Send", type="primary", use_container_width=True):
        if user_input:
            process_user_query(user_input, api_client)
            st.session_state.ai_input = ""  # Clear input
            st.rerun()

with col2:
    if st.button("🎙️ Voice Input", use_container_width=True):
        st.info("Voice input will be implemented")

# Functions
def format_underperformance_response(summary: str, data: Any, metrics: dict, recommendations: list) -> str:
    """
    Format response for underperformance queries with structured output.
    
    Args:
        summary: Original summary from API
        data: Performance data
        metrics: Performance metrics (R-squared, RMSE, etc.)
        recommendations: List of recommendations
    
    Returns:
        Formatted markdown response
    """
    formatted = []
    
    # Add header
    formatted.append("🎯 **UNDERPERFORMANCE ANALYSIS**\n")
    
    # Add summary if not already structured
    if summary and not summary.startswith("🎯"):
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
            # Add context for renewable energy queries
            enhanced_query = sanitized_query
            if is_underperformance_query:
                enhanced_query = f"{sanitized_query}. Please provide R-squared values, RMSE in MW, and financial impact if available. Format the response with clear rankings."
            
            # Create enhanced request with context
            response = api_client.query_ai_assistant_with_context(enhanced_query, context)
        
        # Extract response components
        summary = response.get('summary', 'I couldn\'t process that query.')
        data = response.get('data')
        chart_type = response.get('chart_type')
        columns = response.get('columns', [])
        metrics = response.get('metrics', {})
        recommendations = response.get('recommendations', [])
        
        # Format response for underperformance queries
        if is_underperformance_query and data:
            formatted_summary = format_underperformance_response(
                summary, data, metrics, recommendations
            )
            summary = formatted_summary
        
        # Add assistant response to history with metadata
        add_chat_message(
            "assistant",
            summary,
            metadata={
                'data': data,
                'chart_type': chart_type,
                'columns': columns,
                'metrics': metrics,
                'recommendations': recommendations
            }
        )
        
    except Exception as e:
        error_message = f"I encountered an error: {str(e)}. Please try rephrasing your question."
        add_chat_message("assistant", error_message)


def render_ai_visualization(data: Any, chart_type: str, columns: list) -> None:
    """
    Render visualization based on AI response data.
    Enhanced to support renewable energy performance metrics.
    
    Args:
        data: Data from AI response
        chart_type: Type of chart to render
        columns: Column names for the data
    """
    if not data:
        return
    
    # Convert to DataFrame
    df = pd.DataFrame(data)
    
    # Handle performance metrics visualization
    if chart_type == "performance_metrics":
        render_performance_metrics_chart(df)
        return
    
    # Handle financial impact visualization
    if chart_type == "financial_impact":
        render_financial_impact_chart(df)
        return
    
    if chart_type == "scatter":
        if len(columns) >= 2:
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=df[columns[0]] if columns[0] in df.columns else df.iloc[:, 0],
                y=df[columns[1]] if columns[1] in df.columns else df.iloc[:, 1],
                mode='markers',
                marker=dict(
                    color='#54b892',
                    size=8,
                    line=dict(width=1, color='#ffffff')
                ),
                hovertemplate='%{x}<br>%{y}<extra></extra>'
            ))
            
            fig.update_layout(
                xaxis_title=columns[0] if columns else "X Axis",
                yaxis_title=columns[1] if len(columns) > 1 else "Y Axis",
                height=400,
                paper_bgcolor='#1b2437',
                plot_bgcolor='#1b2437',
                font=dict(color='#f0f0f0'),
                xaxis=dict(gridcolor='#5f5f5f'),
                yaxis=dict(gridcolor='#5f5f5f')
            )
            
            st.plotly_chart(fig, use_container_width=True)
    
    elif chart_type == "bar":
        if columns:
            x_col = columns[0] if columns[0] in df.columns else df.columns[0]
            y_col = columns[1] if len(columns) > 1 and columns[1] in df.columns else df.columns[1]
            
            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=df[x_col],
                y=df[y_col],
                marker=dict(
                    color=df[y_col],
                    colorscale=[
                        [0, '#8c7f79'],
                        [0.5, '#647cb2'],
                        [1, '#54b892']
                    ],
                    line=dict(width=1, color='#ffffff')
                ),
                text=df[y_col].round(1) if df[y_col].dtype in ['float64', 'float32'] else df[y_col],
                textposition='outside',
                hovertemplate='%{x}<br>%{y}<extra></extra>'
            ))
            
            fig.update_layout(
                xaxis_title=x_col,
                yaxis_title=y_col,
                height=400,
                paper_bgcolor='#1b2437',
                plot_bgcolor='#1b2437',
                font=dict(color='#f0f0f0'),
                xaxis=dict(gridcolor='#5f5f5f'),
                yaxis=dict(gridcolor='#5f5f5f'),
                showlegend=False
            )
            
            st.plotly_chart(fig, use_container_width=True)
    
    elif chart_type == "multi-scatter":
        # Multiple series scatter plot
        fig = go.Figure()
        
        # Group by first column if it exists
        if columns and len(df.columns) > 2:
            groups = df[columns[0]].unique() if columns[0] in df.columns else df.iloc[:, 0].unique()
            
            for group in groups[:5]:  # Limit to 5 groups
                group_data = df[df[columns[0]] == group] if columns[0] in df.columns else df[df.iloc[:, 0] == group]
                
                fig.add_trace(go.Scatter(
                    x=group_data[columns[1]] if len(columns) > 1 and columns[1] in group_data.columns else group_data.iloc[:, 1],
                    y=group_data[columns[2]] if len(columns) > 2 and columns[2] in group_data.columns else group_data.iloc[:, 2],
                    mode='markers',
                    name=str(group),
                    marker=dict(size=8, line=dict(width=1, color='#ffffff')),
                    hovertemplate='%{x}<br>%{y}<extra></extra>'
                ))
        
        fig.update_layout(
            xaxis_title=columns[1] if len(columns) > 1 else "X Axis",
            yaxis_title=columns[2] if len(columns) > 2 else "Y Axis",
            height=400,
            paper_bgcolor='#1b2437',
            plot_bgcolor='#1b2437',
            font=dict(color='#f0f0f0'),
            xaxis=dict(gridcolor='#5f5f5f'),
            yaxis=dict(gridcolor='#5f5f5f'),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    else:
        # Enhanced table view for performance data
        if 'r_squared' in df.columns or 'rmse' in df.columns:
            # Style the dataframe for performance metrics
            styled_df = df.style.format({
                'r_squared': '{:.3f}',
                'rmse': '{:.2f}',
                'revenue_impact': '${:,.0f}',
                'capacity_factor': '{:.1%}',
                'availability': '{:.1%}'
            }, na_rep='N/A')
            
            # Apply color gradients for performance metrics
            if 'r_squared' in df.columns:
                styled_df = styled_df.background_gradient(
                    subset=['r_squared'],
                    cmap='RdYlGn',
                    vmin=0.5,
                    vmax=1.0
                )
            
            if 'rmse' in df.columns:
                styled_df = styled_df.background_gradient(
                    subset=['rmse'],
                    cmap='RdYlGn_r',
                    vmin=0,
                    vmax=5
                )
            
            st.dataframe(styled_df, use_container_width=True)
        else:
            # Default table view
            st.dataframe(df, use_container_width=True)


def render_performance_metrics_chart(df: pd.DataFrame) -> None:
    """
    Render specialized chart for performance metrics (R-squared vs RMSE).
    """
    if 'r_squared' in df.columns and 'rmse' in df.columns:
        fig = go.Figure()
        
        # Add scatter plot with custom styling
        fig.add_trace(go.Scatter(
            x=df['r_squared'],
            y=df['rmse'],
            mode='markers+text',
            text=df.get('site_name', df.index),
            textposition="top center",
            marker=dict(
                size=df.get('revenue_impact', 10).fillna(10) / 1000 if 'revenue_impact' in df.columns else 10,
                color=df['r_squared'],
                colorscale=[
                    [0, '#ff4444'],     # Red for low R²
                    [0.5, '#ffaa00'],   # Orange for medium
                    [1, '#44ff44']      # Green for high R²
                ],
                showscale=True,
                colorbar=dict(title="R²"),
                line=dict(width=1, color='#ffffff')
            ),
            hovertemplate=(
                "<b>%{text}</b><br>"
                "R²: %{x:.3f}<br>"
                "RMSE: %{y:.2f} MW<br>"
                "<extra></extra>"
            )
        ))
        
        # Add reference lines
        fig.add_hline(y=2.0, line_dash="dash", line_color="orange", 
                     annotation_text="RMSE Target: 2.0 MW")
        fig.add_vline(x=0.8, line_dash="dash", line_color="orange",
                     annotation_text="R² Target: 0.8")
        
        fig.update_layout(
            title="Site Performance: R² vs RMSE",
            xaxis_title="R² (Correlation)",
            yaxis_title="RMSE (MW)",
            height=500,
            paper_bgcolor='#1b2437',
            plot_bgcolor='#1b2437',
            font=dict(color='#f0f0f0'),
            xaxis=dict(gridcolor='#5f5f5f', range=[0, 1]),
            yaxis=dict(gridcolor='#5f5f5f'),
            showlegend=False
        )
        
        st.plotly_chart(fig, use_container_width=True)

def render_financial_impact_chart(df: pd.DataFrame) -> None:
    """
    Render financial impact waterfall or bar chart.
    """
    if 'revenue_impact' in df.columns:
        # Sort by revenue impact
        df_sorted = df.sort_values('revenue_impact', ascending=True)
        
        fig = go.Figure()
        
        # Create horizontal bar chart
        fig.add_trace(go.Bar(
            x=df_sorted['revenue_impact'],
            y=df_sorted.get('site_name', df_sorted.index),
            orientation='h',
            marker=dict(
                color=df_sorted['revenue_impact'],
                colorscale=[
                    [0, '#44ff44'],     # Green for low impact
                    [0.5, '#ffaa00'],   # Orange for medium
                    [1, '#ff4444']      # Red for high impact
                ],
                line=dict(width=1, color='#ffffff')
            ),
            text=['${:,.0f}'.format(x) for x in df_sorted['revenue_impact']],
            textposition='outside',
            hovertemplate=(
                "<b>%{y}</b><br>"
                "Revenue Impact: %{x:$,.0f}/month<br>"
                "<extra></extra>"
            )
        ))
        
        fig.update_layout(
            title="Monthly Revenue Impact by Site",
            xaxis_title="Revenue Impact ($/month)",
            yaxis_title="Site",
            height=max(400, len(df_sorted) * 40),
            paper_bgcolor='#1b2437',
            plot_bgcolor='#1b2437',
            font=dict(color='#f0f0f0'),
            xaxis=dict(gridcolor='#5f5f5f'),
            yaxis=dict(gridcolor='#5f5f5f'),
            showlegend=False,
            margin=dict(l=150)  # More space for site names
        )
        
        st.plotly_chart(fig, use_container_width=True)

# Footer with capabilities
with st.expander("🔍 AI Assistant Capabilities - Renewable Energy Asset Management"):
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