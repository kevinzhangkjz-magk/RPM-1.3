#!/bin/bash
# Shell script to run the Streamlit application on Mac/Linux
# Make executable with: chmod +x run_local.sh
# Then run with: ./run_local.sh

echo "========================================"
echo "RPM Streamlit Application Launcher"
echo "========================================"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed"
    echo "Please install Python 3.8 or higher"
    exit 1
fi

# Run the Python launcher script
python3 run_local.py

# Check exit status
if [ $? -ne 0 ]; then
    echo ""
    echo "ERROR: Application failed to start"
    exit 1
fi