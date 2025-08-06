# Local Testing Guide for RPM 1.3

## Prerequisites

### 1. Python Environment
- Python 3.11 or higher
- Virtual environment (recommended)

### 2. Database Requirements
- PostgreSQL or AWS Redshift connection (for full functionality)
- Or use mock data mode for testing without database

## Step 1: Environment Setup

### 1.1 Clone and Navigate to Project
```bash
cd /Users/kevz/Documents/GitHub/rpm/RPM-1.3
```

### 1.2 Create and Activate Virtual Environment
```bash
# Create virtual environment if not exists
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
# venv\Scripts\activate
```

### 1.3 Install Dependencies
```bash
# Install backend dependencies
cd apps/backend
pip install -r requirements.txt
pip install scipy numpy pandas  # Additional dependencies for story 4.2

# Install frontend dependencies (if needed)
cd ../streamlit-frontend
pip install -r requirements.txt
```

## Step 2: Configuration

### 2.1 Create Environment File
Create `.env` file in the project root with the following content:
```bash
# PPA Rate Configuration
DEFAULT_PPA_RATE=50.0
SITE_PPA_RATES='{"assembly_2": 48.50, "highland": 52.00, "asmb1": 47.00, "asmb2": 48.50}'

# API Configuration
API_BASE_URL=http://localhost:8001
STREAMLIT_BASE_URL=http://localhost:8502

# Database Configuration (optional - for full functionality)
REDSHIFT_HOST=your-redshift-host
REDSHIFT_PORT=5439
REDSHIFT_DB=your-database
REDSHIFT_USER=your-username
REDSHIFT_PASSWORD=your-password
REDSHIFT_SCHEMA=analytics

# For testing without database, set:
USE_MOCK_DATA=true
```

### 2.2 Create Financial Configuration (Optional)
Create `financial_config.json` in apps/backend/src/core/:
```json
{
  "default_ppa_rate": 50.0,
  "site_ppa_rates": {
    "assembly_2": 48.50,
    "highland": 52.00,
    "asmb1": 47.00,
    "asmb2": 48.50
  }
}
```

## Step 3: Start Backend Server

### 3.1 Navigate to Backend Directory
```bash
cd /Users/kevz/Documents/GitHub/rpm/RPM-1.3/apps/backend
```

### 3.2 Start FastAPI Server
```bash
# Start with auto-reload for development
python -m uvicorn main:app --reload --port 8001

# Or without reload for testing
python -m uvicorn main:app --port 8001
```

### 3.3 Verify Backend is Running
```bash
# In a new terminal, test the health endpoint
curl http://localhost:8001/health

# Should return: {"status":"healthy"}
```

## Step 4: Start Streamlit Frontend

### 4.1 Open New Terminal and Navigate to Frontend
```bash
cd /Users/kevz/Documents/GitHub/rpm/RPM-1.3/apps/streamlit-frontend
source ../../venv/bin/activate  # Activate virtual environment
```

### 4.2 Start Streamlit Application
```bash
streamlit run Home.py --server.port 8502
```

### 4.3 Access the Application
Open your browser and navigate to: http://localhost:8502

## Step 5: Testing Story 4.2 Features

### 5.1 Test AI Assistant Page
1. Navigate to "AI Assistant" in the sidebar
2. Test these queries:
   - "Give me the 3 most underperforming sites"
   - "What is the R-squared for Assembly 2?"
   - "Show sites with RMSE greater than 2.0"
   - "Calculate revenue impact for Highland site"
3. Verify responses include:
   - R-squared values
   - RMSE calculations
   - Financial impact (using PPA rates)
   - Alert levels (CRITICAL/WARNING/MONITOR/GOOD)

### 5.2 Test Settings Page
1. Navigate to "Settings" in the sidebar
2. Go to "Financial" tab
3. Verify:
   - Default PPA rate shows $50.0/MWh
   - Site-specific rates are displayed
   - Revenue Impact Calculator works
4. Try modifying rates and saving

### 5.3 Test Dashboard Widgets
1. Go to main Dashboard page
2. Check for these widgets:
   - Performance Leaderboard
   - Active Alerts
   - Power Curve Analysis
   - KPI Summary
   - Site Comparison
   - Predictive Maintenance

### 5.4 Test Export Functionality
1. From AI Assistant or Dashboard
2. Look for export buttons
3. Test export formats:
   - JSON
   - CSV
   - Excel
   - PDF

## Step 6: Run Automated Tests

### 6.1 Run Comprehensive Test Suite
```bash
cd /Users/kevz/Documents/GitHub/rpm/RPM-1.3
python test_4_2_features.py
```

Expected output:
```
✓ PASSED: PPA Rates Configuration
✓ PASSED: Performance Metrics
✓ PASSED: Query Sanitization
✓ PASSED: Export Formats
✓ PASSED: AI Query Types
✓ PASSED: Dashboard Widgets

Overall: 6/6 tests passed
```

### 6.2 Run Backend Unit Tests
```bash
cd apps/backend
python -m pytest tests/ -v
```

Expected: ~110 out of 126 tests should pass (87%)

### 6.3 Test Query Sanitization
```bash
cd /Users/kevz/Documents/GitHub/rpm/RPM-1.3
python test_sanitization.py
```

## Step 7: Performance Testing

### 7.1 Check Response Times
```bash
# Test AI query endpoint
time curl -X POST http://localhost:8001/api/query \
  -H "Content-Type: application/json" \
  -d '{"query": "give me the 3 most underperforming sites", "context": {}}'
```
Response should be < 3 seconds

### 7.2 Monitor Resource Usage
```bash
# While application is running, monitor CPU and memory
top | grep -E 'python|streamlit'
```

## Step 8: Security Testing

### 8.1 Test SQL Injection Prevention
Try these malicious queries in AI Assistant:
- "DROP TABLE sites; SELECT * FROM users"
- "DELETE FROM data WHERE 1=1"
- "'; UNION SELECT passwords FROM users--"

All should be sanitized and return safe responses.

### 8.2 Test Input Validation
1. Try entering very long queries (>500 characters)
2. Try special characters and scripts
3. Verify all are handled safely

## Step 9: Mock Data Testing (No Database)

If you don't have database access, set in .env:
```bash
USE_MOCK_DATA=true
```

The application will use sample data for testing.

## Step 10: Pre-Deployment Checklist

### ✅ Functionality Checks
- [ ] AI Assistant responds to queries
- [ ] PPA rates are configurable
- [ ] Performance metrics calculate correctly
- [ ] Export functions work
- [ ] Dashboard widgets display data
- [ ] Settings page saves configurations

### ✅ Performance Checks
- [ ] Page load times < 3 seconds
- [ ] API responses < 3 seconds
- [ ] No memory leaks after extended use
- [ ] Handles concurrent users (test with multiple browser tabs)

### ✅ Security Checks
- [ ] Query sanitization working
- [ ] No sensitive data in logs
- [ ] Environment variables not exposed
- [ ] No hardcoded credentials

### ✅ Error Handling
- [ ] Graceful handling of database errors
- [ ] User-friendly error messages
- [ ] No stack traces shown to users
- [ ] Fallback for missing data

## Troubleshooting

### Issue: ModuleNotFoundError for scipy
```bash
pip install scipy numpy pandas
```

### Issue: Port already in use
```bash
# Find and kill process using port 8001
lsof -i :8001
kill -9 <PID>

# Find and kill process using port 8502
lsof -i :8502
kill -9 <PID>
```

### Issue: Database connection errors
1. Check .env file has correct credentials
2. Verify database is accessible
3. Or use USE_MOCK_DATA=true for testing

### Issue: Import errors in Streamlit
```bash
cd apps/streamlit-frontend
pip install -r requirements.txt
```

### Issue: Backend API not responding
1. Check backend logs: `tail -f apps/backend/backend.log`
2. Verify backend is running on port 8001
3. Check API_BASE_URL in .env

## Monitoring During Testing

### Watch Backend Logs
```bash
# In backend directory
tail -f backend.log
```

### Watch Streamlit Logs
Streamlit logs appear directly in the terminal where it's running

### Monitor System Resources
```bash
# CPU and Memory usage
htop

# Network connections
netstat -an | grep -E '8001|8502'
```

## Final Verification Before Deployment

1. **Clean Test**: Stop all services, clear cache, restart and test
```bash
# Stop all services
pkill -f streamlit
pkill -f uvicorn

# Clear Python cache
find . -type d -name __pycache__ -exec rm -r {} + 2>/dev/null

# Restart and test
```

2. **Documentation Check**
- README.md is up to date
- API documentation is current
- Configuration examples are provided

3. **Dependencies Check**
```bash
# Generate updated requirements
pip freeze > requirements_full.txt

# Verify all imports work
python -c "from apps.backend.src.services.ai_service_v2 import AIServiceV2"
python -c "from scipy import stats"
```

4. **Environment Variables**
- Document all required environment variables
- Ensure .env.example is updated
- Remove any sensitive data from code

## Ready for Streamlit Cloud Deployment

Once all tests pass locally:
1. Commit all changes to Git
2. Push to GitHub
3. Deploy to Streamlit Cloud
4. Set environment variables in Streamlit Cloud settings
5. Test deployed application

## Support

If you encounter issues:
1. Check logs (backend.log, Streamlit console)
2. Verify environment variables
3. Ensure all dependencies are installed
4. Test with mock data first
5. Check network connectivity

Good luck with your deployment! 🚀