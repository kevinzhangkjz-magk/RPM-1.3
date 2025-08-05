#!/bin/bash

echo "Starting RPM Streamlit Frontend..."
echo "================================"
echo ""
echo "Fetching real data from Redshift database via API..."
echo ""
echo "Open in browser: http://localhost:8501"
echo ""

streamlit run app.py --server.port 8501