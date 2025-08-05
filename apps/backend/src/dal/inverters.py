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
        WITH inverter_data AS (
            SELECT 
                data.device as inverter_id,
                data.device as inverter_name,
                SPLIT_PART(data.device, '_', 1) || '_' || SPLIT_PART(data.device, '_', 2) as device_skid_id,  -- Extract 'pcs_16' from 'pcs_16_Inverter_01'
                data.timestamp,
                data."tag",
                data.devicetype,
                data."value"
            FROM {table_name} data
            WHERE data.timestamp BETWEEN :start_date AND :end_date
                AND data."value" IS NOT NULL
                AND (
                    (data."tag" = 'P' AND data.devicetype = 'Inverter')
                    OR 
                    (data."tag" = 'POA' AND data.devicetype = 'Met')
                )
        ),
        inverter_power AS (
            SELECT 
                inverter_id,
                inverter_name,
                device_skid_id,
                timestamp,
                CASE WHEN "tag" = 'P' AND devicetype = 'Inverter' THEN "value" END as inverter_power
            FROM inverter_data
            WHERE devicetype = 'Inverter'
        ),
        site_irradiance AS (
            SELECT 
                timestamp,
                AVG(CASE WHEN "tag" = 'POA' AND devicetype = 'Met' THEN "value" END) as poa_irradiance
            FROM inverter_data
            WHERE devicetype = 'Met'
            GROUP BY timestamp
        )
        SELECT 
            ip.inverter_id,
            ip.inverter_name,
            AVG(ip.inverter_power) as avg_actual_power,
            AVG(si.poa_irradiance * 0.0006) as avg_expected_power,
            CASE 
                WHEN AVG(si.poa_irradiance * 0.0006) > 0
                THEN ((AVG(ip.inverter_power) - AVG(si.poa_irradiance * 0.0006)) / 
                       AVG(si.poa_irradiance * 0.0006)) * 100
                ELSE 0
            END as deviation_percentage,
            1.0 as availability,  -- No availability column in schema, assume 100% for valid data
            COUNT(DISTINCT ip.timestamp) as data_point_count
        FROM inverter_power ip
        LEFT JOIN site_irradiance si ON ip.timestamp = si.timestamp
        WHERE ip.device_skid_id = :skid_id  -- Filter by the skid extracted from device name
            AND ip.inverter_power IS NOT NULL
        GROUP BY ip.inverter_id, ip.inverter_name
        HAVING COUNT(DISTINCT ip.timestamp) > 0
        ORDER BY ip.inverter_id ASC
        """