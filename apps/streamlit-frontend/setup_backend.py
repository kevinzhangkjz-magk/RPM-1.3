#!/usr/bin/env python3
"""
Quick script to expose backend to internet using localtunnel
Run this to make your backend accessible from Streamlit Cloud
"""

import subprocess
import time
import os

print("🚀 Setting up backend exposure to internet...")
print("=" * 50)

# Check if backend is running
try:
    import requests
    response = requests.get("http://localhost:8000/health", timeout=2)
    print("✅ Backend is running on localhost:8000")
except:
    print("❌ Backend is NOT running!")
    print("Please run: cd apps/backend && python main.py")
    exit(1)

# Start localtunnel
print("\n📡 Starting localtunnel...")
print("This will expose your backend to the internet")

try:
    # Run localtunnel
    process = subprocess.Popen(
        ["lt", "--port", "8000", "--print-requests"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    # Wait for URL
    time.sleep(2)
    
    print("\n✨ SUCCESS! Your backend is now accessible at:")
    print("-" * 50)
    
    # The URL will be printed by localtunnel
    print("\n📋 NEXT STEPS:")
    print("1. Copy the URL above (https://xxxxx.loca.lt)")
    print("2. Go to https://share.streamlit.io/")
    print("3. Click on your app → Settings → Secrets")
    print("4. Add this:")
    print("""
API_BASE_URL = "YOUR_LOCALTUNNEL_URL_HERE"
API_TIMEOUT = "30"
    """)
    print("5. Save and your app will work!")
    
    # Keep running
    print("\nPress Ctrl+C to stop the tunnel")
    process.wait()
    
except KeyboardInterrupt:
    print("\n\n👋 Tunnel stopped")
except Exception as e:
    print(f"❌ Error: {e}")
    print("Make sure localtunnel is installed: npm install -g localtunnel")