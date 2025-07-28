from fastapi import status
from fastapi.responses import RedirectResponse
from passlib.context import CryptContext

from utils.config import SETTINGS
from utils.signed_token import serializer

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
    """A service class for handling authentication-related operations.

    Methods
    -------
    check_user_credentials(username: str, password: str) -> bool
        Validates the provided username and password against the configured settings.

    create_auth_cookie(username: str) -> RedirectResponse
        Creates a signed authentication token and sets it as a cookie in the response.

    create_error_response(error_message: str) -> RedirectResponse
        Redirects to the login page with an error message in the query string.

    """

    def _check_password(self, plain_password: str) -> bool:
        return pwd_context.verify(plain_password, SETTINGS.app_password)

    def _check_username(self, username: str) -> bool:
        return username == SETTINGS.app_username

    def check_user_credentials(self, username: str, password: str) -> bool:
        """Validate the provided username and password.

        Args:
            username (str): The username to validate.
            password (str): The password to validate.

        Returns:
            bool: True if the credentials are valid, False otherwise.

        """
        return self._check_username(username) and self._check_password(password)

    def create_auth_cookie(self, username: str) -> RedirectResponse:
        """Create a signed authentication token and set it as a cookie in the response.

        Args:
            username (str): The username to include in the token.

        Returns:
            RedirectResponse: A response object with the auth cookie set.

        """
        signed_token = serializer.dumps({"username": username})
        response = RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
        response.set_cookie(
            key="auth_token",
            value=signed_token,
            httponly=True,
            secure=True,
            samesite="strict",
            max_age=SETTINGS.max_age,
        )
        return response

    def create_error_response(self, error_message: str) -> RedirectResponse:
        """Redirect to the login page with an error message in the query string.

        Args:
            error_message (str): The error message to display.

        Returns:
            RedirectResponse: A response object redirecting to the login page with the
            error.

        """
        return RedirectResponse(
            url=f"/login?error={error_message}",
            status_code=status.HTTP_303_SEE_OTHER,
        )
