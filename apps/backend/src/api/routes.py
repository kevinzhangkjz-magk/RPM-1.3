from fastapi import APIRouter, HTTPException, Query, Path, status, Depends
from datetime import datetime, timedelta
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


@sites_router.get("/{site_id}/power-curve")
async def get_site_power_curve(
    site_id: str = Path(..., description="Site identifier", min_length=1),
    year: Optional[int] = Query(None, description="Year to query"),
    month: Optional[int] = Query(None, description="Month to query", ge=1, le=12),
    current_user: str = Depends(get_current_user),
):
    """
    Get hourly power curve data for a site (POA irradiance vs Power)
    
    Returns hourly aggregated data points for power curve visualization.
    """
    try:
        # Use current year/month if not provided
        if not year or not month:
            now = datetime.now()
            year = year or now.year
            month = month or now.month
        
        # Initialize repository
        repo = SitePerformanceRepository()
        
        # Get power curve data
        power_curve_data, fallback_used = repo.get_power_curve_data(site_id, year, month)
        
        # Calculate RMSE and R-squared if we have data
        rmse = 0.0
        r_squared = 0.0
        
        if power_curve_data:
            try:
                import numpy as np
                
                # Extract actual and expected values
                actual = [p.get('actual_power_mw', 0) for p in power_curve_data if p.get('actual_power_mw')]
                expected = [p.get('expected_power_mw', 0) for p in power_curve_data if p.get('expected_power_mw')]
                
                if actual and expected and len(actual) == len(expected):
                    # Calculate RMSE manually
                    actual_arr = np.array(actual)
                    expected_arr = np.array(expected)
                    mse = np.mean((actual_arr - expected_arr) ** 2)
                    rmse = float(np.sqrt(mse))
                    
                    # Calculate R-squared manually
                    ss_res = np.sum((actual_arr - expected_arr) ** 2)
                    ss_tot = np.sum((actual_arr - np.mean(actual_arr)) ** 2)
                    r_squared = float(1 - (ss_res / ss_tot)) if ss_tot > 0 else 0.0
            except ImportError:
                # If numpy not available, skip calculations
                logger.warning("NumPy not available, skipping RMSE/R² calculations")
            except Exception as e:
                logger.warning(f"Error calculating metrics: {e}")
        
        return {
            "site_id": site_id,
            "data_points": power_curve_data,
            "rmse": rmse,
            "r_squared": r_squared,
            "data_fallback": fallback_used,
            "data_month": f"{year}-{month:02d}"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "InternalServerError",
                "message": "Error retrieving power curve data",
                "details": {"error": str(e)}
            }
        )

@sites_router.get("/{site_id}/", response_model=SiteDetails)
async def get_site_detail(
    site_id: str = Path(..., description="Site identifier", min_length=1),
    current_user: str = Depends(get_current_user),
):
    """
    Retrieve detailed information for a specific site.
    
    Returns detailed site information including capacity, location, and status.
    """
    try:
        # Initialize repository
        repo = SitesRepository()
        
        # Get site details from database
        site_data = repo.get_site_by_id(site_id)
        
        if not site_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": "SiteNotFound",
                    "message": f"Site with ID '{site_id}' not found",
                    "details": {"site_id": site_id},
                },
            )
        
        # Convert to Pydantic model
        site = SiteDetails(**site_data)
        
        return site
        
    except HTTPException:
        # Re-raise HTTPException as-is
        raise
    except Exception as e:
        # Handle unexpected errors
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "InternalServerError",
                "message": "An unexpected error occurred while retrieving site details",
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
    year: Optional[int] = Query(
        None, description="Year to query (defaults to current year)"
    ),
    month: Optional[int] = Query(
        None, description="Month to query (defaults to current month)", ge=1, le=12
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

        # Get performance data with optional year/month
        performance_data, fallback_used = repo.get_site_performance_data(
            site_id, query_params.start_date, query_params.end_date,
            year, month
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

        # Determine which month's data we're showing
        if year and month:
            data_month = f"{year}-{month:02d}"
        else:
            now = datetime.now()
            if fallback_used:
                # Previous month
                prev_month = now.replace(day=1) - timedelta(days=1)
                data_month = f"{prev_month.year}-{prev_month.month:02d}"
            else:
                data_month = f"{now.year}-{now.month:02d}"

        # Build response
        response = SitePerformanceResponse(
            site_id=site_id,
            site_name=data_points[0].site_name if data_points else None,
            data_points=data_points,
            summary=summary,
            data_fallback=fallback_used,
            data_month=data_month,
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


@sites_router.get("/{site_id}/skids-performance")
async def get_skids_performance(
    site_id: str = Path(..., description="Site identifier", min_length=1),
    year: Optional[int] = Query(None, description="Year to query"),
    month: Optional[int] = Query(None, description="Month to query", ge=1, le=12),
    current_user: str = Depends(get_current_user),
):
    """
    Get daily average performance for all skids at a site.
    
    Returns daily average power for each skid for comparative analysis.
    """
    try:
        # Use current year/month if not provided
        if not year or not month:
            now = datetime.now()
            year = year or now.year
            month = month or now.month
        
        # Initialize repository
        repo = SkidsRepository()
        
        # Get skids daily average data
        skids_data, fallback_used = repo.get_skids_daily_average(site_id, year, month)
        
        # Identify top performers and underperformers
        top_performers = []
        underperformers = []
        
        if skids_data:
            # Sort by deviation percentage
            sorted_skids = sorted(skids_data, key=lambda x: x.get('deviation_percentage', 0), reverse=True)
            
            # Top 3 performers (highest positive deviation)
            top_performers = [
                {
                    "skid_id": s['skid_id'],
                    "deviation": f"+{s['deviation_percentage']:.1f}%"
                }
                for s in sorted_skids[:3] if s.get('deviation_percentage', 0) > 0
            ]
            
            # Bottom 3 performers (lowest or negative deviation)
            underperformers = [
                {
                    "skid_id": s['skid_id'],
                    "deviation": f"{s['deviation_percentage']:.1f}%"
                }
                for s in sorted_skids[-3:] if s.get('deviation_percentage', 0) < 0
            ]
        
        # Calculate average deviation
        avg_deviation = 0.0
        if skids_data:
            deviations = [s.get('deviation_percentage', 0) for s in skids_data]
            avg_deviation = sum(deviations) / len(deviations) if deviations else 0.0
        
        return {
            "site_id": site_id,
            "skids": skids_data,
            "total_skids": len(skids_data),
            "average_deviation": f"{avg_deviation:.1f}%",
            "top_performers": top_performers,
            "underperformers": underperformers,
            "data_fallback": fallback_used,
            "data_month": f"{year}-{month:02d}"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "InternalServerError",
                "message": "Error retrieving skids performance data",
                "details": {"error": str(e)}
            }
        )

@sites_router.get("/{site_id}/skids/", response_model=SkidsListResponse)
async def get_site_skids(
    site_id: str = Path(..., description="Site identifier", min_length=1),
    start_date: Optional[datetime] = Query(
        None, description="Start date for data retrieval (ISO format)"
    ),
    end_date: Optional[datetime] = Query(
        None, description="End date for data retrieval (ISO format)"
    ),
    current_user: str = Depends(get_current_user),
):
    """
    Retrieve aggregated performance data for all skids on a site.
    
    Returns performance metrics for each skid filtered for 100% inverter availability
    within the specified date range.
    """
    try:
        # If dates not provided, use default range (last 30 days)
        if not start_date or not end_date:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=30)
        
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
