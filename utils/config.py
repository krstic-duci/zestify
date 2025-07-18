import os
from dotenv import load_dotenv
from pydantic_settings import BaseSettings

from .constants import ALLOWED_TAGS, COOKIE_MAX_AGE

load_dotenv()


def get_required_env(key: str) -> str:
    """
    Retrieves the value of a required environment variable.

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


class Settings(BaseSettings):
    gemini_api_key: str = GEMINI_API_KEY
    app_username: str = USERNAME
    app_password: str = HASHED_PASS
    auth_token_key: str = AUTH_TOKEN_KEY
    max_age: int = COOKIE_MAX_AGE
    allowed_tags: list[str] = ALLOWED_TAGS


settings = Settings()
