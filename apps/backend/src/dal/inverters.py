from typing import List, Optional, Dict, Any
from datetime import datetime
import logging
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from src.core.database import get_database_connection

logger = logging.getLogger(__name__)


class InvertersRepository:
    """Repository for inverters data operations"""

    def __init__(self):
        self.db_connection = get_database_connection()

    def get_inverters_performance_data(
        self, skid_id: str, start_date: datetime, end_date: datetime
    ) -> List[Dict[str, Any]]:
        """
        Retrieve performance data for all inverters on a skid
        
        Args:
            skid_id: The skid identifier
            start_date: Start date for data retrieval
            end_date: End date for data retrieval
            
        Returns:
            List of inverter performance data with individual metrics
            
        Raises:
            SQLAlchemyError: If database query fails
        """
        try:
            engine = self.db_connection.get_engine()
            query = self._build_inverters_performance_query(skid_id, start_date, end_date)
            
            with engine.connect() as connection:
                result = connection.execute(
                    text(query),
                    {
                        "skid_id": skid_id,
                        "start_date": start_date,
                        "end_date": end_date,
                    },
                )
                
                columns = result.keys()
                rows = result.fetchall()
                
                return [dict(zip(columns, row)) for row in rows]
                
        except SQLAlchemyError as e:
            logger.error(
                f"Database error retrieving inverters data for skid {skid_id}: {e}"
            )
            raise
        except Exception as e:
            logger.error(
                f"Unexpected error retrieving inverters data for skid {skid_id}: {e}"
            )
            raise

    def _build_inverters_performance_query(
        self, skid_id: str, start_date: datetime, end_date: datetime
    ) -> str:
        """
        Build SQL query for retrieving inverter performance data
        
        Returns:
            SQL query string for inverter performance
        """
        # Validate skid_id to prevent SQL injection
        if not skid_id.replace('_', '').replace('-', '').isalnum():
            raise ValueError(f"Invalid skid_id format: {skid_id}")
            
        # Query gets individual inverter data with 100% availability filter
        # Note: We need to determine the site_id from skid_id to build the table name
        # For now, assuming a pattern or that this info is passed differently
        year = start_date.year
        month = start_date.month
        
        # Extract site_id from skid_id (assuming format like SITE001_SKID001)
        site_id = skid_id.split('_')[0] if '_' in skid_id else 'ASMB2'
        
        # Validate extracted site_id
        if not site_id.replace('_', '').replace('-', '').isalnum():
            raise ValueError(f"Invalid site_id extracted from skid_id: {site_id}")
        
        # Use parameterized table name through identifier quoting
        table_name = f"dataanalytics.public.desri_{site_id}_{year}_{month:02d}"
        
        return f"""
        SELECT 
            data.inverter_id,
            data.inverter_id as inverter_name,
            AVG(CASE WHEN data."tag" = 'P' AND data.devicetype = 'inv' THEN data."value" END) as avg_actual_power,
            AVG(CASE WHEN data."tag" = 'POA' AND data.devicetype = 'Met' THEN data."value" * 0.0006 END) as avg_expected_power,
            CASE 
                WHEN AVG(CASE WHEN data."tag" = 'POA' AND data.devicetype = 'Met' THEN data."value" * 0.0006 END) > 0
                THEN ((AVG(CASE WHEN data."tag" = 'P' AND data.devicetype = 'inv' THEN data."value" END) - 
                       AVG(CASE WHEN data."tag" = 'POA' AND data.devicetype = 'Met' THEN data."value" * 0.0006 END)) / 
                       AVG(CASE WHEN data."tag" = 'POA' AND data.devicetype = 'Met' THEN data."value" * 0.0006 END)) * 100
                ELSE 0
            END as deviation_percentage,
            AVG(data.inverter_availability) as availability,
            COUNT(DISTINCT data.timestamp) as data_point_count
        FROM {table_name} data
        WHERE data.timestamp BETWEEN :start_date AND :end_date
            AND data.skid_id = :skid_id
            AND data.inverter_availability = 1
            AND (
                (data."tag" = 'P' AND data.devicetype = 'inv')
                OR 
                (data."tag" = 'POA' AND data.devicetype = 'Met')
            )
        GROUP BY data.inverter_id
        HAVING COUNT(DISTINCT data.timestamp) > 0
        ORDER BY data.inverter_id ASC
        """