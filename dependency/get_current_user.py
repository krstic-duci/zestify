from fastapi import HTTPException, Request, status
from itsdangerous import BadSignature, SignatureExpired

from utils.config import SETTINGS
from utils.signed_token import serializer


def get_current_user(request: Request) -> str:
    """Retrieve the current authenticated user from the request.

    This function acts as a FastAPI dependency to extract and verify the
    authentication token from the request's cookies. It uses a signed token
    to ensure the integrity and authenticity of the data.

    Args:
        request (Request): The incoming HTTP request object.

    Returns:
        str: The username of the authenticated user.

    Raises:
        HTTPException: If the authentication token is missing, invalid, or expired.

    """
    auth_token = request.cookies.get("auth_token")
    if not auth_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    try:
        # Verify the signed token
        token_data = serializer.loads(auth_token, max_age=SETTINGS.max_age)
        return token_data["username"]
    except (BadSignature, SignatureExpired) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        ) from exc
