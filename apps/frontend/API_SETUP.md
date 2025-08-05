# API Setup Guide

To connect your frontend to a real backend API, follow these steps:

## Option 1: Using ngrok (Quick Testing)

1. Make sure your backend is running locally:
   ```bash
   cd apps/backend
   python main.py
   ```

2. Install and run ngrok:
   ```bash
   # Install ngrok
   brew install ngrok  # macOS
   # or download from https://ngrok.com/download

   # Expose your local backend
   ngrok http 8000
   ```

3. Copy the ngrok URL (e.g., `https://abc123.ngrok.io`)

4. Update your frontend environment:
   - Go to Netlify Dashboard > Site Settings > Environment Variables
   - Add: `NEXT_PUBLIC_API_URL` = `https://abc123.ngrok.io`
   - Redeploy your site

## Option 2: Deploy Backend to Cloud

### AWS Lambda (Recommended)
Your backend is already configured for AWS Lambda deployment.

1. Install AWS CLI and configure credentials
2. Deploy using Serverless Framework or SAM
3. Update `NEXT_PUBLIC_API_URL` with your Lambda function URL

### Other Options
- Heroku
- Google Cloud Run
- Azure Functions
- Railway.app

## Option 3: Local Development with Tunnel

For local development while keeping Netlify deployment:

1. Create `.env.production.local` in frontend:
   ```
   NEXT_PUBLIC_API_URL=https://your-backend-url.com
   ```

2. Run backend with public access using a service like:
   - localtunnel: `npx localtunnel --port 8000`
   - serveo: `ssh -R 80:localhost:8000 serveo.net`

## Important Notes

- The backend CORS is already configured to accept requests from Netlify domains
- Make sure to use HTTPS URLs in production
- Don't commit API URLs with credentials to version control