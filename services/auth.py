from fastapi import status
from fastapi.responses import RedirectResponse
from passlib.context import CryptContext

from utils.config import SETTINGS
from utils.signed_token import serializer

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
    """
    Service for handling authentication logic, including user credential validation,
    password verification, and authentication cookie management.

    Responsibilities:
        - Validate user credentials against configured username and hashed password.
        - Generate and set signed authentication cookies for session management.
        - Provide error responses for failed authentication attempts.

    Methods:
        _check_password(plain_password): Verify a plain password against the stored hash.
        _check_username(username): Check if the username matches the configured value.
        check_user_credentials(username, password): Validate both username and password.
        create_auth_cookie(username): Create and set a signed authentication cookie.
        create_error_response(error_message): Redirect to login with an error message.
    """
    def _check_password(self, plain_password: str) -> bool:
        """Check if the provided plain password matches the stored hashed password.

        Args:
            plain_password (str): The plain text password to check.

        Returns:
            bool: True if the password is valid, False otherwise.

        """
        return pwd_context.verify(plain_password, SETTINGS.app_password)

    def _check_username(self, username: str) -> bool:
        """Check if the provided username matches the configured application username.

        Args:
            username (str): The username to check.
        Returns:
            bool: True if the username matches, False otherwise.

        """
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
            key=SETTINGS.cookie_name,
            value=signed_token,
            httponly=True,
            secure=(SETTINGS.env == "prod"),
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
