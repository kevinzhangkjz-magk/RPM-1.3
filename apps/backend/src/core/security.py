import secrets
from typing import Optional
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from src.core.config import settings


# HTTP Basic Authentication
security = HTTPBasic()


def get_current_user(credentials: HTTPBasicCredentials = Depends(security)) -> str:
    """
    Validate HTTP Basic Authentication credentials.

    Args:
        credentials: HTTP Basic Authentication credentials

    Returns:
        Username if authentication is successful

    Raises:
        HTTPException: If authentication fails
    """
    # Get configured credentials
    correct_username = settings.basic_auth_username
    correct_password = settings.basic_auth_password

    # Validate credentials exist in configuration
    if not correct_username or not correct_password:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "AuthenticationConfigurationError",
                "message": "Authentication is not properly configured",
            },
        )

    # Validate provided credentials
    is_correct_username = secrets.compare_digest(
        credentials.username.encode("utf8"), correct_username.encode("utf8")
    )
    is_correct_password = secrets.compare_digest(
        credentials.password.encode("utf8"), correct_password.encode("utf8")
    )

    if not (is_correct_username and is_correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": "AuthenticationFailed",
                "message": "Invalid username or password",
            },
            headers={"WWW-Authenticate": "Basic"},
        )

    return credentials.username


def get_optional_current_user(
    credentials: Optional[HTTPBasicCredentials] = Depends(security),
) -> Optional[str]:
    """
    Optional authentication dependency that doesn't require authentication.

    Args:
        credentials: Optional HTTP Basic Authentication credentials

    Returns:
        Username if authentication is provided and valid, None otherwise

    Note:
        This is for endpoints that support optional authentication
    """
    if not credentials:
        return None

    try:
        return get_current_user(credentials)
    except HTTPException:
        return None
