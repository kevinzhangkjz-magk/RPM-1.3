from typing import List, Dict, Any, Optional
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
import logging

from src.core.database import get_database_connection

logger = logging.getLogger(__name__)


class SitesRepository:
    """Repository for site-related database operations"""

    def __init__(self):
        """Initialize the repository"""
        self.db_connection = get_database_connection()

    def get_all_sites(self) -> List[Dict[str, Any]]:
        """
        Retrieve all solar sites from the database.

        Returns:
            List of site dictionaries containing site_id and site_name

        Raises:
            SQLAlchemyError: If database operation fails
        """
        try:
            query = self._build_sites_query()

            with self.db_connection.get_engine().connect() as connection:
                result = connection.execute(text(query))

                # Convert result to list of dictionaries
                columns = result.keys()
                rows = result.fetchall()

                sites = []
                for row in rows:
                    site_dict = dict(zip(columns, row))
                    sites.append(site_dict)

                logger.info(f"Retrieved {len(sites)} sites from database")
                return sites

        except SQLAlchemyError as e:
            logger.error(f"Database error retrieving sites: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error retrieving sites: {str(e)}")
            raise

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
        Build SQL query to retrieve all sites.

        Returns:
            SQL query string
        """
        return """
            SELECT 
                site_id,
                site_name,
                location,
                capacity_kw,
                installation_date,
                status
            FROM sites
            WHERE status = 'active'
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
                site_id,
                site_name,
                location,
                capacity_kw,
                installation_date,
                status
            FROM sites
            WHERE site_id = :site_id
        """
