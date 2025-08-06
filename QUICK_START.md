# Quick Start Testing Guide

## 🚀 5-Minute Quick Test

### Step 1: Setup Environment (1 minute)
```bash
# From project root
cd /Users/kevz/Documents/GitHub/rpm/RPM-1.3

# Install missing dependencies
pip install scipy numpy pandas

# Create minimal .env file
echo 'DEFAULT_PPA_RATE=50.0
SITE_PPA_RATES={"assembly_2": 48.50, "highland": 52.00}
USE_MOCK_DATA=true' > .env
```

### Step 2: Start Backend (30 seconds)
```bash
# Terminal 1
cd apps/backend
python -m uvicorn main:app --port 8001
```

### Step 3: Start Frontend (30 seconds)
```bash
# Terminal 2
cd apps/streamlit-frontend
streamlit run Home.py --server.port 8502
```

### Step 4: Open Browser
Navigate to: http://localhost:8502

### Step 5: Test Key Features (3 minutes)

#### Test 1: AI Assistant
1. Click "AI Assistant" in sidebar
2. Type: "Give me the 3 most underperforming sites"
3. Verify response shows R-squared and RMSE values

#### Test 2: Settings Page
1. Click "Settings" in sidebar
2. Go to "Financial" tab
3. Check PPA rates are displayed ($50/MWh default)

#### Test 3: Dashboard
1. Go to main Dashboard
2. Verify widgets are displayed
3. Check for Performance Leaderboard widget

## 🧪 Automated Test (1 minute)
```bash
# From project root
python test_4_2_features.py
```

Expected output:
```
✅ ALL TESTS PASSED!
Overall: 6/6 tests passed
```

## ✅ Success Criteria

If you see:
- ✅ Backend running on port 8001
- ✅ Streamlit running on port 8502
- ✅ AI Assistant responds to queries
- ✅ Settings page shows PPA rates
- ✅ Dashboard displays widgets
- ✅ Automated tests pass

**Your implementation is working correctly!**

## 🔧 Common Issues & Fixes

### Issue: "ModuleNotFoundError: scipy"
```bash
pip install scipy
```

### Issue: "Port already in use"
```bash
# Kill existing processes
pkill -f "uvicorn.*8001"
pkill -f "streamlit.*8502"
```

### Issue: "Database connection error"
Add to .env:
```bash
USE_MOCK_DATA=true
```

## 📋 Pre-Deployment Checklist

- [ ] All 6 automated tests pass
- [ ] AI Assistant responds correctly
- [ ] PPA rates are configurable
- [ ] No error messages in console
- [ ] Response times < 3 seconds

## 🚀 Ready to Deploy?

If all tests pass, you're ready for Streamlit Cloud deployment!