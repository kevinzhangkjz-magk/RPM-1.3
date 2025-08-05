#!/bin/bash

echo "=== Railway Deployment with Environment Variables ==="

# First, ensure we're linked to the right service
echo "Linking to Railway service..."
railway link

# Set environment variables
echo ""
echo "Setting environment variables..."
railway variables set BASIC_AUTH_USERNAME=testuser
railway variables set BASIC_AUTH_PASSWORD=testpass
railway variables set DEBUG=false
railway variables set ENVIRONMENT=production

# Optional: Set Redshift variables if you have them
# railway variables set REDSHIFT_HOST=your-host
# railway variables set REDSHIFT_DATABASE=your-db
# railway variables set REDSHIFT_USER=your-user
# railway variables set REDSHIFT_PASSWORD=your-password

echo ""
echo "Environment variables set. Deploying to Railway..."
railway up

echo ""
echo "Deployment initiated. Check the Railway dashboard for logs."
echo "Dashboard URL: https://railway.app/dashboard"