from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException

from routes.api import router as api_router
from routes.pages import router as pages_router
from utils.error_handlers import (
    general_exception_handler,
    http_exception_dispatcher,
    validation_error_handler,
)
from utils.security import SecurityMiddleware

# TODO: Add some sorts of tests for the endpoints, E2E and even JS

app = FastAPI()

app.add_middleware(SecurityMiddleware)

app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(pages_router)
app.include_router(api_router)

# NOTE: not sure why I need two HTTPException handlers but they seem to be for different
# layers
app.exception_handler(HTTPException)(http_exception_dispatcher)
app.exception_handler(StarletteHTTPException)(http_exception_dispatcher)
app.exception_handler(RequestValidationError)(validation_error_handler)
app.exception_handler(Exception)(general_exception_handler)
