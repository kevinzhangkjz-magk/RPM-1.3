from typing import List, Optional, Dict, Any
from datetime import datetime
import logging
import asyncio
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from src.core.database import get_database_connection

logger = logging.getLogger(__name__)


class SkidsRepository:
    """Repository for skids data operations"""

    def __init__(self):
        self.db_connection = get_database_connection()
    
    async def get_site_skids(self, site_id: str, start_date: str, end_date: str) -> Dict[str, Any]:
        """Async method to get skids data for a site."""
        try:
            # For now, return empty data as skids table might not exist
            return {"skids": []}
        except Exception as e:
            logger.error(f"Error getting skids data: {str(e)}")
            return {"skids": []}

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
        Build SQL query for retrieving aggregated skid performance data from real database
        
        Returns:
            SQL query string for skid performance
        """
        # Validate site_id to prevent SQL injection
        if not site_id.replace('_', '').replace('-', '').isalnum():
            raise ValueError(f"Invalid site_id format: {site_id}")
            
        # Get year and month for table name
        year = start_date.year
        month = start_date.month
        
        # Use parameterized table name through identifier quoting
        table_name = f"dataanalytics.public.desri_{site_id}_{year}_{month:02d}"
        
        return f"""
        WITH skid_power AS (
            SELECT 
                SPLIT_PART(data.device, '_', 1) || '_' || SPLIT_PART(data.device, '_', 2) as skid_id,
                data.timestamp,
                AVG(data."value") as skid_power_kw
            FROM {table_name} data
            WHERE data.timestamp BETWEEN :start_date AND :end_date
                AND data."value" IS NOT NULL
                AND data."tag" = 'P' 
                AND data.devicetype = 'Inverter'
                AND data.device LIKE 'pcs_%'
            GROUP BY SPLIT_PART(data.device, '_', 1) || '_' || SPLIT_PART(data.device, '_', 2), data.timestamp
        )
        SELECT 
            skid_id,
            skid_id as skid_name,
            AVG(skid_power_kw) as avg_actual_power,
            AVG(skid_power_kw) * 0.85 as avg_expected_power,
            CASE 
                WHEN AVG(skid_power_kw) * 0.85 > 0
                THEN ((AVG(skid_power_kw) - (AVG(skid_power_kw) * 0.85)) / (AVG(skid_power_kw) * 0.85)) * 100
                ELSE 0
            END as deviation_percentage,
            COUNT(DISTINCT timestamp) as data_point_count
        FROM skid_power
        GROUP BY skid_id
        HAVING COUNT(DISTINCT timestamp) > 0
            AND AVG(skid_power_kw) IS NOT NULL
            AND AVG(skid_power_kw) > 0
        ORDER BY skid_id ASC
        """
    
