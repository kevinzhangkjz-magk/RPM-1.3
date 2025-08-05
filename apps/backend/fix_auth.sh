#!/bin/bash

echo "Fixing authentication by setting environment variables..."

# Set the required environment variables
railway variables --set "BASIC_AUTH_USERNAME=testuser" \
                  --set "BASIC_AUTH_PASSWORD=testpass" \
                  --set "DEBUG=false" \
                  --set "ENVIRONMENT=production"

echo ""
echo "Variables set. Now triggering a redeploy..."
echo ""
echo "Please go to Railway dashboard and click 'Redeploy' on your latest deployment"
echo "Or run: railway up"
echo ""
echo "After redeployment, test with:"
echo "curl https://rpm-13-production-ca68.up.railway.app/api/sites/ -u testuser:testpass"