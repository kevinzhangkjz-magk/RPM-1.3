import pytest
from datetime import datetime, timedelta
from pydantic import ValidationError

from src.models.site_performance import (
    Site,
    SiteDetails,
    SitesListResponse,
    PerformanceDataPoint,
    SitePerformanceQueryParams,
    SitePerformanceResponse,
    SiteDataSummary,
    ErrorResponse,
)


class TestSite:
    """Tests for Site model"""

    def test_site_valid_data(self):
        """Test Site model with valid data"""
        site = Site(site_id="SITE001", site_name="Solar Farm Alpha")

        assert site.site_id == "SITE001"
        assert site.site_name == "Solar Farm Alpha"

    def test_site_without_name(self):
        """Test Site model without optional name"""
        site = Site(site_id="SITE001")

        assert site.site_id == "SITE001"
        assert site.site_name is None

    def test_site_missing_required_field(self):
        """Test Site model with missing required field"""
        with pytest.raises(ValidationError) as exc_info:
            Site()

        assert "site_id" in str(exc_info.value)


class TestPerformanceDataPoint:
    """Tests for PerformanceDataPoint model"""

    def test_performance_data_point_valid(self):
        """Test PerformanceDataPoint with valid data"""
        data_point = PerformanceDataPoint(
            timestamp=datetime(2024, 1, 15, 12, 0),
            site_id="SITE001",
            poa_irradiance=850.5,
            actual_power=456.2,
            expected_power=475.8,
            inverter_availability=1.0,
            site_name="Solar Farm Alpha",
        )

        assert data_point.timestamp == datetime(2024, 1, 15, 12, 0)
        assert data_point.site_id == "SITE001"
        assert data_point.poa_irradiance == 850.5
        assert data_point.actual_power == 456.2
        assert data_point.expected_power == 475.8
        assert data_point.inverter_availability == 1.0
        assert data_point.site_name == "Solar Farm Alpha"

    def test_performance_data_point_negative_values(self):
        """Test PerformanceDataPoint with negative values (should fail)"""
        with pytest.raises(ValidationError) as exc_info:
            PerformanceDataPoint(
                timestamp=datetime(2024, 1, 15, 12, 0),
                site_id="SITE001",
                poa_irradiance=-100.0,  # Negative value
                actual_power=456.2,
                expected_power=475.8,
                inverter_availability=1.0,
            )

        assert "poa_irradiance" in str(exc_info.value)

    def test_performance_data_point_invalid_availability(self):
        """Test PerformanceDataPoint with invalid inverter availability"""
        with pytest.raises(ValidationError) as exc_info:
            PerformanceDataPoint(
                timestamp=datetime(2024, 1, 15, 12, 0),
                site_id="SITE001",
                poa_irradiance=850.5,
                actual_power=456.2,
                expected_power=475.8,
                inverter_availability=1.5,  # > 1.0
            )

        assert "inverter_availability" in str(exc_info.value)


class TestSitePerformanceQueryParams:
    """Tests for SitePerformanceQueryParams model"""

    def test_query_params_valid(self):
        """Test query params with valid date range"""
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 1, 31)

        params = SitePerformanceQueryParams(start_date=start_date, end_date=end_date)

        assert params.start_date == start_date
        assert params.end_date == end_date

    def test_query_params_invalid_date_range(self):
        """Test query params with end_date before start_date"""
        start_date = datetime(2024, 1, 31)
        end_date = datetime(2024, 1, 1)  # Before start_date

        with pytest.raises(ValidationError) as exc_info:
            SitePerformanceQueryParams(start_date=start_date, end_date=end_date)

        assert "end_date must be after start_date" in str(exc_info.value)

    def test_query_params_future_dates(self):
        """Test query params with future dates"""
        future_date = datetime.now() + timedelta(days=1)

        with pytest.raises(ValidationError) as exc_info:
            SitePerformanceQueryParams(
                start_date=future_date, end_date=future_date + timedelta(days=1)
            )

        assert "Date cannot be in the future" in str(exc_info.value)


class TestSiteDataSummary:
    """Tests for SiteDataSummary model"""

    def test_site_data_summary_valid(self):
        """Test SiteDataSummary with valid data"""
        summary = SiteDataSummary(
            data_point_count=1440,
            avg_actual_power=387.5,
            avg_expected_power=402.1,
            avg_poa_irradiance=612.3,
            first_reading=datetime(2024, 1, 1),
            last_reading=datetime(2024, 1, 31),
        )

        assert summary.data_point_count == 1440
        assert summary.avg_actual_power == 387.5
        assert summary.avg_expected_power == 402.1
        assert summary.avg_poa_irradiance == 612.3
        assert summary.first_reading == datetime(2024, 1, 1)
        assert summary.last_reading == datetime(2024, 1, 31)

    def test_site_data_summary_negative_count(self):
        """Test SiteDataSummary with negative data point count"""
        with pytest.raises(ValidationError) as exc_info:
            SiteDataSummary(
                data_point_count=-1,  # Negative count
                avg_actual_power=387.5,
                avg_expected_power=402.1,
                avg_poa_irradiance=612.3,
                first_reading=datetime(2024, 1, 1),
                last_reading=datetime(2024, 1, 31),
            )

        assert "data_point_count" in str(exc_info.value)


class TestSitePerformanceResponse:
    """Tests for SitePerformanceResponse model"""

    def test_performance_response_valid(self):
        """Test SitePerformanceResponse with valid data"""
        data_point = PerformanceDataPoint(
            timestamp=datetime(2024, 1, 15, 12, 0),
            site_id="SITE001",
            poa_irradiance=850.5,
            actual_power=456.2,
            expected_power=475.8,
            inverter_availability=1.0,
            site_name="Solar Farm Alpha",
        )

        summary = SiteDataSummary(
            data_point_count=1,
            avg_actual_power=456.2,
            avg_expected_power=475.8,
            avg_poa_irradiance=850.5,
            first_reading=datetime(2024, 1, 15, 12, 0),
            last_reading=datetime(2024, 1, 15, 12, 0),
        )

        response = SitePerformanceResponse(
            site_id="SITE001",
            site_name="Solar Farm Alpha",
            data_points=[data_point],
            summary=summary,
        )

        assert response.site_id == "SITE001"
        assert response.site_name == "Solar Farm Alpha"
        assert len(response.data_points) == 1
        assert response.summary is not None
        assert response.summary.data_point_count == 1

    def test_performance_response_without_summary(self):
        """Test SitePerformanceResponse without optional summary"""
        data_point = PerformanceDataPoint(
            timestamp=datetime(2024, 1, 15, 12, 0),
            site_id="SITE001",
            poa_irradiance=850.5,
            actual_power=456.2,
            expected_power=475.8,
            inverter_availability=1.0,
        )

        response = SitePerformanceResponse(site_id="SITE001", data_points=[data_point])

        assert response.site_id == "SITE001"
        assert response.site_name is None
        assert len(response.data_points) == 1
        assert response.summary is None


class TestErrorResponse:
    """Tests for ErrorResponse model"""

    def test_error_response_valid(self):
        """Test ErrorResponse with valid data"""
        error = ErrorResponse(
            error="ValidationError",
            message="Invalid date range provided",
            details={"field": "end_date", "issue": "end_date must be after start_date"},
        )

        assert error.error == "ValidationError"
        assert error.message == "Invalid date range provided"
        assert error.details["field"] == "end_date"

    def test_error_response_without_details(self):
        """Test ErrorResponse without optional details"""
        error = ErrorResponse(error="DatabaseError", message="Connection failed")

        assert error.error == "DatabaseError"
        assert error.message == "Connection failed"
        assert error.details is None


class TestModelSerialization:
    """Tests for model serialization/deserialization"""

    def test_performance_data_point_json(self):
        """Test PerformanceDataPoint JSON serialization"""
        data_point = PerformanceDataPoint(
            timestamp=datetime(2024, 1, 15, 12, 0),
            site_id="SITE001",
            poa_irradiance=850.5,
            actual_power=456.2,
            expected_power=475.8,
            inverter_availability=1.0,
            site_name="Solar Farm Alpha",
        )

        # Test serialization
        json_data = data_point.model_dump()
        assert json_data["site_id"] == "SITE001"
        assert json_data["poa_irradiance"] == 850.5

        # Test deserialization
        new_data_point = PerformanceDataPoint(**json_data)
        assert new_data_point.site_id == data_point.site_id
        assert new_data_point.poa_irradiance == data_point.poa_irradiance


class TestSiteDetails:
    """Tests for SiteDetails model"""

    def test_site_details_valid_data(self):
        """Test SiteDetails with valid data"""
        from datetime import date

        site_details = SiteDetails(
            site_id="SITE001",
            site_name="Solar Farm Alpha",
            location="Arizona, USA",
            capacity_kw=5000.0,
            installation_date=date(2023, 1, 15),
            status="active",
        )

        assert site_details.site_id == "SITE001"
        assert site_details.site_name == "Solar Farm Alpha"
        assert site_details.location == "Arizona, USA"
        assert site_details.capacity_kw == 5000.0
        assert site_details.installation_date == date(2023, 1, 15)
        assert site_details.status == "active"

    def test_site_details_minimal_data(self):
        """Test SiteDetails with only required fields"""
        site_details = SiteDetails(site_id="SITE001")

        assert site_details.site_id == "SITE001"
        assert site_details.site_name is None
        assert site_details.location is None
        assert site_details.capacity_kw is None
        assert site_details.installation_date is None
        assert site_details.status is None

    def test_site_details_negative_capacity(self):
        """Test SiteDetails with negative capacity (should fail)"""
        with pytest.raises(ValidationError) as exc_info:
            SiteDetails(site_id="SITE001", capacity_kw=-1000.0)  # Negative capacity

        assert "capacity_kw" in str(exc_info.value)

    def test_site_details_missing_required_field(self):
        """Test SiteDetails with missing required field"""
        with pytest.raises(ValidationError) as exc_info:
            SiteDetails()

        assert "site_id" in str(exc_info.value)

    def test_site_details_json_serialization(self):
        """Test SiteDetails JSON serialization"""
        from datetime import date

        site_details = SiteDetails(
            site_id="SITE001",
            site_name="Solar Farm Alpha",
            location="Arizona, USA",
            capacity_kw=5000.0,
            installation_date=date(2023, 1, 15),
            status="active",
        )

        # Test serialization
        json_data = site_details.model_dump()
        assert json_data["site_id"] == "SITE001"
        assert json_data["site_name"] == "Solar Farm Alpha"
        assert json_data["capacity_kw"] == 5000.0

        # Test deserialization
        new_site_details = SiteDetails(**json_data)
        assert new_site_details.site_id == site_details.site_id
        assert new_site_details.site_name == site_details.site_name


class TestSitesListResponse:
    """Tests for SitesListResponse model"""

    def test_sites_list_response_valid(self):
        """Test SitesListResponse with valid data"""
        from datetime import date

        site1 = SiteDetails(
            site_id="SITE001",
            site_name="Solar Farm Alpha",
            location="Arizona, USA",
            capacity_kw=5000.0,
            installation_date=date(2023, 1, 15),
            status="active",
        )

        site2 = SiteDetails(
            site_id="SITE002",
            site_name="Solar Farm Beta",
            location="California, USA",
            capacity_kw=3000.0,
            installation_date=date(2023, 3, 20),
            status="active",
        )

        response = SitesListResponse(sites=[site1, site2], total_count=2)

        assert len(response.sites) == 2
        assert response.total_count == 2
        assert response.sites[0].site_id == "SITE001"
        assert response.sites[1].site_id == "SITE002"

    def test_sites_list_response_empty(self):
        """Test SitesListResponse with empty sites list"""
        response = SitesListResponse(sites=[], total_count=0)

        assert len(response.sites) == 0
        assert response.total_count == 0

    def test_sites_list_response_negative_count(self):
        """Test SitesListResponse with negative total count (should fail)"""
        with pytest.raises(ValidationError) as exc_info:
            SitesListResponse(sites=[], total_count=-1)  # Negative count

        assert "total_count" in str(exc_info.value)

    def test_sites_list_response_missing_required_fields(self):
        """Test SitesListResponse with missing required fields"""
        with pytest.raises(ValidationError) as exc_info:
            SitesListResponse()

        error_str = str(exc_info.value)
        assert "sites" in error_str or "total_count" in error_str

    def test_sites_list_response_json_serialization(self):
        """Test SitesListResponse JSON serialization"""
        from datetime import date

        site = SiteDetails(
            site_id="SITE001",
            site_name="Solar Farm Alpha",
            location="Arizona, USA",
            capacity_kw=5000.0,
            installation_date=date(2023, 1, 15),
            status="active",
        )

        response = SitesListResponse(sites=[site], total_count=1)

        # Test serialization
        json_data = response.model_dump()
        assert json_data["total_count"] == 1
        assert len(json_data["sites"]) == 1
        assert json_data["sites"][0]["site_id"] == "SITE001"

        # Test deserialization
        new_response = SitesListResponse(**json_data)
        assert new_response.total_count == response.total_count
        assert len(new_response.sites) == len(response.sites)
        assert new_response.sites[0].site_id == response.sites[0].site_id
