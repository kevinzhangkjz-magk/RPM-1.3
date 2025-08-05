"""
Chart components for data visualization
Uses real data from API/Redshift database
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta


def render_power_curve(performance_data: Dict[str, Any], 
                      availability_filter: bool = False) -> None:
    """
    Render power curve visualization from real performance data.
    
    Args:
        performance_data: Performance data from API containing irradiance and power readings
        availability_filter: Whether to filter for 100% availability periods
    """
    if not performance_data or 'data' not in performance_data:
        st.warning("No performance data available for power curve")
        return
    
    # Extract real data from API response
    df = pd.DataFrame(performance_data['data'])
    
    # Required columns from database: irradiance, power_output, expected_power, availability
    if not all(col in df.columns for col in ['irradiance', 'power_output']):
        st.error("Missing required data columns for power curve")
        return
    
    fig = go.Figure()
    
    # Plot expected power curve if available
    if 'expected_power' in df.columns:
        fig.add_trace(go.Scatter(
            x=df['irradiance'],
            y=df['expected_power'],
            mode='lines',
            name='Expected Power',
            line=dict(color='#647cb2', width=2, dash='dash')
        ))
    
    # Apply availability filter if requested
    plot_data = df
    if availability_filter and 'availability' in df.columns:
        plot_data = df[df['availability'] >= 100.0]
        
    # Plot actual power output
    fig.add_trace(go.Scatter(
        x=plot_data['irradiance'],
        y=plot_data['power_output'],
        mode='markers',
        name='Actual Power',
        marker=dict(
            color='#54b892',
            size=6,
            opacity=0.7,
            line=dict(width=1, color='#ffffff')
        ),
        text=[f"Time: {row.get('timestamp', 'N/A')}<br>"
              f"Irradiance: {row['irradiance']:.1f} W/m²<br>"
              f"Power: {row['power_output']:.1f} kW<br>"
              f"Availability: {row.get('availability', 'N/A')}%"
              for _, row in plot_data.iterrows()],
        hovertemplate='%{text}<extra></extra>'
    ))
    
    # Add trend line
    if len(plot_data) > 10:
        z = np.polyfit(plot_data['irradiance'], plot_data['power_output'], 2)
        p = np.poly1d(z)
        x_trend = np.linspace(plot_data['irradiance'].min(), plot_data['irradiance'].max(), 100)
        fig.add_trace(go.Scatter(
            x=x_trend,
            y=p(x_trend),
            mode='lines',
            name='Trend',
            line=dict(color='#bd6821', width=2),
            opacity=0.8
        ))
    
    fig.update_layout(
        title="Power Curve Analysis",
        xaxis_title="Irradiance (W/m²)",
        yaxis_title="Power Output (kW)",
        height=500,
        paper_bgcolor='#1b2437',
        plot_bgcolor='#1b2437',
        font=dict(color='#f0f0f0'),
        xaxis=dict(
            gridcolor='#5f5f5f',
            zeroline=True,
            zerolinecolor='#5f5f5f'
        ),
        yaxis=dict(
            gridcolor='#5f5f5f',
            zeroline=True,
            zerolinecolor='#5f5f5f'
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        hovermode='closest'
    )
    
    st.plotly_chart(fig, use_container_width=True)


def render_performance_scatter(performance_data: Dict[str, Any],
                              x_axis: str = 'timestamp',
                              y_axis: str = 'performance_ratio',
                              color_by: Optional[str] = None) -> None:
    """
    Render scatter plot of performance metrics from real data.
    
    Args:
        performance_data: Performance data from API
        x_axis: Column to use for x-axis
        y_axis: Column to use for y-axis
        color_by: Optional column to color points by
    """
    if not performance_data or 'data' not in performance_data:
        st.warning("No performance data available")
        return
    
    df = pd.DataFrame(performance_data['data'])
    
    # Validate columns exist
    if x_axis not in df.columns or y_axis not in df.columns:
        st.error(f"Required columns not found. Available: {', '.join(df.columns)}")
        return
    
    # Convert timestamp if needed
    if x_axis == 'timestamp' and x_axis in df.columns:
        df[x_axis] = pd.to_datetime(df[x_axis])
    
    fig = go.Figure()
    
    if color_by and color_by in df.columns:
        # Create scatter with color scale
        fig.add_trace(go.Scatter(
            x=df[x_axis],
            y=df[y_axis],
            mode='markers',
            marker=dict(
                color=df[color_by],
                colorscale=[
                    [0, '#8c7f79'],
                    [0.5, '#647cb2'],
                    [1, '#54b892']
                ],
                size=8,
                colorbar=dict(
                    title=color_by.replace('_', ' ').title(),
                    titlefont=dict(color='#f0f0f0'),
                    tickfont=dict(color='#f0f0f0')
                ),
                line=dict(width=1, color='#ffffff')
            ),
            text=[f"{x_axis}: {row[x_axis]}<br>"
                  f"{y_axis}: {row[y_axis]:.2f}<br>"
                  f"{color_by}: {row[color_by]:.2f}"
                  for _, row in df.iterrows()],
            hovertemplate='%{text}<extra></extra>'
        ))
    else:
        fig.add_trace(go.Scatter(
            x=df[x_axis],
            y=df[y_axis],
            mode='markers',
            marker=dict(
                color='#54b892',
                size=8,
                line=dict(width=1, color='#ffffff')
            ),
            text=[f"{x_axis}: {row[x_axis]}<br>"
                  f"{y_axis}: {row[y_axis]:.2f}"
                  for _, row in df.iterrows()],
            hovertemplate='%{text}<extra></extra>'
        ))
    
    # Add average line
    avg_y = df[y_axis].mean()
    fig.add_hline(
        y=avg_y,
        line_dash="dash",
        line_color="#bd6821",
        annotation_text=f"Avg: {avg_y:.2f}",
        annotation_position="right"
    )
    
    fig.update_layout(
        title=f"{y_axis.replace('_', ' ').title()} Analysis",
        xaxis_title=x_axis.replace('_', ' ').title(),
        yaxis_title=y_axis.replace('_', ' ').title(),
        height=500,
        paper_bgcolor='#1b2437',
        plot_bgcolor='#1b2437',
        font=dict(color='#f0f0f0'),
        xaxis=dict(gridcolor='#5f5f5f'),
        yaxis=dict(gridcolor='#5f5f5f'),
        hovermode='closest'
    )
    
    st.plotly_chart(fig, use_container_width=True)


def render_time_series(performance_data: Dict[str, Any],
                       metrics: List[str] = ['power_output'],
                       date_range: Optional[tuple] = None) -> None:
    """
    Render time series chart from real performance data.
    
    Args:
        performance_data: Performance data from API
        metrics: List of metrics to plot
        date_range: Optional tuple of (start_date, end_date)
    """
    if not performance_data or 'data' not in performance_data:
        st.warning("No time series data available")
        return
    
    df = pd.DataFrame(performance_data['data'])
    
    # Ensure timestamp column exists and convert
    if 'timestamp' not in df.columns:
        st.error("Timestamp column not found in data")
        return
    
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df = df.sort_values('timestamp')
    
    # Apply date range filter if provided
    if date_range and len(date_range) == 2:
        start_date, end_date = date_range
        df = df[(df['timestamp'] >= pd.to_datetime(start_date)) & 
                (df['timestamp'] <= pd.to_datetime(end_date))]
    
    fig = go.Figure()
    
    # Color palette for multiple metrics
    colors = ['#54b892', '#647cb2', '#bd6821', '#8c7f79', '#98a8cc']
    
    for idx, metric in enumerate(metrics):
        if metric in df.columns:
            fig.add_trace(go.Scatter(
                x=df['timestamp'],
                y=df[metric],
                mode='lines',
                name=metric.replace('_', ' ').title(),
                line=dict(color=colors[idx % len(colors)], width=2),
                hovertemplate='%{x}<br>%{y:.2f}<extra></extra>'
            ))
    
    fig.update_layout(
        title="Performance Time Series",
        xaxis_title="Time",
        yaxis_title="Value",
        height=400,
        paper_bgcolor='#1b2437',
        plot_bgcolor='#1b2437',
        font=dict(color='#f0f0f0'),
        xaxis=dict(
            gridcolor='#5f5f5f',
            rangeslider=dict(visible=True, bgcolor='#293653'),
            type='date'
        ),
        yaxis=dict(gridcolor='#5f5f5f'),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        hovermode='x unified'
    )
    
    st.plotly_chart(fig, use_container_width=True)


def render_performance_heatmap(performance_data: Dict[str, Any],
                               aggregate_by: str = 'hour_day') -> None:
    """
    Render performance heatmap from real data.
    
    Args:
        performance_data: Performance data from API
        aggregate_by: How to aggregate ('hour_day', 'day_month', etc.)
    """
    if not performance_data or 'data' not in performance_data:
        st.warning("No data available for heatmap")
        return
    
    df = pd.DataFrame(performance_data['data'])
    
    if 'timestamp' not in df.columns or 'performance_ratio' not in df.columns:
        st.error("Required columns not found for heatmap")
        return
    
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    if aggregate_by == 'hour_day':
        df['hour'] = df['timestamp'].dt.hour
        df['day'] = df['timestamp'].dt.day_name()
        
        # Pivot for heatmap
        pivot = df.pivot_table(
            values='performance_ratio',
            index='day',
            columns='hour',
            aggfunc='mean'
        )
        
        # Reorder days
        days_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        pivot = pivot.reindex([d for d in days_order if d in pivot.index])
        
        fig = go.Figure(data=go.Heatmap(
            z=pivot.values,
            x=pivot.columns,
            y=pivot.index,
            colorscale=[
                [0, '#8c7f79'],
                [0.5, '#647cb2'],
                [1, '#54b892']
            ],
            text=pivot.values.round(1),
            texttemplate='%{text}%',
            textfont={"size": 10},
            colorbar=dict(
                title="Performance %",
                titlefont=dict(color='#f0f0f0'),
                tickfont=dict(color='#f0f0f0')
            ),
            hovertemplate='Day: %{y}<br>Hour: %{x}<br>Performance: %{z:.1f}%<extra></extra>'
        ))
        
        fig.update_layout(
            title="Performance Heatmap - By Hour and Day",
            xaxis_title="Hour of Day",
            yaxis_title="Day of Week",
            height=400,
            paper_bgcolor='#1b2437',
            plot_bgcolor='#1b2437',
            font=dict(color='#f0f0f0'),
            xaxis=dict(
                tickmode='linear',
                tick0=0,
                dtick=1
            )
        )
    
    st.plotly_chart(fig, use_container_width=True)


def render_comparison_bar_chart(sites_data: List[Dict],
                                metric: str = 'performance_ratio',
                                top_n: int = 10) -> None:
    """
    Render comparison bar chart for multiple sites using real data.
    
    Args:
        sites_data: List of site performance data from API
        metric: Metric to compare
        top_n: Number of top sites to show
    """
    if not sites_data:
        st.warning("No sites data available for comparison")
        return
    
    # Extract metric for each site
    comparison_data = []
    for site in sites_data:
        if metric in site:
            comparison_data.append({
                'site_name': site.get('site_name', site.get('site_id', 'Unknown')),
                'value': site[metric]
            })
    
    if not comparison_data:
        st.error(f"Metric '{metric}' not found in sites data")
        return
    
    # Sort and take top N
    df = pd.DataFrame(comparison_data)
    df = df.nlargest(top_n, 'value')
    
    fig = go.Figure(data=[
        go.Bar(
            x=df['site_name'],
            y=df['value'],
            marker=dict(
                color=df['value'],
                colorscale=[
                    [0, '#8c7f79'],
                    [0.5, '#647cb2'],
                    [1, '#54b892']
                ],
                line=dict(width=1, color='#ffffff')
            ),
            text=df['value'].round(1),
            textposition='outside',
            hovertemplate='%{x}<br>%{y:.1f}<extra></extra>'
        )
    ])
    
    fig.update_layout(
        title=f"Top {top_n} Sites by {metric.replace('_', ' ').title()}",
        xaxis_title="Site",
        yaxis_title=metric.replace('_', ' ').title(),
        height=400,
        paper_bgcolor='#1b2437',
        plot_bgcolor='#1b2437',
        font=dict(color='#f0f0f0'),
        xaxis=dict(gridcolor='#5f5f5f'),
        yaxis=dict(gridcolor='#5f5f5f'),
        showlegend=False
    )
    
    st.plotly_chart(fig, use_container_width=True)