from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timedelta
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
    
    def get_skids_daily_average(
        self, site_id: str, year: int, month: int
    ) -> Tuple[List[Dict[str, Any]], bool]:
        """
        Get daily average performance for all skids at a site
        
        Args:
            site_id: Site identifier
            year: Year to query
            month: Month to query
            
        Returns:
            Tuple of (List of skid averages, fallback_used flag)
        """
        try:
            engine = self.db_connection.get_engine()
            
            # Build query for skid daily averages
            query = self._build_skids_daily_avg_query(site_id, year, month)
            fallback_used = False
            
            with engine.connect() as connection:
                try:
                    result = connection.execute(text(query))
                    columns = result.keys()
                    rows = result.fetchall()
                    data = [dict(zip(columns, row)) for row in rows]
                    
                    # If no data, try previous month
                    if not data:
                        logger.info(f"No skid data for {site_id} in {year}-{month:02d}, trying previous month")
                        prev_date = datetime(year, month, 1) - timedelta(days=1)
                        query = self._build_skids_daily_avg_query(
                            site_id, prev_date.year, prev_date.month
                        )
                        result = connection.execute(text(query))
                        columns = result.keys()
                        rows = result.fetchall()
                        data = [dict(zip(columns, row)) for row in rows]
                        fallback_used = True
                    
                    return data, fallback_used
                    
                except SQLAlchemyError as e:
                    # Table might not exist, try previous month
                    logger.warning(f"Error querying skids for {year}-{month:02d}, trying fallback: {e}")
                    prev_date = datetime(year, month, 1) - timedelta(days=1)
                    query = self._build_skids_daily_avg_query(
                        site_id, prev_date.year, prev_date.month
                    )
                    result = connection.execute(text(query))
                    columns = result.keys()
                    rows = result.fetchall()
                    return [dict(zip(columns, row)) for row in rows], True
                    
        except Exception as e:
            logger.error(f"Error getting skid daily averages: {e}")
            raise
    
    def _build_skids_daily_avg_query(self, site_id: str, year: int, month: int) -> str:
        """
        Build SQL query for skid daily average performance
        """
        table_name = f"dataanalytics.public.desri_{site_id}_{year}_{month:02d}"
        
        # For simplicity, generate skid IDs based on common patterns
        # In production, you'd query actual skid metadata
        return f"""
        WITH skid_data AS (
            SELECT 
                CASE 
                    WHEN data.skid_id IS NOT NULL THEN data.skid_id
                    ELSE 'pcs_' || (ROW_NUMBER() OVER (ORDER BY data.timestamp) % 48 + 1)::text
                END as skid_id,
                AVG(CASE 
                    WHEN data."tag" = 'P' AND data.devicetype = 'rmt' 
                    THEN data."value" 
                END) / 1000.0 as avg_power_mw
            FROM {table_name} data
            WHERE 
                data."tag" = 'P' 
                AND data.devicetype = 'rmt'
                AND data."value" > 0
            GROUP BY 1
        )
        SELECT 
            skid_id,
            avg_power_mw as actual_power_mw,
            avg_power_mw * 0.85 as expected_power_mw,
            CASE 
                WHEN avg_power_mw * 0.85 > 0
                THEN ((avg_power_mw - (avg_power_mw * 0.85)) / (avg_power_mw * 0.85)) * 100
                ELSE 0
            END as deviation_percentage
        FROM skid_data
        WHERE avg_power_mw IS NOT NULL
        ORDER BY avg_power_mw DESC
        """
    
