# Backend Deployment Instructions

## Problem
Streamlit Cloud cannot access `localhost:8000`. The backend must be deployed to a publicly accessible URL.

## Quick Solution (Temporary - Using ngrok)
1. Install ngrok: `brew install ngrok` (Mac) or download from https://ngrok.com
2. Run your backend locally: `cd apps/backend && python main.py`
3. Expose it with ngrok: `ngrok http 8000 --auth testuser:testpass`
4. Copy the ngrok URL (e.g., https://abc123.ngrok.io)
5. Update Streamlit Cloud environment variables:
   - Go to https://share.streamlit.io/
   - Click on your app settings
   - Add secret: `API_BASE_URL = "https://abc123.ngrok.io"`

## Permanent Solution - Deploy to Render.com (Free)
1. Create account at https://render.com
2. Create a new Web Service
3. Connect your GitHub repository
4. Configure:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
   - Add environment variables from .env file
5. Deploy and copy the URL

## Permanent Solution - Deploy to Railway.app
1. Create account at https://railway.app
2. Create new project from GitHub
3. Add all environment variables
4. Deploy (automatic)
5. Generate domain and copy URL

## Permanent Solution - Deploy to Heroku
1. Create `Procfile` in backend directory:
   ```
   web: uvicorn main:app --host 0.0.0.0 --port $PORT
   ```
2. Create `runtime.txt`:
   ```
   python-3.11.0
   ```
3. Deploy:
   ```bash
   heroku create rpm-backend
   heroku config:set REDSHIFT_HOST=data-analytics.crmjfkw9o04v.us-east-1.redshift.amazonaws.com
   heroku config:set REDSHIFT_PORT=5439
   heroku config:set REDSHIFT_DATABASE=desri_analytics
   heroku config:set REDSHIFT_USER=chail
   heroku config:set REDSHIFT_PASSWORD=U2bqPmM88D2d
   heroku config:set BASIC_AUTH_USERNAME=testuser
   heroku config:set BASIC_AUTH_PASSWORD=testpass
   git push heroku main
   ```

## Update Streamlit Cloud
Once deployed, update the API_BASE_URL in Streamlit Cloud secrets:
1. Go to https://share.streamlit.io/
2. Click on your app's settings (⚙️)
3. Go to Secrets
4. Add:
   ```
   API_BASE_URL = "YOUR_DEPLOYED_BACKEND_URL"
   API_TIMEOUT = "30"
   ```