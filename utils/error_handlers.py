import logging

from fastapi import HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, RedirectResponse

from utils.error_codes import ErrorCode
from utils.templates import templates

logger = logging.getLogger(__name__)


class WeeklyServiceError(Exception):
    """Base exception for WeeklyService operations."""

    def __init__(
        self, message: str, status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    ):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class RecipeProcessingError(Exception):
    """Custom exception for recipe processing errors."""

    def __init__(self, message: str, original_error: Exception | None = None):
        super().__init__(message)
        self.original_error = original_error


async def unauthorized_handler(request: Request, exc: HTTPException):
    accept = request.headers.get("accept", "")
    if "application/json" in accept:
        return JSONResponse(
            {
                "status": "error",
                "error": {
                    "code": ErrorCode.Api.UNAUTHORIZED,
                    "message": "Not authenticated.",
                },
            },
            status_code=status.HTTP_401_UNAUTHORIZED,
        )
    return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)


async def not_found_handler(request: Request, exc: HTTPException):
    accept = request.headers.get("accept", "")
    print(accept)
    if "application/json" in accept:
        return JSONResponse(
            {
                "status": "error",
                "error": {
                    "code": ErrorCode.Api.NOT_FOUND,
                    "message": f"The page '{request.url.path}' could not be found.",
                },
            },
            status_code=status.HTTP_404_NOT_FOUND,
        )
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
    accept = request.headers.get("accept", "")
    if "application/json" in accept:
        return JSONResponse(
            {
                "status": "error",
                "error": {
                    "code": ErrorCode.Api.VALIDATION_ERROR,
                    "message": "Invalid input. Please check your data and try again.",
                },
            },
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )
    return templates.TemplateResponse(
        "error.html.jinja",
        {
            "request": request,
            "error": "Invalid input. Please check your data and try again.",
        },
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
    )


async def too_many_requests_handler(request: Request, exc: HTTPException):
    accept = request.headers.get("accept", "")
    if "application/json" in accept:
        return JSONResponse(
            {
                "status": "error",
                "error": {
                    "code": ErrorCode.Api.TOO_MANY_REQUESTS,
                    "message": "Too many requests. Please try again later.",
                },
            },
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        )
    return templates.TemplateResponse(
        "error.html.jinja",
        {"request": request, "error": "Too many requests. Please try again later."},
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
    )


async def internal_server_error_handler(request: Request, exc: Exception):
    accept = request.headers.get("accept", "")
    if "application/json" in accept:
        return JSONResponse(
            {
                "status": "error",
                "error": {
                    "code": ErrorCode.Api.INTERNAL_ERROR,
                    "message": "An unexpected error occurred. Please try again later.",
                },
            },
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
    return templates.TemplateResponse(
        "error.html.jinja",
        {
            "request": request,
            "error": "An unexpected error occurred. Please try again later.",
        },
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )


async def general_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled exception occurred: %s", exc)
    accept = request.headers.get("accept", "")
    if "application/json" in accept:
        return JSONResponse(
            {
                "status": "error",
                "error": {
                    "code": ErrorCode.Api.INTERNAL_ERROR,
                    "message": "An unexpected error occurred. Please try again later.",
                },
            },
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
    return templates.TemplateResponse(
        "error.html.jinja",
        {
            "request": request,
            "error": "An unexpected error occurred. Please try again later.",
        },
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )


async def http_exception_dispatcher(request: Request, exc: HTTPException):
    """Dispatch HTTP exceptions to the appropriate handler."""
    if exc.status_code == status.HTTP_401_UNAUTHORIZED:
        return await unauthorized_handler(request, exc)
    elif exc.status_code == status.HTTP_404_NOT_FOUND:
        return await not_found_handler(request, exc)
    elif exc.status_code == status.HTTP_429_TOO_MANY_REQUESTS:
        return await too_many_requests_handler(request, exc)
    elif exc.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR:
        return await internal_server_error_handler(request, exc)
    else:
        return await internal_server_error_handler(request, exc)
