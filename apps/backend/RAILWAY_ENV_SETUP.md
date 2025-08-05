# Setting Environment Variables in Railway

The authentication is failing because environment variables are not set. Follow these steps:

## Option 1: Railway Dashboard (Recommended)

1. Go to https://railway.app/dashboard
2. Click on your "rpm 1.3" project
3. Click on the "rpm 1.3" service
4. Click on the "Variables" tab
5. Click "Add Variable" and add these:

```
BASIC_AUTH_USERNAME=testuser
BASIC_AUTH_PASSWORD=testpass
DEBUG=false
ENVIRONMENT=production
```

6. After adding all variables, Railway will automatically redeploy

## Option 2: Railway CLI

Run these commands in the backend directory:

```bash
cd apps/backend
railway link

# Set variables one by one
railway variables set BASIC_AUTH_USERNAME=testuser
railway variables set BASIC_AUTH_PASSWORD=testpass
railway variables set DEBUG=false
railway variables set ENVIRONMENT=production

# Trigger redeploy
railway up
```

## Verify Setup

After redeployment completes:

1. Check logs for "BASIC_AUTH_USERNAME: SET" in the debug output
2. Test the API:
   ```bash
   curl https://rpm-13-production-ca68.up.railway.app/api/sites/ -u testuser:testpass
   ```

3. The frontend should now work at:
   https://frabjous-cuchufli-daaafb.netlify.app/portfolio/

## Why This Happens

Railway doesn't automatically read .env files. Environment variables must be set through:
- Railway Dashboard (persists across deployments)
- Railway CLI (persists across deployments)
- railway.toml (not recommended for secrets)

The variables are stored in Railway's infrastructure and injected at runtime.