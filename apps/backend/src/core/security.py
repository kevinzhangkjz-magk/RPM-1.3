import secrets
from typing import Optional
from fastapi import HTTPException, status, Depends, Request
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from src.core.config import settings


# HTTP Basic Authentication
security = HTTPBasic()


def get_current_user_skip_options(request: Request) -> str:
    """
    Validate HTTP Basic Authentication credentials, but skip for OPTIONS requests.
    
    Args:
        request: The FastAPI request object
        
    Returns:
        Username if authentication is successful, or 'options_user' for OPTIONS requests
        
    Raises:
        HTTPException: If authentication fails (except for OPTIONS requests)
    """
    # Skip authentication for OPTIONS requests (CORS preflight)
    if request.method == "OPTIONS":
        return "options_user"
    
    # For all other requests, require authentication
    credentials = None
    auth_header = request.headers.get("authorization")
    if auth_header and auth_header.startswith("Basic "):
        import base64
        try:
            encoded_credentials = auth_header.split(" ", 1)[1]
            decoded_credentials = base64.b64decode(encoded_credentials).decode("utf-8")
            username, password = decoded_credentials.split(":", 1)
            credentials = HTTPBasicCredentials(username=username, password=password)
        except Exception:
            pass
    
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": "AuthenticationRequired",
                "message": "Authentication credentials are required",
            },
            headers={"WWW-Authenticate": "Basic"},
        )
    
    return get_current_user(credentials)


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
