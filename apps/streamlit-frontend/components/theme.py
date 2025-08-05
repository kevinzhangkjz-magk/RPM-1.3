"""
Custom theme and styling for Streamlit application
Professional appearance with solar energy branding
"""

import streamlit as st


def apply_custom_theme() -> None:
    """
    Apply custom CSS theme to the Streamlit application.
    Creates a modern, professional appearance.
    """
    custom_css = """
    <style>
    /* Main color scheme - Custom palette */
    :root {
        --primary-color: #54b892;
        --secondary-color: #647cb2;
        --accent-color: #bd6821;
        --success-color: #54b892;
        --warning-color: #bd6821;
        --danger-color: #8c7f79;
        --dark-bg: #1b1b1b;
        --card-bg: #1b2437;
        --card-hover: #293653;
        --border-color: #5f5f5f;
        --text-primary: #ffffff;
        --text-secondary: #f0f0f0;
        --text-muted: #bfb5b8;
        --light-accent: #98a8cc;
        --lightest: #cbd3e5;
    }
    
    /* Improve overall appearance */
    .stApp {
        background: linear-gradient(180deg, var(--dark-bg) 0%, var(--card-bg) 100%);
        color: var(--text-primary);
    }
    
    /* Enhanced buttons */
    .stButton > button {
        background: linear-gradient(90deg, var(--primary-color) 0%, var(--secondary-color) 100%);
        color: var(--text-primary);
        border: none;
        padding: 0.5rem 1rem;
        font-weight: 600;
        border-radius: 8px;
        transition: all 0.3s ease;
        box-shadow: 0 2px 4px rgba(84, 184, 146, 0.2);
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0, 212, 255, 0.4);
    }
    
    /* Card styling */
    .element-container {
        transition: all 0.3s ease;
    }
    
    .element-container:hover {
        transform: translateY(-2px);
    }
    
    /* Metric cards */
    [data-testid="metric-container"] {
        background: var(--card-bg);
        padding: 1rem;
        border-radius: 12px;
        border: 1px solid var(--border-color);
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
    }
    
    /* Selectbox styling */
    .stSelectbox > div > div {
        background: var(--card-bg);
        border: 1px solid var(--border-color);
        border-radius: 8px;
    }
    
    /* DataFrame styling */
    .stDataFrame {
        border: 1px solid var(--border-color);
        border-radius: 8px;
        overflow: hidden;
    }
    
    /* Success/Warning/Error messages */
    .stAlert {
        border-radius: 8px;
        border-left: 4px solid;
    }
    
    .stSuccess {
        background: rgba(0, 255, 136, 0.1);
        border-left-color: var(--success-color);
    }
    
    .stWarning {
        background: rgba(255, 149, 0, 0.1);
        border-left-color: var(--warning-color);
    }
    
    .stError {
        background: rgba(255, 59, 48, 0.1);
        border-left-color: var(--danger-color);
    }
    
    /* Sidebar styling */
    .css-1d391kg {
        background: var(--card-bg);
    }
    
    /* Headers enhancement */
    h1, h2, h3 {
        background: linear-gradient(90deg, #00D4FF 0%, #FFB800 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    
    /* Loading spinner */
    .stSpinner > div {
        border-color: var(--primary-color) transparent transparent transparent;
    }
    
    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        background: var(--card-bg);
        border-radius: 8px;
        padding: 0.25rem;
    }
    
    .stTabs [data-baseweb="tab"] {
        border-radius: 6px;
        color: #FAFAFA;
        font-weight: 500;
    }
    
    .stTabs [aria-selected="true"] {
        background: var(--primary-color);
    }
    
    /* Progress bar */
    .stProgress > div > div {
        background: linear-gradient(90deg, var(--primary-color) 0%, var(--secondary-color) 100%);
    }
    
    /* Chat message styling */
    .stChatMessage {
        background: var(--card-bg);
        border-radius: 12px;
        padding: 1rem;
        margin: 0.5rem 0;
    }
    
    /* Custom animations */
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .element-container {
        animation: fadeIn 0.5s ease;
    }
    
    /* Responsive design */
    @media (max-width: 768px) {
        .stButton > button {
            width: 100%;
        }
        
        [data-testid="column"] {
            width: 100% !important;
            flex: 100% !important;
        }
    }
    </style>
    """
    
    st.markdown(custom_css, unsafe_allow_html=True)


def render_loading_animation() -> None:
    """
    Display a custom loading animation.
    """
    loading_html = """
    <div style="text-align: center; padding: 2rem;">
        <div class="solar-loader">
            <style>
                .solar-loader {
                    display: inline-block;
                    position: relative;
                    width: 80px;
                    height: 80px;
                }
                .solar-loader div {
                    position: absolute;
                    border: 4px solid #00D4FF;
                    opacity: 1;
                    border-radius: 50%;
                    animation: solar-loader 1.2s cubic-bezier(0, 0.2, 0.8, 1) infinite;
                }
                .solar-loader div:nth-child(2) {
                    animation-delay: -0.5s;
                }
                @keyframes solar-loader {
                    0% {
                        top: 36px;
                        left: 36px;
                        width: 0;
                        height: 0;
                        opacity: 1;
                    }
                    100% {
                        top: 0px;
                        left: 0px;
                        width: 72px;
                        height: 72px;
                        opacity: 0;
                    }
                }
            </style>
            <div></div>
            <div></div>
        </div>
        <p style="color: #00D4FF; margin-top: 1rem;">Loading solar data...</p>
    </div>
    """
    
    st.markdown(loading_html, unsafe_allow_html=True)


def render_metric_card(title: str, value: str, delta: str = None, delta_color: str = "normal") -> None:
    """
    Render a custom metric card with enhanced styling.
    
    Args:
        title: Metric title
        value: Metric value
        delta: Change indicator
        delta_color: Color for delta (normal, inverse, off)
    """
    st.metric(
        label=title,
        value=value,
        delta=delta,
        delta_color=delta_color
    )