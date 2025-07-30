from typing import List, Optional, Dict, Any
from datetime import datetime
import logging
from sqlalchemy import text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError

from src.core.database import get_database_connection

logger = logging.getLogger(__name__)


class SitePerformanceRepository:
    """Repository for site performance data operations"""

    def __init__(self):
        self.db_connection = get_database_connection()

    def get_site_performance_data(
        self, site_id: str, start_date: datetime, end_date: datetime
    ) -> List[Dict[str, Any]]:
        """
        Retrieve time-series performance data for a specific site

        Args:
            site_id: The site identifier
            start_date: Start date for data retrieval
            end_date: End date for data retrieval

        Returns:
            List of performance data points

        Raises:
            SQLAlchemyError: If database query fails
        """
        try:
            engine = self.db_connection.get_engine()
            query = self._build_performance_query()

            with engine.connect() as connection:
                result = connection.execute(
                    text(query),
                    {
                        "site_id": site_id,
                        "start_date": start_date,
                        "end_date": end_date,
                    },
                )

                columns = result.keys()
                rows = result.fetchall()

                return [dict(zip(columns, row)) for row in rows]

        except SQLAlchemyError as e:
            logger.error(
                f"Database error retrieving performance data for site {site_id}: {e}"
            )
            raise
        except Exception as e:
            logger.error(
                f"Unexpected error retrieving performance data for site {site_id}: {e}"
            )
            raise

    def _build_performance_query(self) -> str:
        """
        Build the SQL query for retrieving site performance data

        Returns:
            SQL query string
        """
        return """
        SELECT 
            t.timestamp,
            t.site_id,
            t.poa_irradiance,
            t.actual_power,
            t.expected_power,
            t.inverter_availability,
            s.site_name
        FROM inverter_telemetry t
        INNER JOIN sites s ON t.site_id = s.site_id
        WHERE t.site_id = :site_id
            AND t.timestamp BETWEEN :start_date AND :end_date
            AND t.inverter_availability = 1.0
        ORDER BY t.timestamp ASC
        """

    def validate_site_exists(self, site_id: str) -> bool:
        """
        Check if a site exists in the database

        Args:
            site_id: The site identifier to validate

        Returns:
            True if site exists, False otherwise
        """
        try:
            engine = self.db_connection.get_engine()
            query = "SELECT COUNT(*) FROM sites WHERE site_id = :site_id"

            with engine.connect() as connection:
                result = connection.execute(text(query), {"site_id": site_id})
                count = result.fetchone()[0]
                return count > 0

        except SQLAlchemyError as e:
            logger.error(f"Database error validating site {site_id}: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error validating site {site_id}: {e}")
            return False

    def get_site_data_summary(
        self, site_id: str, start_date: datetime, end_date: datetime
    ) -> Optional[Dict[str, Any]]:
        """
        Get summary statistics for site performance data

        Args:
            site_id: The site identifier
            start_date: Start date for summary
            end_date: End date for summary

        Returns:
            Dictionary with summary statistics or None if no data
        """
        try:
            engine = self.db_connection.get_engine()
            query = """
            SELECT 
                COUNT(*) as data_point_count,
                AVG(actual_power) as avg_actual_power,
                AVG(expected_power) as avg_expected_power,
                AVG(poa_irradiance) as avg_poa_irradiance,
                MIN(timestamp) as first_reading,
                MAX(timestamp) as last_reading
            FROM inverter_telemetry t
            WHERE t.site_id = :site_id
                AND t.timestamp BETWEEN :start_date AND :end_date
                AND t.inverter_availability = 1.0
            """

            with engine.connect() as connection:
                result = connection.execute(
                    text(query),
                    {
                        "site_id": site_id,
                        "start_date": start_date,
                        "end_date": end_date,
                    },
                )

                row = result.fetchone()
                if row and row[0] > 0:  # data_point_count > 0
                    columns = result.keys()
                    return dict(zip(columns, row))

                return None

        except SQLAlchemyError as e:
            logger.error(f"Database error getting summary for site {site_id}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error getting summary for site {site_id}: {e}")
            raise
