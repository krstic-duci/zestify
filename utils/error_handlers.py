from fastapi import HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import RedirectResponse

from utils.templates import templates


class WeeklyServiceError(Exception):
    """Base exception for WeeklyService operations."""

    def __init__(self, message: str, status_code: int = 500):
        super().__init__(message)
        self.message = message
        self.status_code = status_code

class RecipeProcessingError(Exception):
    """Custom exception for recipe processing errors."""

    def __init__(self, message: str, original_error: Exception | None = None):
        super().__init__(message)
        self.original_error = original_error

async def unauthorized_handler(request: Request, exc: HTTPException):
    """Handle 401 Unauthorized errors."""
    return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)


async def not_found_handler(request: Request, exc: HTTPException):
    """Handle 404 Not Found errors."""
    path = request.url.path
    return templates.TemplateResponse(
        "404.html.jinja",
        {
            "request": request,
            "error": f"The page '{path}' could not be found.",
            "path": path,
        },
        status_code=status.HTTP_404_NOT_FOUND,
    )


async def validation_error_handler(request: Request, exc: RequestValidationError):
    """Handle 422 Validation errors."""
    return templates.TemplateResponse(
        "error.html.jinja",
        {
            "request": request,
            "error": "Invalid input. Please check your data and try again.",
        },
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
    )


async def too_many_requests_handler(request: Request, exc: HTTPException):
    """Handle 429 Rate Limit errors."""
    return templates.TemplateResponse(
        "error.html.jinja",
        {"request": request, "error": "Too many requests. Please try again later."},
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
    )


async def internal_server_error_handler(request: Request, exc: Exception):
    """Handle 500 Internal Server errors."""
    return templates.TemplateResponse(
        "error.html.jinja",
        {
            "request": request,
            "error": "An unexpected error occurred. Please try again later.",
        },
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )


async def general_exception_handler(request: Request, exc: Exception):
    """Handle all unhandled exceptions."""
    print(f"Unhandled exception: {exc}")
    return templates.TemplateResponse(
        "error.html.jinja",
        {
            "request": request,
            "error": "An unexpected error occurred. Please try again later.",
        },
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )
