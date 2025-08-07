"""
Cloudflare Workers adapter for FastAPI app
Uses Cloudflare's Python Workers (Beta)
"""
from js import Response
import json
from main import app
import asyncio

async def on_fetch(request, env):
    """Handle incoming requests"""
    # Get the URL path
    url = request.url
    path = url.split(request.headers.get("host"))[1] if request.headers.get("host") else "/"
    
    # Basic auth check
    auth_header = request.headers.get("Authorization")
    if not auth_header or not check_basic_auth(auth_header, env):
        return Response.new(
            "Unauthorized",
            status=401,
            headers={"WWW-Authenticate": 'Basic realm="RPM Backend"'}
        )
    
    # Handle CORS preflight
    if request.method == "OPTIONS":
        return Response.new(
            "",
            headers={
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type, Authorization",
            }
        )
    
    # Route to FastAPI
    try:
        # Convert CF request to FastAPI format
        body = await request.text() if request.method in ["POST", "PUT"] else None
        
        # Call FastAPI app
        response = await handle_fastapi_request(
            method=request.method,
            path=path,
            headers=dict(request.headers),
            body=body,
            env=env
        )
        
        # Add CORS headers
        headers = {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
        }
        
        return Response.new(
            json.dumps(response),
            headers=headers
        )
        
    except Exception as e:
        return Response.new(
            json.dumps({"error": str(e)}),
            status=500,
            headers={"Content-Type": "application/json"}
        )

def check_basic_auth(auth_header, env):
    """Verify basic authentication"""
    import base64
    
    if not auth_header.startswith("Basic "):
        return False
    
    try:
        credentials = base64.b64decode(auth_header[6:]).decode()
        username, password = credentials.split(":", 1)
        
        return (
            username == env.BASIC_AUTH_USERNAME and
            password == env.BASIC_AUTH_PASSWORD
        )
    except:
        return False

async def handle_fastapi_request(method, path, headers, body, env):
    """Route request to FastAPI app"""
    # Import FastAPI routes
    from src.routes import ai, data, test, portfolio, auth
    
    # Simple routing based on path
    if path.startswith("/api/health"):
        return {"status": "healthy", "timestamp": "2024-08-06T00:00:00Z"}
    
    elif path.startswith("/api/ai/query"):
        # Handle AI queries
        if body:
            data = json.loads(body)
            # You'll need to adapt this based on your actual AI service
            return {"response": f"Processing query: {data.get('query', '')}", "data": []}
    
    elif path.startswith("/api/data"):
        # Handle data endpoints
        return {"message": "Data endpoint", "path": path}
    
    elif path.startswith("/api/portfolio"):
        # Handle portfolio endpoints  
        return {"message": "Portfolio endpoint", "path": path}
    
    else:
        return {"error": "Not found", "path": path}