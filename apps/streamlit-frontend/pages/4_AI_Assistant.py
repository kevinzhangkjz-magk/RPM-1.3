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

# Add project root to path - handle both local and Streamlit Cloud
import os
current_dir = Path(__file__).parent

# Try multiple approaches to ensure imports work
if os.path.exists('/mount/src/rpm-1.3/apps/streamlit-frontend'):
    # Streamlit Cloud environment
    sys.path.insert(0, '/mount/src/rpm-1.3/apps/streamlit-frontend')
    # Also try adding lib and components directly
    sys.path.insert(0, '/mount/src/rpm-1.3/apps/streamlit-frontend/lib')
    sys.path.insert(0, '/mount/src/rpm-1.3/apps/streamlit-frontend/components')
else:
    # Local environment
    parent_dir = current_dir.parent
    sys.path.insert(0, str(parent_dir))
    sys.path.insert(0, str(parent_dir.absolute()))

# Import with explicit module paths as fallback
try:
    from lib.session_state_isolated import (
        initialize_session_state,
        add_chat_message,
        get_session_value
    )
    from lib.api_client_refactored import get_api_client
    from lib.auth_manager import check_and_redirect_auth
    from lib.security import input_sanitizer
    from components.navigation import render_breadcrumb
    from components.charts import render_performance_scatter
    import components.theme as theme
except ImportError:
    # Try direct imports if lib is not recognized as a package
    import session_state_isolated
    import api_client_refactored
    import auth_manager
    import security
    from navigation import render_breadcrumb
    from charts import render_performance_scatter
    import theme
    
    # Reassign for consistency
    initialize_session_state = session_state_isolated.initialize_session_state
    add_chat_message = session_state_isolated.add_chat_message
    get_session_value = session_state_isolated.get_session_value
    get_api_client = api_client_refactored.get_api_client
    check_and_redirect_auth = auth_manager.check_and_redirect_auth
    input_sanitizer = security.input_sanitizer

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
    
    predefined_questions = [
        "Which sites are underperforming today?",
        "Show me the power curve for sites with low PR",
        "What's causing the performance drop at Site A?",
        "Compare inverter efficiency across all sites",
        "Which inverters need maintenance?",
        "Show availability trends for the past week",
        "What's the total portfolio generation today?",
        "Identify sites with clipping issues",
        "Show me sites with communication errors"
    ]
    
    for question in predefined_questions:
        if st.button(question, key=f"q_{question[:20]}", use_container_width=True):
            st.session_state.ai_input = question
    
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
def process_user_query(query: str, api_client) -> None:
    """
    Process user query through AI API and display response.
    
    Args:
        query: User's natural language query
        api_client: API client for AI endpoint
    """
    # Add user message to history
    add_chat_message("user", query)
    
    try:
        # Call AI API with real query
        with st.spinner("Thinking..."):
            response = api_client.query_ai_assistant(query)
        
        # Extract response components
        summary = response.get('summary', 'I couldn\'t process that query.')
        data = response.get('data')
        chart_type = response.get('chart_type')
        columns = response.get('columns', [])
        
        # Add assistant response to history with metadata
        add_chat_message(
            "assistant",
            summary,
            metadata={
                'data': data,
                'chart_type': chart_type,
                'columns': columns
            }
        )
        
    except Exception as e:
        error_message = f"I encountered an error: {str(e)}. Please try rephrasing your question."
        add_chat_message("assistant", error_message)


def render_ai_visualization(data: Any, chart_type: str, columns: list) -> None:
    """
    Render visualization based on AI response data.
    
    Args:
        data: Data from AI response
        chart_type: Type of chart to render
        columns: Column names for the data
    """
    if not data:
        return
    
    # Convert to DataFrame
    df = pd.DataFrame(data)
    
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
        # Default table view
        st.dataframe(df, use_container_width=True)


# Footer with capabilities
with st.expander("🔍 AI Assistant Capabilities"):
    st.markdown("""
    ### What I can do:
    
    **Performance Analysis**
    - Identify underperforming sites and equipment
    - Analyze power curves and performance ratios
    - Detect clipping and curtailment issues
    
    **Diagnostics**
    - Troubleshoot performance drops
    - Identify equipment failures
    - Suggest maintenance actions
    
    **Data Visualization**
    - Generate custom charts and graphs
    - Create comparative analyses
    - Show trends and patterns
    
    **Reporting**
    - Summarize portfolio performance
    - Generate efficiency reports
    - Track KPIs and metrics
    
    ### Tips for better results:
    - Be specific about time ranges (e.g., "last week", "today")
    - Mention specific sites or equipment when relevant
    - Ask for visualizations when you want charts
    - Use technical terms like PR, availability, capacity factor
    """)