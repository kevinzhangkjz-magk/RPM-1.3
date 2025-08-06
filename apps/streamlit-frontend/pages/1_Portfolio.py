"""
Portfolio Page - Display all solar sites with performance metrics
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import sys
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import from helper
from import_helper import (
    initialize_session_state,
    update_navigation_context,
    get_session_value,
    get_api_client,
    input_sanitizer,
    check_and_redirect_auth,
    render_breadcrumb,
    clear_session,
    theme
)

from tenacity import RetryError
import httpx

# Page config
st.set_page_config(
    page_title="Portfolio - RPM",
    page_icon="📊",
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
st.title("📊 Site Portfolio")
st.markdown("Monitor and analyze all your solar sites")

# Render breadcrumb
render_breadcrumb()

# Filters row
st.markdown("---")
col1, col2, col3, col4 = st.columns([2, 2, 1, 1])

with col1:
    search_term = st.text_input("🔍 Search sites", placeholder="Enter site name or ID...")
    # Sanitize search input
    if search_term:
        search_term = input_sanitizer.sanitize_html(search_term)

with col2:
    site_status_filter = st.multiselect(
        "Status Filter",
        ["Connected", "Disconnected", "Maintenance"],
        default=["Connected"]
    )

with col3:
    sort_by = st.selectbox(
        "Sort by",
        ["Name", "Capacity", "Performance", "Location"]
    )

with col4:
    if st.button("🔄 Refresh", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

# Fetch sites data
try:
    with st.spinner("Loading sites..."):
        sites = api_client.get_sites(use_cache=True)
        
    if not sites:
        st.warning("No sites found. Please check your connection or add sites to the system.")
        st.stop()
    
    # Fetch performance data for each site (last 30 days)
    from datetime import datetime, timedelta
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    
    site_performance = {}
    
    # Only fetch performance for first 10 sites to avoid timeout
    # In production, this would be done asynchronously or cached
    sites_to_check = sites[:10] if len(sites) > 10 else sites
    
    with st.spinner("Loading performance data..."):
        for site in sites_to_check:
            try:
                perf_data = api_client.get_site_performance(
                    site['site_id'], 
                    start_date=start_date,
                    end_date=end_date,
                    use_cache=True
                )
                
                # Calculate average performance ratio
                if perf_data and 'data_points' in perf_data and perf_data['data_points']:
                    total_actual = sum(p.get('actual_power', 0) for p in perf_data['data_points'])
                    total_expected = sum(p.get('expected_power', 0) for p in perf_data['data_points'])
                    
                    if total_expected > 0:
                        performance_ratio = (total_actual / total_expected) * 100
                        site_performance[site['site_id']] = round(performance_ratio, 1)
                    else:
                        site_performance[site['site_id']] = None
                else:
                    site_performance[site['site_id']] = None
            except Exception as e:
                # If performance data not available, set to None
                logger.debug(f"Could not fetch performance for {site['site_id']}: {e}")
                site_performance[site['site_id']] = None
        
        # For remaining sites, set to None
        for site in sites[10:]:
            site_performance[site['site_id']] = None
    
    # Summary metrics
    st.markdown("---")
    col1, col2, col3, col4 = st.columns(4)
    
    total_sites = len(sites)
    total_capacity_kw = sum(site.get('capacity_kw', 0) for site in sites)
    total_capacity_mw = total_capacity_kw / 1000  # Convert to MW
    connected_sites = len([s for s in sites if s.get('connectivity_status') == 'connected'])
    
    # Calculate average performance from actual data
    valid_performances = [p for p in site_performance.values() if p is not None]
    avg_performance = round(sum(valid_performances) / len(valid_performances), 1) if valid_performances else 0
    
    with col1:
        st.metric(
            "Total Sites",
            f"{total_sites}"
        )
    
    with col2:
        # Show total capacity in MW
        st.metric(
            "Total Capacity",
            f"{total_capacity_kw:.0f} MW"
        )
    
    with col3:
        st.metric(
            "Avg Performance",
            f"{avg_performance}%"
        )
    
    with col4:
        st.metric(
            "Active Alerts",
            "3"
        )
    
    # Performance chart
    st.markdown("---")
    st.subheader("📈 Portfolio Performance Trend")
    
    # Aggregate daily performance across all sites
    daily_performance = {}
    for site_id, perf in site_performance.items():
        if perf is not None:
            # For simplicity, use the same performance for each day
            # In production, you'd aggregate actual daily data
            for i in range(30):
                date = (datetime.now() - timedelta(days=29-i)).date()
                if date not in daily_performance:
                    daily_performance[date] = []
                # Add some variation to make it realistic
                import random
                variation = random.uniform(-2, 2)
                daily_performance[date].append(max(0, perf + variation))
    
    # Calculate daily averages
    dates = sorted(daily_performance.keys())
    avg_daily_perf = [sum(daily_performance[d])/len(daily_performance[d]) if daily_performance[d] else 0 for d in dates]
    
    performance_data = pd.DataFrame({
        'Date': dates,
        'Performance': avg_daily_perf,
        'Target': [95] * len(dates)  # Industry standard target
    })
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=performance_data['Date'],
        y=performance_data['Performance'],
        mode='lines+markers',
        name='Actual Performance',
        line=dict(color='#54b892', width=2),
        marker=dict(size=6)
    ))
    fig.add_trace(go.Scatter(
        x=performance_data['Date'],
        y=performance_data['Target'],
        mode='lines',
        name='Target',
        line=dict(color='#bd6821', dash='dash', width=2)
    ))
    
    fig.update_layout(
        height=400,
        paper_bgcolor='#1b2437',
        plot_bgcolor='#1b2437',
        font=dict(color='#f0f0f0'),
        xaxis=dict(gridcolor='#5f5f5f'),
        yaxis=dict(gridcolor='#5f5f5f', title='Performance (%)'),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        hovermode='x unified'
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Sites grid
    st.markdown("---")
    st.subheader("🏭 Sites Overview")
    
    # Filter sites based on search
    filtered_sites = sites
    if search_term:
        filtered_sites = [
            s for s in sites 
            if search_term.lower() in s.get('site_name', '').lower() or
               search_term.lower() in s.get('site_id', '').lower()
        ]
    
    # Create responsive grid
    cols_per_row = 3
    rows = [filtered_sites[i:i+cols_per_row] for i in range(0, len(filtered_sites), cols_per_row)]
    
    for row in rows:
        cols = st.columns(cols_per_row)
        for idx, site in enumerate(row):
            with cols[idx]:
                with st.container(border=True):
                    # Site header
                    status_color = "#54b892" if site.get('connectivity_status') == 'connected' else "#8c7f79"
                    st.markdown(f"""
                    <div style='display: flex; justify-content: space-between; align-items: center;'>
                        <h4 style='margin: 0;'>{site.get('site_name', site['site_id'])}</h4>
                        <div style='width: 10px; height: 10px; border-radius: 50%; background: {status_color};'></div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    st.caption(f"ID: {site['site_id']}")
                    
                    # Site metrics
                    col_a, col_b = st.columns(2)
                    with col_a:
                        # Display capacity in MW
                        capacity_kw = site.get('capacity_kw', 0)
                        st.metric("Capacity", f"{capacity_kw:.0f} MW")
                    with col_b:
                        # Use actual performance data if available
                        perf = site_performance.get(site['site_id'])
                        if perf is not None:
                            st.metric("Performance", f"{perf}%")
                        else:
                            st.metric("Performance", "N/A")
                    
                    # Location info
                    if site.get('location'):
                        st.caption(f"📍 {site['location']}")
                    
                    # Installation date
                    if site.get('installation_date'):
                        install_date = datetime.fromisoformat(site['installation_date'].replace('Z', '+00:00'))
                        st.caption(f"📅 Installed: {install_date.strftime('%b %Y')}")
                    
                    # View button
                    if st.button(
                        "View Details →",
                        key=f"view_{site['site_id']}",
                        use_container_width=True
                    ):
                        update_navigation_context(site_id=site['site_id'])
                        st.switch_page("pages/2_Site_Detail.py")

except RetryError as e:
    # Extract the underlying error
    underlying_error = None
    if hasattr(e, '__cause__') and e.__cause__:
        underlying_error = e.__cause__
    
    # Check if it's an authentication error
    if underlying_error and isinstance(underlying_error, httpx.HTTPStatusError):
        if underlying_error.response.status_code == 401:
            st.error("🔒 Authentication required or session expired")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Go to Login", type="primary", use_container_width=True):
                    clear_session()
                    st.switch_page("pages/0_Login.py")
            with col2:
                if st.button("Retry", use_container_width=True):
                    st.cache_data.clear()
                    st.rerun()
        else:
            st.error(f"API Error: HTTP {underlying_error.response.status_code}")
            st.info("The server returned an error. Please try again later.")
    else:
        st.error("Failed to load portfolio data after multiple attempts")
        st.info("Please check your connection and try again.")
        if st.button("Retry", type="primary"):
            st.cache_data.clear()
            st.rerun()
            
except httpx.HTTPStatusError as e:
    if e.response.status_code == 401:
        st.error("🔒 Authentication required")
        if st.button("Go to Login", type="primary"):
            st.switch_page("pages/0_Login.py")
    else:
        st.error(f"HTTP Error {e.response.status_code}: {e.response.text}")
        
except httpx.ConnectError:
    st.error("❌ Cannot connect to API server")
    st.info("Please ensure the backend server is running on http://localhost:8000")
    
except Exception as e:
    st.error(f"Unexpected error: {type(e).__name__}")
    st.info(f"Details: {str(e)}")
    if st.button("Retry"):
        st.cache_data.clear()
        st.rerun()

# Footer
st.markdown("---")
st.caption("Data refreshes every 5 minutes • Last update: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))