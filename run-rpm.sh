#!/bin/bash

# RPM Application Launcher for Mac
# Save this as run-rpm.sh in your project root directory

# Function for colorful output
print_step() {
  BLUE='\033[0;34m'
  GREEN='\033[0;32m'
  NC='\033[0m' # No Color
  echo -e "\n${GREEN}===${NC} ${BLUE}$1${NC} ${GREEN}===${NC}"
}

# Check if script is being run from project root
if [ ! -d "apps/frontend" ] || [ ! -d "apps/backend" ]; then
  echo "Error: Please run this script from the RPM-1.3 project root directory"
  exit 1
fi

# Kill any processes that might be using our ports
print_step "Checking for processes using ports 3000 and 8000"
kill $(lsof -ti:3000) 2>/dev/null || true
kill $(lsof -ti:8000) 2>/dev/null || true

# Backend setup and start
print_step "Setting up and starting the backend server"
cd apps/backend

# Check if virtual environment exists, create if it doesn't
if [ ! -d "venv" ]; then
  print_step "Creating Python virtual environment"
  python3 -m venv venv
fi

# Activate virtual environment and install dependencies
source venv/bin/activate
pip install -r requirements.txt

# Start backend server in the background
print_step "Starting backend server at http://localhost:8000"
npm run dev &
BACKEND_PID=$!
echo "Backend server started with PID: $BACKEND_PID"

# Wait for backend to initialize
sleep 3

# Frontend setup and start
print_step "Setting up and starting the frontend server"
cd ../frontend

# Install dependencies if node_modules doesn't exist
if [ ! -d "node_modules" ]; then
  print_step "Installing frontend dependencies"
  npm install
fi

# Start frontend server in the background
print_step "Starting frontend server at http://localhost:3000"
npm run dev &
FRONTEND_PID=$!
echo "Frontend server started with PID: $FRONTEND_PID"

# Open the application in browser
print_step "Opening the application in your default browser"
sleep 3
open http://localhost:3000

print_step "RPM application is now running"
echo "- Frontend: http://localhost:3000"
echo "- Backend: http://localhost:8000"
echo ""
echo "Press Ctrl+C to stop both servers"

# Function to clean up processes when script exits
cleanup() {
  print_step "Stopping servers"
  kill $BACKEND_PID 2>/dev/null || true
  kill $FRONTEND_PID 2>/dev/null || true
  echo "Servers stopped. Thanks for using RPM!"
  exit 0
}

# Register the cleanup function to run on script exit
trap cleanup INT TERM EXIT

# Keep script running
wait