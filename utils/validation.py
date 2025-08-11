from pydantic import HttpUrl
from pydantic import ValidationError as PydanticValidationError


class ValidationError(Exception):
    """Exception raised by validation functions."""

    def __init__(self, message: str, field_name: str = "", original_error: str = ""):
        super().__init__(message)
        self.field_name = field_name
        self.original_error = original_error


def validate_url(url: str, field_name: str) -> str:
    """Validate URL using Pydantic HttpUrl validator.

    Args:
        url: The URL string to validate
        field_name: Name of the field for error messages

    Returns:
        str: The validated URL

    Raises:
        ValidationError: If URL is invalid
    """
    if not url or not isinstance(url, str):
        raise ValidationError(
            f"Invalid {field_name}: must be non-empty string", field_name
        )

    try:
        validated_url = HttpUrl(url.strip())
        return str(validated_url)
    except PydanticValidationError as e:
        raise ValidationError(
            f"Invalid {field_name}: {e.errors()[0]['msg']}", field_name
        ) from e


def validate_position(position: int, field_name: str = "position") -> int:
    """Validate meal position to prevent injection via integer fields.

    Args:
        position: The position integer to validate
        field_name: Name of the field for error messages

    Returns:
        int: The validated position

    Raises:
        ValidationError: If position is invalid
    """
    if not isinstance(position, int) or position < 0 or position > 13:
        raise ValidationError(
            f"Invalid {field_name}: {position}. Must be integer between 0 and 13.",
            field_name,
        )
    return position
