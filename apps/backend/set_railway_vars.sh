#!/bin/bash

echo "Setting Railway environment variables..."

# Make sure we're in the backend directory
cd "$(dirname "$0")"

# Set each variable
railway variables set BASIC_AUTH_USERNAME=testuser
railway variables set BASIC_AUTH_PASSWORD=testpass
railway variables set DEBUG=false
railway variables set ENVIRONMENT=production

echo ""
echo "Variables set! Railway will automatically redeploy."
echo ""
echo "To check if variables are set:"
echo "railway variables"
echo ""
echo "To manually trigger a redeploy:"
echo "railway up"