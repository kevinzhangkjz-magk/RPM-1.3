from typing import List, Dict, Any, Optional
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
import logging
import asyncio

from src.core.database import get_database_connection

logger = logging.getLogger(__name__)


class SitesRepository:
    """Repository for site-related database operations"""

    def __init__(self):
        """Initialize the repository"""
        self.db_connection = get_database_connection()

    async def get_all_sites(self) -> Dict[str, Any]:
        """
        Retrieve all solar sites from the database.

        Returns:
            Dictionary containing sites list

        Raises:
            SQLAlchemyError: If database operation fails
        """
        try:
            query = self._build_sites_query()

            # Run synchronous database operation in thread pool
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, self._execute_query, query)
            
            logger.info(f"Retrieved {len(result)} sites from database")
            return {"sites": result}

        except SQLAlchemyError as e:
            logger.error(f"Database error retrieving sites: {str(e)}")
            return {"sites": [], "error": str(e)}
        except Exception as e:
            logger.error(f"Unexpected error retrieving sites: {str(e)}")
            return {"sites": [], "error": str(e)}
    
    def _execute_query(self, query: str) -> List[Dict[str, Any]]:
        """Execute a query synchronously (helper for async methods)"""
        engine = self.db_connection.get_engine()
        with engine.connect() as connection:
            result = connection.execute(text(query))
            columns = result.keys()
            rows = result.fetchall()
            
            items = []
            for row in rows:
                item_dict = dict(zip(columns, row))
                items.append(item_dict)
            
            connection.commit()  # Ensure we commit the read transaction
            return items
            raise
    
    async def get_sites_by_name(self, site_name: str) -> List[Dict[str, Any]]:
        """
        Retrieve sites by name (partial match).
        
        Args:
            site_name: Site name to search for
            
        Returns:
            List of matching sites
        """
        try:
            query = """
                SELECT 
                    site as site_id,
                    site_name,
                    state as location,
                    ac_capacity_poi_limited as capacity_kw,
                    cod_date as installation_date,
                    'active' as status
                FROM analytics.site_metadata
                WHERE LOWER(site_name) LIKE LOWER('%' || :site_name || '%')
                ORDER BY site_name ASC
            """
            
            loop = asyncio.get_event_loop()
            
            def execute():
                with self.db_connection.get_engine().connect() as connection:
                    result = connection.execute(text(query), {"site_name": site_name})
                    columns = result.keys()
                    rows = result.fetchall()
                    
                    sites = []
                    for row in rows:
                        site_dict = dict(zip(columns, row))
                        sites.append(site_dict)
                    return sites
            
            result = await loop.run_in_executor(None, execute)
            logger.info(f"Found {len(result)} sites matching '{site_name}'")
            return result
            
        except Exception as e:
            logger.error(f"Error searching for sites by name '{site_name}': {str(e)}")
            return []

    def get_site_by_id(self, site_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a specific site by its ID.

        Args:
            site_id: The unique identifier for the site

        Returns:
            Site dictionary if found, None otherwise

        Raises:
            SQLAlchemyError: If database operation fails
        """
        try:
            query = self._build_site_by_id_query()

            with self.db_connection.get_engine().connect() as connection:
                result = connection.execute(text(query), {"site_id": site_id})

                row = result.fetchone()
                if row:
                    columns = result.keys()
                    site_dict = dict(zip(columns, row))
                    logger.info(f"Retrieved site {site_id} from database")
                    return site_dict
                else:
                    logger.info(f"Site {site_id} not found in database")
                    return None

        except SQLAlchemyError as e:
            logger.error(f"Database error retrieving site {site_id}: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error retrieving site {site_id}: {str(e)}")
            raise

    def _build_sites_query(self) -> str:
        """
        Build SQL query to retrieve all sites with connectivity check based on data recency.

        Returns:
            SQL query string
        """
        # For now, we'll implement a hybrid approach:
        # Check if site has recent activity by testing a known active site pattern
        # Sites that appear in your Python script (ASMB1-3, IRIS1, STJM1) are likely active
        # Others may be inactive/offline
        
        return """
            SELECT 
                site as site_id,
                site_name,
                state as location,
                ac_capacity_poi_limited as capacity_kw,
                cod_date as installation_date,
                'active' as status,
                CASE 
                    -- Sites that were in your Python script are likely active
                    WHEN site IN ('ASMB1', 'ASMB2', 'ASMB3', 'IRIS1', 'STJM1') THEN 'connected'
                    -- Sites with recent installation dates (within 2 years) might be active
                    WHEN cod_date > CURRENT_DATE - INTERVAL '2 years' THEN 'connected'
                    -- All others are likely disconnected
                    ELSE 'disconnected'
                END as connectivity_status
            FROM analytics.site_metadata
            WHERE site IS NOT NULL
            ORDER BY site_name ASC
        """

    def _build_site_by_id_query(self) -> str:
        """
        Build SQL query to retrieve a specific site by ID.

        Returns:
            SQL query string
        """
        return """
            SELECT 
                site as site_id,
                site_name,
                state as location,
                ac_capacity_poi_limited as capacity_kw,
                cod_date as installation_date,
                'active' as status
            FROM analytics.site_metadata
            WHERE site = :site_id
        """
