import os

from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv()


def get_required_env(key: str) -> str:
    """Retrieve the value of a required environment variable.

    This function fetches the value of the specified environment variable
    and raises an error if the variable is not set.

    Args:
        key (str): The name of the environment variable to retrieve.

    Returns:
        str: The value of the environment variable.

    Raises:
        ValueError: If the environment variable is not set.

    """
    value = os.getenv(key)
    if not value:
        raise ValueError(f"{key} environment variable is required and must be set.")
    return value


GEMINI_API_KEY: str = get_required_env("GEMINI_API_KEY")
USERNAME: str = get_required_env("APP_USERNAME")
HASHED_PASS: str = get_required_env("APP_PASSWORD")
AUTH_TOKEN_KEY: str = get_required_env("AUTH_TOKEN_KEY")
SUPABASE_URL: str = get_required_env("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY: str = get_required_env("SUPABASE_SERVICE_ROLE_KEY")


class Settings(BaseSettings):
    """Application settings loaded from environment variables.

    Attributes:
        gemini_api_key (str): API key for Gemini service.
        app_username (str): Username for the application.
        app_password (str): Hashed password for the application.
        auth_token_key (str): Key used for authentication tokens.
        cookie_name (str): Name of the authentication cookie.
        max_age (int): Maximum age for cookies.
        supabase_url (str): URL for the Supabase instance.
        supabase_service_role_key (str): Service role key for Supabase.

    """

    gemini_api_key: str = GEMINI_API_KEY
    app_username: str = USERNAME
    app_password: str = HASHED_PASS
    auth_token_key: str = AUTH_TOKEN_KEY
    cookie_name: str = "auth_token"
    max_age: int = 86400  # 24 hours in seconds
    env: str = "dev"
    supabase_url: str = SUPABASE_URL
    supabase_service_role_key: str = SUPABASE_SERVICE_ROLE_KEY


SETTINGS = Settings()
