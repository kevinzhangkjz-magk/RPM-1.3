#!/bin/bash

# Set Railway environment variables
echo "Setting Railway environment variables..."

railway variables \
  --set "REDSHIFT_HOST=data-analytics.crmjfkw9o04v.us-east-1.redshift.amazonaws.com" \
  --set "REDSHIFT_PORT=5439" \
  --set "REDSHIFT_DATABASE=desri_analytics" \
  --set "REDSHIFT_USER=chail" \
  --set "REDSHIFT_PASSWORD=U2bqPmM88D2d" \
  --set "BASIC_AUTH_USERNAME=testuser" \
  --set "BASIC_AUTH_PASSWORD=testpass" \
  --set "DEBUG=false" \
  --set "ENVIRONMENT=production"

echo "Environment variables set successfully!"
echo ""
echo "To view your variables, run:"
echo "railway variables"