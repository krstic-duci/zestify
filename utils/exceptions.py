import logging

logger = logging.getLogger(__name__)


class BaseError(Exception):
    """Base exception for all application errors."""

    def __init__(
        self,
        message: str,
        operation: str = "",
        original_error: str = "",
        context: dict | None = None,
    ):
        super().__init__(message)
        self.message = message
        self.operation = operation
        self.original_error = original_error
        self.context = context or {}


class ServiceError(BaseError):
    """Exception for service layer errors."""

    pass


class RepositoryError(BaseError):
    """Exception for repository layer errors."""

    pass


class ValidationError(BaseError):
    """Exception for validation errors."""

    pass


def handle_repository_error(
    exc: Exception, operation: str, context: dict | None = None
) -> RepositoryError:
    """
    Standardized error handling for repository operations.

    Args:
        exc: The original exception
        operation: Description of the operation that failed
        context: Optional context dictionary with relevant details

    Returns:
        RepositoryError: Standardized repository error
    """
    error_msg = f"Repository operation failed: {operation}"
    logger.error(f"{error_msg} - {exc}", exc_info=True)

    return RepositoryError(
        message=error_msg, operation=operation, original_error=str(exc), context=context
    )


def handle_service_error(
    exc: Exception, operation: str, context: dict | None = None
) -> ServiceError:
    """
    Standardized error handling for service operations.

    Args:
        exc: The original exception
        operation: Description of the operation that failed
        context: Optional context dictionary with relevant details

    Returns:
        ServiceError: Standardized service error
    """
    error_msg = f"Service operation failed: {operation}"
    logger.error(f"{error_msg} - {exc}", exc_info=True)

    return ServiceError(
        message=error_msg, operation=operation, original_error=str(exc), context=context
    )


def log_and_reraise(exc: Exception, operation: str, context: dict | None = None):
    """
    Log an exception and re-raise it without modification.
    Useful for adding logging to existing exception flows.

    Args:
        exc: The exception to log and re-raise
        operation: Description of the operation that failed
        context: Optional context dictionary with relevant details
    """
    logger.error(f"Operation failed: {operation} - {exc}", exc_info=True)
    if context:
        logger.error(f"Context: {context}")
    raise exc
