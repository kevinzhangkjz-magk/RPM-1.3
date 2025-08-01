from typing import Optional

from pydantic import ConfigDict
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings"""

    model_config = ConfigDict(env_file=".env")

    app_name: str = "RPM Solar Performance API"
    app_version: str = "1.0.0"
    environment: str = "development"
    debug: bool = False

    # Database settings - AWS Redshift
    redshift_host: Optional[str] = 'data-analytics.crmjfkw9o04v.us-east-1.redshift.amazonaws.com'
    redshift_port: int = 5439
    redshift_database: Optional[str] = 'desri_analytics'
    redshift_user: Optional[str] = 'chail'
    redshift_password: Optional[str] = 'U2bqPmM88D2d'
    redshift_ssl: bool = True

    # AWS settings (for serverless deployment)
    aws_region: str = "us-east-1"

    # Basic Authentication configuration
    basic_auth_username: Optional[str] = "testuser"
    basic_auth_password: Optional[str] = "testpass"


settings = Settings()
