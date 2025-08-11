from fastapi import APIRouter, Depends, Form, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse

from dependency.auth import get_auth_service
from dependency.get_current_user import get_current_user
from dependency.limiter import general_rate_limit, login_rate_limit
from dependency.weekly import get_weekly_service
from services.auth import AuthService
from services.weekly import WeeklyService
from utils.config import SETTINGS
from utils.templates import templates

router = APIRouter()


@router.get("/login", response_class=HTMLResponse)
async def get_login(request: Request):
    """Render the login page.

    This endpoint serves the login page of the application.

    Args:
        request (Request): The HTTP request object.

    Returns:
        HTMLResponse: A rendered HTML template for the login page.
    """
    return templates.TemplateResponse("login.html.jinja", {"request": request})


@router.post(
    "/login", response_class=HTMLResponse, dependencies=[Depends(login_rate_limit)]
)
async def login(
    request: Request,
    username: str = Form(..., min_length=2, max_length=50),
    # TODO: Add password validation via Pydantic
    password: str = Form(
        ...,
        min_length=8,
        max_length=128,
        description="Password must contain at least one uppercase letter, one lowercase"
        " letter, one digit, and one special character (@$!%*?&).",
    ),
    auth_service: AuthService = Depends(get_auth_service),
):
    """Authenticate the user and establish a session.

    This endpoint verifies the provided username and password against the
    application's stored credentials. If the credentials are valid, a signed
    authentication token is generated and set as a cookie in the response.
    Otherwise, the user is redirected back to the login page with an error message.

    Args:
        request (Request): The HTTP request object.
        username (str): The username of the user attempting to log in.
        password (str): The password of the user attempting to log in.
        auth_service (AuthService): The service responsible for authentication.

    Returns:
        HTMLResponse: A rendered HTML template for the login page with an error message
                      if authentication fails, or a redirect response to the index page
                      if authentication succeeds.
    """
    if not auth_service.check_user_credentials(username, password):
        return auth_service.create_error_response("Invalid username or password")

    return auth_service.create_auth_cookie(username)


@router.get(
    "/", response_class=HTMLResponse, dependencies=[Depends(general_rate_limit)]
)
async def index(request: Request, _: str = Depends(get_current_user)):
    """Render the index page.

    This endpoint serves the main page of the application. It requires the user
    to be authenticated and applies a general rate limit.

    Args:
        request (Request): The HTTP request object.
        _ (str): The current user, obtained from the dependency injection.

    Returns:
        HTMLResponse: A rendered HTML template for the index page.
    """
    return templates.TemplateResponse("index.html.jinja", {"request": request})


@router.get(
    "/weekly",
    response_class=HTMLResponse,
    dependencies=[Depends(general_rate_limit)],
)
async def weekly(
    request: Request,
    _: str = Depends(get_current_user),
    weekly_service: WeeklyService = Depends(get_weekly_service),
):
    """Render the weekly plan page.

    This endpoint retrieves the weekly meal plan and renders it using a Jinja2 template.

    Args:
        request (Request): The HTTP request object.
        _: str: The current user, obtained from the dependency injection.
        weekly_service (WeeklyService): The service to fetch the weekly meal plan.

    Returns:
        HTMLResponse: A rendered HTML template for the weekly meal plan page.
    """
    meal_plan = await weekly_service.get_weekly_meal_plan()
    return templates.TemplateResponse(
        "weekly.html.jinja",
        # TODO: don't like this song and dance with .get('data')
        {"request": request, "data": meal_plan.get("data", {})},
    )


@router.get("/logout", response_class=HTMLResponse)
async def logout():
    """Log out the user by clearing the authentication token.

    This endpoint redirects the user to the login page and deletes the
    authentication token cookie to terminate the session.

    Returns:
        RedirectResponse: A redirection to the login page.
    """
    response = RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    response.delete_cookie(SETTINGS.cookie_name)
    return response
