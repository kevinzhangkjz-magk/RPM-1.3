# Railway Deployment Guide for RPM Backend

This guide provides step-by-step instructions for deploying the RPM backend to Railway.

## Prerequisites

1. Railway account (sign up at https://railway.app)
2. Railway CLI installed (`brew install railway` or `npm install -g @railway/cli`)
3. Git repository with your code

## Deployment Steps

### 1. Initial Setup

```bash
# Navigate to backend directory
cd apps/backend

# Login to Railway
railway login
```

### 2. Create New Project

```bash
# Initialize new Railway project
railway init

# Choose "Create new project"
# Name it something like "rpm-backend"
```

### 3. Configure Environment Variables

You have two options:

#### Option A: Using Railway CLI
```bash
# Set all required environment variables
railway variables set APP_NAME="RPM Solar Performance API"
railway variables set APP_VERSION="1.0.0"
railway variables set ENVIRONMENT="production"
railway variables set DEBUG="false"

# Database credentials (replace with your actual values)
railway variables set REDSHIFT_HOST="data-analytics.crmjfkw9o04v.us-east-1.redshift.amazonaws.com"
railway variables set REDSHIFT_PORT="5439"
railway variables set REDSHIFT_DATABASE="desri_analytics"
railway variables set REDSHIFT_USER="your_username"
railway variables set REDSHIFT_PASSWORD="your_password"
railway variables set REDSHIFT_SSL="true"

# Authentication (use secure values)
railway variables set BASIC_AUTH_USERNAME="your_api_username"
railway variables set BASIC_AUTH_PASSWORD="your_secure_password"

# AI Service (if using)
railway variables set OPENAI_API_KEY="your_openai_api_key"
```

#### Option B: Using Railway Dashboard
1. Go to your project in Railway dashboard
2. Click on "Variables" tab
3. Add each variable from `.env.example`

### 4. Deploy

```bash
# Deploy to Railway
railway up

# This will:
# - Upload your code
# - Install dependencies from requirements.txt
# - Start the application using Procfile
```

### 5. Get Your API URL

```bash
# Get deployment status
railway status

# Open in browser
railway open
```

Or in Railway dashboard:
1. Go to your project
2. Click on the service
3. Go to Settings → Networking
4. Click "Generate Domain"
5. Your API will be available at: `https://rpm-backend-production.up.railway.app`

### 6. Update Frontend

1. Go to Netlify Dashboard
2. Site settings → Environment variables
3. Add: `NEXT_PUBLIC_API_URL = https://your-railway-domain.up.railway.app`
4. Trigger redeploy

## Testing the Deployment

### Health Check
```bash
curl https://your-railway-domain.up.railway.app/health
# Should return: {"status":"healthy"}
```

### API Documentation
Visit: `https://your-railway-domain.up.railway.app/docs`

## Monitoring

### View Logs
```bash
railway logs
```

### Check Metrics
In Railway dashboard, click on your service to see:
- CPU usage
- Memory usage
- Network traffic
- Response times

## Troubleshooting

### Common Issues

1. **Port Binding Error**
   - Make sure you're using `$PORT` environment variable
   - Railway assigns the port dynamically

2. **Module Import Errors**
   - Ensure all dependencies are in `requirements.txt`
   - Check Python version in `runtime.txt`

3. **Database Connection Failed**
   - Verify all database environment variables are set
   - Check if database allows connections from Railway IPs

4. **CORS Issues**
   - The backend already includes your Netlify domain in CORS settings
   - If using custom domain, update `main.py` CORS configuration

### Debug Commands

```bash
# View all environment variables
railway variables

# SSH into the container (if needed)
railway run bash

# Run commands in Railway environment
railway run python -c "import sys; print(sys.version)"
```

## CI/CD Setup

### Connect GitHub

1. In Railway dashboard → Settings
2. Connect GitHub repository
3. Select branch (main/master)
4. Enable automatic deploys

Now every push to your repository will automatically deploy!

## Production Best Practices

1. **Security**
   - Use strong passwords for BASIC_AUTH
   - Keep sensitive data in environment variables
   - Regularly update dependencies

2. **Performance**
   - Enable caching where appropriate
   - Use connection pooling for database
   - Monitor response times

3. **Reliability**
   - Set up health checks
   - Configure restart policies
   - Monitor error rates

## Costs

Railway offers:
- $5 monthly credit (free tier)
- Pay-as-you-go after that
- Typical FastAPI app: ~$5-10/month

To optimize costs:
- Enable sleep mode when not in use
- Use efficient code
- Monitor resource usage

## Next Steps

1. Set up custom domain (optional)
2. Configure monitoring alerts
3. Set up database backups
4. Implement rate limiting
5. Add API key authentication for production