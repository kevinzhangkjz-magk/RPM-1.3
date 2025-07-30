from typing import Optional
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError

from src.core.config import settings

logger = logging.getLogger(__name__)


class DatabaseConnection:
    """Database connection manager for AWS Redshift"""

    def __init__(self):
        self._engine: Optional[Engine] = None

    def get_connection_string(self) -> str:
        """Build Redshift connection string from settings"""
        if not all(
            [
                settings.redshift_host,
                settings.redshift_database,
                settings.redshift_user,
                settings.redshift_password,
            ]
        ):
            raise ValueError("Missing required Redshift connection parameters")

        ssl_mode = "require" if settings.redshift_ssl else "disable"

        return (
            f"redshift+psycopg2://{settings.redshift_user}:{settings.redshift_password}"
            f"@{settings.redshift_host}:{settings.redshift_port}"
            f"/{settings.redshift_database}?sslmode={ssl_mode}"
        )

    def get_engine(self) -> Engine:
        """Get or create database engine"""
        if self._engine is None:
            connection_string = self.get_connection_string()
            self._engine = create_engine(
                connection_string,
                pool_size=5,
                max_overflow=10,
                pool_timeout=30,
                pool_recycle=3600,
                echo=settings.debug,
            )
        return self._engine

    def test_connection(self) -> bool:
        """Test database connectivity"""
        try:
            engine = self.get_engine()
            with engine.connect() as connection:
                result = connection.execute(text("SELECT 1"))
                return result.fetchone()[0] == 1
        except SQLAlchemyError as e:
            logger.error(f"Database connection test failed: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error during connection test: {e}")
            return False

    def close(self):
        """Close database connection"""
        if self._engine:
            self._engine.dispose()
            self._engine = None


# Global database connection instance
db_connection = DatabaseConnection()


def get_database_connection() -> DatabaseConnection:
    """Get database connection instance"""
    return db_connection
