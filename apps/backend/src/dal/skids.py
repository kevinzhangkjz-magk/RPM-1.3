from typing import List, Optional, Dict, Any
from datetime import datetime
import logging
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from src.core.database import get_database_connection

logger = logging.getLogger(__name__)


class SkidsRepository:
    """Repository for skids data operations"""

    def __init__(self):
        self.db_connection = get_database_connection()

    def get_skids_performance_data(
        self, site_id: str, start_date: datetime, end_date: datetime
    ) -> List[Dict[str, Any]]:
        """
        Retrieve aggregated performance data for all skids on a site
        
        Args:
            site_id: The site identifier
            start_date: Start date for data retrieval
            end_date: End date for data retrieval
            
        Returns:
            List of skid performance data with aggregated metrics
            
        Raises:
            SQLAlchemyError: If database query fails
        """
        try:
            engine = self.db_connection.get_engine()
            query = self._build_skids_performance_query(site_id, start_date, end_date)
            
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
                f"Database error retrieving skids data for site {site_id}: {e}"
            )
            raise
        except Exception as e:
            logger.error(
                f"Unexpected error retrieving skids data for site {site_id}: {e}"
            )
            raise

    def _build_skids_performance_query(
        self, site_id: str, start_date: datetime, end_date: datetime
    ) -> str:
        """
        Build SQL query for retrieving aggregated skid performance data
        
        Returns:
            SQL query string for skid performance
        """
        # Validate site_id to prevent SQL injection
        if not site_id.replace('_', '').replace('-', '').isalnum():
            raise ValueError(f"Invalid site_id format: {site_id}")
            
        # Query aggregates data at skid level with 100% availability filter
        year = start_date.year
        month = start_date.month
        
        # Use parameterized table name through identifier quoting
        table_name = f"dataanalytics.public.desri_{site_id}_{year}_{month:02d}"
        
        return f"""
        SELECT 
            data.skid_id,
            data.skid_id as skid_name,
            AVG(CASE WHEN data."tag" = 'P' AND data.devicetype = 'rmt' THEN data."value" END) as avg_actual_power,
            AVG(CASE WHEN data."tag" = 'POA' AND data.devicetype = 'Met' THEN data."value" * 0.0006 END) as avg_expected_power,
            CASE 
                WHEN AVG(CASE WHEN data."tag" = 'POA' AND data.devicetype = 'Met' THEN data."value" * 0.0006 END) > 0
                THEN ((AVG(CASE WHEN data."tag" = 'P' AND data.devicetype = 'rmt' THEN data."value" END) - 
                       AVG(CASE WHEN data."tag" = 'POA' AND data.devicetype = 'Met' THEN data."value" * 0.0006 END)) / 
                       AVG(CASE WHEN data."tag" = 'POA' AND data.devicetype = 'Met' THEN data."value" * 0.0006 END)) * 100
                ELSE 0
            END as deviation_percentage,
            COUNT(DISTINCT data.timestamp) as data_point_count
        FROM {table_name} data
        WHERE data.timestamp BETWEEN :start_date AND :end_date
            AND data.inverter_availability = 1
            AND (
                (data."tag" = 'P' AND data.devicetype = 'rmt')
                OR 
                (data."tag" = 'POA' AND data.devicetype = 'Met')
            )
        GROUP BY data.skid_id
        HAVING COUNT(DISTINCT data.timestamp) > 0
        ORDER BY data.skid_id ASC
        """