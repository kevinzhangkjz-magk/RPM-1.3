#!/usr/bin/env python3
"""Debug script to test Railway environment variables"""

import os
import sys

print("=== Railway Environment Debug ===")
print(f"Python version: {sys.version}")
print(f"Current directory: {os.getcwd()}")
print(f"PORT: {os.environ.get('PORT', 'NOT SET')}")
print("\n--- Authentication Variables ---")
print(f"BASIC_AUTH_USERNAME: {'SET' if os.environ.get('BASIC_AUTH_USERNAME') else 'NOT SET'}")
print(f"BASIC_AUTH_PASSWORD: {'SET' if os.environ.get('BASIC_AUTH_PASSWORD') else 'NOT SET'}")
print(f"DEBUG: {os.environ.get('DEBUG', 'NOT SET')}")
print(f"ENVIRONMENT: {os.environ.get('ENVIRONMENT', 'NOT SET')}")
print("\n--- All Environment Variables ---")
for key, value in sorted(os.environ.items()):
    if any(secret in key.lower() for secret in ['password', 'key', 'secret', 'token']):
        print(f"{key}: ***HIDDEN***")
    else:
        print(f"{key}: {value}")