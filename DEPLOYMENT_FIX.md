# 🚨 IMMEDIATE FIX FOR STREAMLIT CLOUD

## The Problem
- Backend is running locally at `localhost:8000` ✅
- Backend connects to Redshift successfully ✅
- Backend queries correct table (`analytics.site_metadata`) ✅
- **BUT: Streamlit Cloud cannot access `localhost:8000`** ❌

## Solution 1: IMMEDIATE FIX (5 minutes) - Use ngrok

### Step 1: Install ngrok
```bash
# Mac
brew install ngrok

# Or download from https://ngrok.com/download
```

### Step 2: Expose your local backend
```bash
# In one terminal, make sure backend is running:
cd apps/backend
python main.py

# In another terminal, expose it with ngrok:
ngrok http 8000
```

### Step 3: Update Streamlit Cloud
1. Copy the ngrok URL (e.g., `https://abc123.ngrok-free.app`)
2. Go to https://share.streamlit.io/
3. Click on your app (rpm-1-3)
4. Click the three dots menu → Settings
5. Go to "Secrets" section
6. Add this content:
```toml
API_BASE_URL = "https://YOUR-NGROK-URL.ngrok-free.app"
API_TIMEOUT = "30"
BASIC_AUTH_USERNAME = "testuser"
BASIC_AUTH_PASSWORD = "testpass"
```
7. Click "Save"
8. The app will automatically restart

## Solution 2: PERMANENT FIX - Deploy to Render.com (Free)

### Step 1: Prepare backend for deployment
The files are already created:
- `Procfile` - Tells Render how to run the app
- `render.yaml` - Contains all environment variables

### Step 2: Deploy to Render
1. Go to https://render.com and sign up (free)
2. Click "New +" → "Web Service"
3. Connect your GitHub account
4. Select your repository: `RPM-1.3`
5. Configure:
   - **Name**: rpm-backend
   - **Root Directory**: apps/backend
   - **Environment**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
6. Click "Create Web Service"
7. Wait for deployment (5-10 minutes)
8. Copy your URL (e.g., `https://rpm-backend.onrender.com`)

### Step 3: Update Streamlit Cloud
Same as above, but use the Render URL instead of ngrok.

## Solution 3: Quick Deploy with Railway (Alternative)

1. Go to https://railway.app
2. Click "Start a New Project"
3. Select "Deploy from GitHub repo"
4. Choose your repository
5. Set root directory to `apps/backend`
6. Railway will auto-detect and deploy
7. Generate a domain and use that URL

## Testing the Connection

Once you've updated the API_BASE_URL in Streamlit Cloud:
1. Go to your app: https://rpm-1-3.streamlit.app/
2. Navigate to Portfolio
3. You should now see all 35 solar sites from Redshift!

## Current Status
- ✅ Backend code is correct
- ✅ Redshift connection works
- ✅ Database queries are correct
- ✅ Local testing shows 35 sites
- ❌ Just need to expose backend to internet

## Quick Test Command
To verify your backend is working:
```bash
curl -u testuser:testpass YOUR_BACKEND_URL/api/sites/
```

Should return JSON with all sites.