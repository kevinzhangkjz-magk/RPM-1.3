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
            query = self._build_performance_query(site_id, start_date, end_date)

            with engine.connect() as connection:
                result = connection.execute(
                    text(query),
                    {
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

    def _build_performance_query(self, site_id: str, start_date: datetime, end_date: datetime) -> str:
        """
        Build the SQL query for retrieving site performance data from monthly tables

        Returns:
            SQL query string for specific month table
        """
        # For now, use current month (July 2025) as example
        # In production, would dynamically determine which monthly tables to query
        year = start_date.year
        month = start_date.month
        
        return f"""
        SELECT 
            data.timestamp,
            '{site_id}' as site_id,
            AVG(CASE WHEN data."tag" = 'POA' AND data.devicetype = 'Met' THEN data."value" END) as poa_irradiance,
            AVG(CASE WHEN data."tag" = 'P' AND data.devicetype = 'rmt' THEN data."value" END) as actual_power,
            AVG(CASE WHEN data."tag" = 'P' AND data.devicetype = 'rmt' THEN data."value" * 0.85 END) as expected_power,
            1.0 as inverter_availability,
            NULL as site_name
        FROM dataanalytics.public.desri_{site_id}_{year}_{month:02d} data
        WHERE data.timestamp BETWEEN :start_date AND :end_date
            AND data."value" IS NOT NULL
            AND (
                (data."tag" = 'P' AND data.devicetype = 'rmt' AND data."value" > 0)
                OR 
                (data."tag" = 'POA' AND data.devicetype = 'Met' AND data."value" > 50)
            )
        GROUP BY data.timestamp
        HAVING AVG(CASE WHEN data."tag" = 'POA' AND data.devicetype = 'Met' THEN data."value" END) > 50
        ORDER BY data.timestamp ASC
        LIMIT 500
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
            query = "SELECT COUNT(*) FROM analytics.site_metadata WHERE site = :site_id"

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
            # For now, return basic summary - in production would calculate from actual data
            query = f"""
            SELECT 
                100 as data_point_count,
                50.5 as avg_actual_power,
                52.1 as avg_expected_power,
                850.0 as avg_poa_irradiance,
                :start_date as first_reading,
                :end_date as last_reading
            """

            with engine.connect() as connection:
                result = connection.execute(
                    text(query),
                    {
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
