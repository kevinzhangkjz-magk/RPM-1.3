from datetime import datetime, date
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator, ConfigDict
from enum import Enum


class Site(BaseModel):
    """Site model representing a solar installation site"""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {"site_id": "SITE001", "site_name": "Solar Farm Alpha"}
        }
    )

    site_id: str = Field(..., description="Unique identifier for the site")
    site_name: Optional[str] = Field(
        None, description="Human-readable name of the site"
    )


class SiteDetails(BaseModel):
    """Detailed site model with additional information for site listing"""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "site_id": "SITE001",
                "site_name": "Solar Farm Alpha",
                "location": "Arizona, USA",
                "capacity_kw": 5000.0,
                "installation_date": "2023-01-15",
                "status": "active",
                "connectivity_status": "connected",
            }
        }
    )

    site_id: str = Field(..., description="Unique identifier for the site")
    site_name: Optional[str] = Field(
        None, description="Human-readable name of the site"
    )
    location: Optional[str] = Field(None, description="Geographic location of the site")
    capacity_kw: Optional[float] = Field(
        None, ge=0, description="Total capacity in kilowatts"
    )
    installation_date: Optional[date] = Field(
        None, description="Date when the site was installed"
    )
    status: Optional[str] = Field(None, description="Current status of the site")
    connectivity_status: Optional[str] = Field(
        None, description="Current connectivity status (connected/disconnected)"
    )


class SitesListResponse(BaseModel):
    """Response model for sites list endpoint"""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "sites": [
                    {
                        "site_id": "SITE001",
                        "site_name": "Solar Farm Alpha",
                        "location": "Arizona, USA",
                        "capacity_kw": 5000.0,
                        "installation_date": "2023-01-15",
                        "status": "active",
                    },
                    {
                        "site_id": "SITE002",
                        "site_name": "Solar Farm Beta",
                        "location": "California, USA",
                        "capacity_kw": 3000.0,
                        "installation_date": "2023-03-20",
                        "status": "active",
                    },
                ],
                "total_count": 2,
            }
        }
    )

    sites: List[SiteDetails] = Field(..., description="List of site details")
    total_count: int = Field(..., ge=0, description="Total number of sites")


class PerformanceDataPoint(BaseModel):
    """Performance data point representing a single telemetry reading"""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "timestamp": "2024-01-15T12:00:00Z",
                "site_id": "SITE001",
                "poa_irradiance": 850.5,
                "actual_power": 456.2,
                "expected_power": 475.8,
                "inverter_availability": 1.0,
                "site_name": "Solar Farm Alpha",
            }
        }
    )

    timestamp: datetime = Field(..., description="Timestamp of the reading")
    site_id: str = Field(..., description="Site identifier")
    poa_irradiance: float = Field(
        ..., ge=0, description="Plane of Array Irradiance (W/m²)"
    )
    actual_power: float = Field(..., ge=0, description="Actual power output (kW)")
    expected_power: float = Field(..., ge=0, description="Expected power output (kW)")
    inverter_availability: float = Field(
        ..., ge=0, le=1, description="Inverter availability (0.0 to 1.0)"
    )
    site_name: Optional[str] = Field(None, description="Site name")


class SitePerformanceQueryParams(BaseModel):
    """Query parameters for site performance data endpoint"""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "start_date": "2024-01-01T00:00:00Z",
                "end_date": "2024-01-31T23:59:59Z",
            }
        }
    )

    start_date: datetime = Field(
        ..., description="Start date for data retrieval (ISO format)"
    )
    end_date: datetime = Field(
        ..., description="End date for data retrieval (ISO format)"
    )

    @field_validator("end_date")
    @classmethod
    def validate_date_range(cls, v, info):
        """Validate that end_date is after start_date"""
        if info.data.get("start_date") and v <= info.data.get("start_date"):
            raise ValueError("end_date must be after start_date")
        return v

    @field_validator("start_date", "end_date")
    @classmethod
    def validate_date_not_future(cls, v):
        """Validate that dates are not in the future"""
        from datetime import timezone
        
        # Handle both timezone-aware and timezone-naive datetimes
        now = datetime.now(timezone.utc) if v.tzinfo else datetime.now()
        
        if v > now:
            raise ValueError("Date cannot be in the future")
        return v


class SitePerformanceResponse(BaseModel):
    """Response model for site performance data"""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "site_id": "SITE001",
                "site_name": "Solar Farm Alpha",
                "data_points": [
                    {
                        "timestamp": "2024-01-15T12:00:00Z",
                        "site_id": "SITE001",
                        "poa_irradiance": 850.5,
                        "actual_power": 456.2,
                        "expected_power": 475.8,
                        "inverter_availability": 1.0,
                        "site_name": "Solar Farm Alpha",
                    }
                ],
                "summary": {
                    "data_point_count": 1440,
                    "avg_actual_power": 387.5,
                    "avg_expected_power": 402.1,
                    "avg_poa_irradiance": 612.3,
                    "first_reading": "2024-01-01T00:00:00Z",
                    "last_reading": "2024-01-31T23:59:59Z",
                },
            }
        }
    )

    site_id: str = Field(..., description="Site identifier")
    site_name: Optional[str] = Field(None, description="Site name")
    data_points: List[PerformanceDataPoint] = Field(
        ..., description="List of performance data points"
    )
    summary: Optional["SiteDataSummary"] = Field(None, description="Summary statistics")
    data_fallback: bool = Field(
        False, description="Indicates if previous month's data was used as fallback"
    )
    data_month: Optional[str] = Field(
        None, description="Month/Year of the data being displayed (e.g., '2025-08')"
    )


class SiteDataSummary(BaseModel):
    """Summary statistics for site performance data"""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "data_point_count": 1440,
                "avg_actual_power": 387.5,
                "avg_expected_power": 402.1,
                "avg_poa_irradiance": 612.3,
                "first_reading": "2024-01-01T00:00:00Z",
                "last_reading": "2024-01-31T23:59:59Z",
            }
        }
    )

    data_point_count: int = Field(..., ge=0, description="Number of data points")
    avg_actual_power: float = Field(..., ge=0, description="Average actual power (kW)")
    avg_expected_power: float = Field(
        ..., ge=0, description="Average expected power (kW)"
    )
    avg_poa_irradiance: float = Field(
        ..., ge=0, description="Average POA irradiance (W/m²)"
    )
    first_reading: datetime = Field(..., description="Timestamp of first reading")
    last_reading: datetime = Field(..., description="Timestamp of last reading")


class ErrorResponse(BaseModel):
    """Standard error response model"""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "error": "ValidationError",
                "message": "Invalid date range provided",
                "details": {
                    "field": "end_date",
                    "issue": "end_date must be after start_date",
                },
            }
        }
    )

    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    details: Optional[dict] = Field(None, description="Additional error details")


# Skid models
class SkidPerformance(BaseModel):
    """Skid performance data with aggregate metrics"""
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "skid_id": "SKID001",
                "skid_name": "Skid 01",
                "avg_actual_power": 450.5,
                "avg_expected_power": 468.2,
                "deviation_percentage": -3.8,
                "data_point_count": 1440
            }
        }
    )
    
    skid_id: str = Field(..., description="Unique identifier for the skid")
    skid_name: Optional[str] = Field(None, description="Human-readable name of the skid")
    avg_actual_power: float = Field(..., ge=0, description="Average actual power (kW)")
    avg_expected_power: float = Field(..., ge=0, description="Average expected power (kW)")
    deviation_percentage: float = Field(..., description="Performance deviation percentage")
    data_point_count: int = Field(..., ge=0, description="Number of data points")


class SkidsListResponse(BaseModel):
    """Response model for skids list endpoint"""
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "site_id": "SITE001",
                "skids": [
                    {
                        "skid_id": "SKID001",
                        "skid_name": "Skid 01",
                        "avg_actual_power": 450.5,
                        "avg_expected_power": 468.2,
                        "deviation_percentage": -3.8,
                        "data_point_count": 1440
                    }
                ],
                "total_count": 3
            }
        }
    )
    
    site_id: str = Field(..., description="Site identifier")
    skids: List[SkidPerformance] = Field(..., description="List of skid performance data")
    total_count: int = Field(..., ge=0, description="Total number of skids")


# Inverter models
class InverterPerformance(BaseModel):
    """Inverter performance data with individual metrics"""
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "inverter_id": "INV001",
                "inverter_name": "Inverter 01",
                "avg_actual_power": 45.5,
                "avg_expected_power": 46.8,
                "deviation_percentage": -2.8,
                "availability": 1.0,
                "data_point_count": 1440
            }
        }
    )
    
    inverter_id: str = Field(..., description="Unique identifier for the inverter")
    inverter_name: Optional[str] = Field(None, description="Human-readable name of the inverter")
    avg_actual_power: float = Field(..., ge=0, description="Average actual power (kW)")
    avg_expected_power: float = Field(..., ge=0, description="Average expected power (kW)")
    deviation_percentage: float = Field(..., description="Performance deviation percentage")
    availability: float = Field(..., ge=0, le=1, description="Inverter availability (0.0 to 1.0)")
    data_point_count: int = Field(..., ge=0, description="Number of data points")


class InvertersListResponse(BaseModel):
    """Response model for inverters list endpoint"""
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "skid_id": "SKID001",
                "inverters": [
                    {
                        "inverter_id": "INV001",
                        "inverter_name": "Inverter 01",
                        "avg_actual_power": 45.5,
                        "avg_expected_power": 46.8,
                        "deviation_percentage": -2.8,
                        "availability": 1.0,
                        "data_point_count": 1440
                    }
                ],
                "total_count": 10
            }
        }
    )
    
    skid_id: str = Field(..., description="Skid identifier")
    inverters: List[InverterPerformance] = Field(..., description="List of inverter performance data")
    total_count: int = Field(..., ge=0, description="Total number of inverters")


# Update forward references
SitePerformanceResponse.model_rebuild()
SkidsListResponse.model_rebuild()
InvertersListResponse.model_rebuild()
