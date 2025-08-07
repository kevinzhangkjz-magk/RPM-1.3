#!/bin/bash

echo "🚀 Deploying RPM Backend to Cloudflare..."

# Install cloudflared if not installed
if ! command -v cloudflared &> /dev/null; then
    echo "Installing cloudflared..."
    brew install cloudflared
fi

# Kill any existing tunnels
pkill cloudflared 2>/dev/null

# Start the FastAPI backend if not running
if ! lsof -i :8000 > /dev/null; then
    echo "Starting backend server..."
    python main.py &
    sleep 3
fi

# Create a Cloudflare Tunnel
echo "Creating Cloudflare Tunnel..."
cloudflared tunnel --url http://localhost:8000 &

# Wait for tunnel to be established
sleep 5

# Get the tunnel URL
echo ""
echo "✅ Your backend is now accessible via Cloudflare!"
echo "The tunnel URL will be displayed above (look for *.trycloudflare.com)"
echo ""
echo "📝 Next steps:"
echo "1. Copy the Cloudflare URL (https://xxxxx.trycloudflare.com)"
echo "2. Go to https://share.streamlit.io/"
echo "3. Click on your app's settings (⚙️)"
echo "4. Go to Secrets section"
echo "5. Add: API_BASE_URL = \"YOUR_CLOUDFLARE_URL\""
echo ""
echo "Press Ctrl+C to stop the tunnel when done."

# Keep the script running
wait