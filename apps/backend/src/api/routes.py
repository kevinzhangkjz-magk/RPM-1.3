from fastapi import APIRouter, HTTPException, Query, Path, status, Depends
from datetime import datetime
from typing import Optional

from src.models.site_performance import (
    SitePerformanceResponse,
    SitePerformanceQueryParams,
    ErrorResponse,
    PerformanceDataPoint,
    SiteDataSummary,
    SiteDetails,
    SitesListResponse,
    SkidsListResponse,
    SkidPerformance,
    InvertersListResponse,
    InverterPerformance,
)
from src.dal.site_performance import SitePerformanceRepository
from src.dal.sites import SitesRepository
from src.dal.skids import SkidsRepository
from src.dal.inverters import InvertersRepository
from src.core.security import get_current_user

# Main API router
api_router = APIRouter()


# Health check routes
@api_router.get("/")
async def root():
    """Root endpoint for health check"""
    return {"message": "RPM Solar Performance API is running"}


@api_router.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy"}


# Future API routes will be added here
# Sites API routes
sites_router = APIRouter(prefix="/api/sites", tags=["sites"])


@sites_router.get("/", response_model=SitesListResponse)
async def list_sites(current_user: str = Depends(get_current_user)):
    """
    Retrieve list of all solar sites.

    Returns a list of all active solar sites available for performance monitoring.
    """
    try:
        # Initialize repository
        repo = SitesRepository()

        # Get all sites from database
        sites_data = repo.get_all_sites()

        # Convert to Pydantic models
        sites = [SiteDetails(**site) for site in sites_data]

        # Build response
        response = SitesListResponse(sites=sites, total_count=len(sites))

        return response

    except Exception as e:
        # Handle unexpected errors
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "InternalServerError",
                "message": "An unexpected error occurred while retrieving sites",
                "details": {"error_type": type(e).__name__},
            },
        )


@sites_router.get("/{site_id}/performance", response_model=SitePerformanceResponse)
async def get_site_performance(
    site_id: str = Path(..., description="Site identifier", min_length=1),
    start_date: datetime = Query(
        ..., description="Start date for data retrieval (ISO format)"
    ),
    end_date: datetime = Query(
        ..., description="End date for data retrieval (ISO format)"
    ),
    current_user: str = Depends(get_current_user),
):
    """
    Retrieve time-series performance data for a specific site.

    Returns performance data points filtered for 100% inverter availability
    within the specified date range.
    """
    try:
        # Validate query parameters using Pydantic model
        query_params = SitePerformanceQueryParams(
            start_date=start_date, end_date=end_date
        )

        # Initialize repository
        repo = SitePerformanceRepository()

        # Validate site exists
        if not repo.validate_site_exists(site_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": "SiteNotFound",
                    "message": f"Site with ID '{site_id}' not found",
                    "details": {"site_id": site_id},
                },
            )

        # Get performance data
        performance_data = repo.get_site_performance_data(
            site_id, query_params.start_date, query_params.end_date
        )

        # Check if data exists
        if not performance_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": "NoDataFound",
                    "message": f"No performance data found for site '{site_id}' in the specified date range",
                    "details": {
                        "site_id": site_id,
                        "start_date": query_params.start_date.isoformat(),
                        "end_date": query_params.end_date.isoformat(),
                    },
                },
            )

        # Convert raw data to Pydantic models
        data_points = [PerformanceDataPoint(**point) for point in performance_data]

        # Get summary statistics
        summary_data = repo.get_site_data_summary(
            site_id, query_params.start_date, query_params.end_date
        )

        summary = None
        if summary_data:
            summary = SiteDataSummary(**summary_data)

        # Build response
        response = SitePerformanceResponse(
            site_id=site_id,
            site_name=data_points[0].site_name if data_points else None,
            data_points=data_points,
            summary=summary,
        )

        return response

    except HTTPException:
        # Re-raise HTTPException as-is
        raise
    except ValueError as e:
        # Handle Pydantic validation errors
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "ValidationError",
                "message": str(e),
                "details": {"parameter_validation": str(e)},
            },
        )
    except Exception as e:
        # Handle unexpected errors
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "InternalServerError",
                "message": "An unexpected error occurred while processing your request",
                "details": {"error_type": type(e).__name__},
            },
        )


@sites_router.get("/{site_id}/skids", response_model=SkidsListResponse)
async def get_site_skids(
    site_id: str = Path(..., description="Site identifier", min_length=1),
    start_date: datetime = Query(
        ..., description="Start date for data retrieval (ISO format)"
    ),
    end_date: datetime = Query(
        ..., description="End date for data retrieval (ISO format)"
    ),
    current_user: str = Depends(get_current_user),
):
    """
    Retrieve aggregated performance data for all skids on a site.
    
    Returns performance metrics for each skid filtered for 100% inverter availability
    within the specified date range.
    """
    try:
        # Validate query parameters using Pydantic model
        query_params = SitePerformanceQueryParams(
            start_date=start_date, end_date=end_date
        )
        
        # Initialize repositories
        repo = SkidsRepository()
        site_repo = SitePerformanceRepository()
        
        # Validate site exists
        if not site_repo.validate_site_exists(site_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": "SiteNotFound",
                    "message": f"Site with ID '{site_id}' not found",
                    "details": {"site_id": site_id},
                },
            )
        
        # Get skids performance data
        skids_data = repo.get_skids_performance_data(
            site_id, query_params.start_date, query_params.end_date
        )
        
        # Check if data exists
        if not skids_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": "NoDataFound",
                    "message": f"No skids data found for site '{site_id}' in the specified date range",
                    "details": {
                        "site_id": site_id,
                        "start_date": query_params.start_date.isoformat(),
                        "end_date": query_params.end_date.isoformat(),
                    },
                },
            )
        
        # Convert raw data to Pydantic models
        skids = [SkidPerformance(**skid) for skid in skids_data]
        
        # Build response
        response = SkidsListResponse(
            site_id=site_id,
            skids=skids,
            total_count=len(skids),
        )
        
        return response
        
    except HTTPException:
        # Re-raise HTTPException as-is
        raise
    except ValueError as e:
        # Handle Pydantic validation errors
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "ValidationError",
                "message": str(e),
                "details": {"parameter_validation": str(e)},
            },
        )
    except Exception as e:
        # Handle unexpected errors
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "InternalServerError",
                "message": "An unexpected error occurred while processing your request",
                "details": {"error_type": type(e).__name__},
            },
        )



# Skids API routes
skids_router = APIRouter(prefix="/api/skids", tags=["skids"])


@skids_router.get("/{skid_id}/inverters", response_model=InvertersListResponse)
async def get_skid_inverters(
    skid_id: str = Path(..., description="Skid identifier", min_length=1),
    start_date: datetime = Query(
        ..., description="Start date for data retrieval (ISO format)"
    ),
    end_date: datetime = Query(
        ..., description="End date for data retrieval (ISO format)"
    ),
    current_user: str = Depends(get_current_user),
):
    """
    Retrieve performance data for all inverters on a skid.
    
    Returns individual performance metrics for each inverter filtered for 100% availability
    within the specified date range.
    """
    try:
        # Validate query parameters using Pydantic model
        query_params = SitePerformanceQueryParams(
            start_date=start_date, end_date=end_date
        )
        
        # Initialize repository
        repo = InvertersRepository()
        
        # Get inverters performance data
        inverters_data = repo.get_inverters_performance_data(
            skid_id, query_params.start_date, query_params.end_date
        )
        
        # Check if data exists
        if not inverters_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": "NoDataFound",
                    "message": f"No inverters data found for skid '{skid_id}' in the specified date range",
                    "details": {
                        "skid_id": skid_id,
                        "start_date": query_params.start_date.isoformat(),
                        "end_date": query_params.end_date.isoformat(),
                    },
                },
            )
        
        # Convert raw data to Pydantic models
        inverters = [InverterPerformance(**inverter) for inverter in inverters_data]
        
        # Build response
        response = InvertersListResponse(
            skid_id=skid_id,
            inverters=inverters,
            total_count=len(inverters),
        )
        
        return response
        
    except HTTPException:
        # Re-raise HTTPException as-is
        raise
    except ValueError as e:
        # Handle Pydantic validation errors
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "ValidationError",
                "message": str(e),
                "details": {"parameter_validation": str(e)},
            },
        )
    except Exception as e:
        # Handle unexpected errors
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "InternalServerError",
                "message": "An unexpected error occurred while processing your request",
                "details": {"error_type": type(e).__name__},
            },
        )
