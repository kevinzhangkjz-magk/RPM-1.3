from typing import Optional

from pydantic import ConfigDict
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings"""

    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    app_name: str = "RPM Solar Performance API"
    app_version: str = "1.0.0"
    environment: str = "development"
    debug: bool = False

    # Database settings - AWS Redshift
    redshift_host: Optional[str] = None
    redshift_port: int = 5439
    redshift_database: Optional[str] = None
    redshift_user: Optional[str] = None
    redshift_password: Optional[str] = None
    redshift_ssl: bool = True

    # AWS settings (for serverless deployment)
    aws_region: str = "us-east-1"

    # Basic Authentication configuration
    basic_auth_username: Optional[str] = None
    basic_auth_password: Optional[str] = None

    # AI Service configuration
    openai_api_key: Optional[str] = None
    ai_model: str = "gpt-4o-mini"
    ai_max_tokens: int = 1000


settings = Settings()
