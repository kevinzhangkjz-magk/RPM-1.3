from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.routes import api_router, sites_router
from src.core.config import settings

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
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(api_router)
app.include_router(sites_router)


# AWS Lambda handler for serverless deployment
def lambda_handler(event, context):
    """AWS Lambda handler for serverless deployment"""
    from mangum import Mangum

    handler = Mangum(app)
    return handler(event, context)
