import os
import sys
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.api.routes import api_router, sites_router, skids_router
from src.api.ai import router as ai_router
from src.core.config import settings

# Debug print for Railway
print(f"Starting app with AUTH_USERNAME: {bool(os.environ.get('BASIC_AUTH_USERNAME'))}")
print(f"Starting app with AUTH_PASSWORD: {bool(os.environ.get('BASIC_AUTH_PASSWORD'))}")

# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    description="API for Solar Performance Monitoring",
    version=settings.app_version,
    debug=settings.debug,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000", 
        "http://localhost:3001",
        "https://frabjous-cuchufli-daaafb.netlify.app",
        "https://*.netlify.app"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(api_router)
app.include_router(sites_router)
app.include_router(skids_router)
app.include_router(ai_router)

# Add health check
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "auth_configured": bool(settings.basic_auth_username and settings.basic_auth_password),
        "environment": settings.environment
    }


# AWS Lambda handler for serverless deployment
def lambda_handler(event, context):
    """AWS Lambda handler for serverless deployment"""
    from mangum import Mangum

    handler = Mangum(app)
    return handler(event, context)
