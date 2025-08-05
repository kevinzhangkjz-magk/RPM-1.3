# RPM Streamlit Frontend

## Architecture Overview

### Multi-Page Navigation Structure
- **app.py**: Main entry point with home/landing page
- **pages/**: Streamlit's native multi-page app structure
  - `1_Portfolio.py`: Site portfolio listing
  - `2_Site_Detail.py`: Individual site performance
  - `3_Dashboard.py`: Customizable dashboard
  - `4_AI_Assistant.py`: AI chat interface

### Session State Management Strategy
```python
# Core session state structure
{
    'user_id': str,              # User identification
    'selected_site': str,         # Current site context
    'selected_skid': str,         # Current skid context
    'selected_inverter': str,     # Current inverter context
    'dashboard_layout': dict,     # User's dashboard configuration
    'chat_history': list,         # AI conversation history
    'filters': dict,              # Active data filters
    'cached_data': dict          # Temporary data cache
}
```

### Component Reusability Pattern
- **components/**: Reusable UI components
  - `charts.py`: Chart rendering functions (power curves, scatter plots, bar charts)
  - `widgets.py`: Dashboard widgets (leaderboard, alerts, metrics)
  - `chat.py`: Chat interface components
  - `navigation.py`: Breadcrumb and navigation helpers

### Deployment Architecture
- **Option 1**: Streamlit Cloud (Recommended for MVP)
  - Direct GitHub integration
  - Automatic deployments
  - Built-in secrets management
  
- **Option 2**: Docker Container
  - Dockerfile provided
  - Environment variable configuration
  - Scalable for production

## Development Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the app
streamlit run app.py
```

## API Integration
All API calls go through `lib/api_client.py` which handles:
- Authentication (JWT tokens)
- Error handling and retries
- Response caching
- WebSocket connections for real-time updates