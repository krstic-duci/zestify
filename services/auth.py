from fastapi import status
from fastapi.responses import RedirectResponse
from passlib.context import CryptContext

from utils.config import settings
from utils.signed_token import serializer

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
    def _check_password(self, plain_password: str) -> bool:
        return pwd_context.verify(plain_password, settings.app_password)

    def _check_username(self, username: str) -> bool:
        return username == settings.app_username

    def check_user_credentials(self, username: str, password: str) -> bool:
        return self._check_username(username) and self._check_password(password)

    def create_auth_cookie(self, username: str) -> RedirectResponse:
        """
        Create a signed authentication token and set it as a cookie in the response.

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
            max_age=settings.max_age,
        )
        return response

    def create_error_response(self, error_message: str) -> RedirectResponse:
        """
        Redirect to the login page with an error message in the query string.

        Args:
            error_message: The error message to display.

        Returns:
            RedirectResponse: A response object redirecting to the login page with the
            error.
        """
        return RedirectResponse(
            url=f"/login?error={error_message}",
            status_code=status.HTTP_303_SEE_OTHER,
        )
