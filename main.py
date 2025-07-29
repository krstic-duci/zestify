from fastapi import Depends, FastAPI, Form, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from dependency.get_current_user import get_current_user
from dependency.limiter import general_rate_limit, login_rate_limit
from services.auth import AuthService
from services.ingredients import IngredientService
from services.weekly import WeeklyService
from utils.error_handlers import (
    general_exception_handler,
    internal_server_error_handler,
    not_found_handler,
    too_many_requests_handler,
    unauthorized_handler,
    validation_error_handler,
)

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")

auth_service = AuthService()
ingredient_service = IngredientService()
weekly_service = WeeklyService()


@app.get("/login", response_class=HTMLResponse)
async def get_login(request: Request):
    """Render the login page.

    This endpoint serves the login page of the application.

    Args:
        request (Request): The HTTP request object.

    Returns:
        HTMLResponse: A rendered HTML template for the login page.

    """
    response = templates.TemplateResponse("login.html.jinja", {"request": request})
    return response


@app.post(
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

    Returns:
        HTMLResponse: A rendered HTML template for the login page with an error message
                      if authentication fails, or a redirect response to the index page
                      if authentication succeeds.

    """
    if not auth_service.check_user_credentials(username, password):
        return auth_service.create_error_response("Invalid username or password")

    return auth_service.create_auth_cookie(username)


@app.get("/", response_class=HTMLResponse, dependencies=[Depends(general_rate_limit)])
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
    response = templates.TemplateResponse("index.html.jinja", {"request": request})
    return response


@app.post(
    "/ingredients",
    response_class=HTMLResponse,
    dependencies=[Depends(general_rate_limit)],
)
async def ingredients(
    request: Request,
    recipes_text: str = Form(..., min_length=10),
    _: str = Depends(get_current_user),
    have_at_home: str | None = Form(None),
):
    """Handle the processing of recipes text input and generate categorized ingredients.

    This endpoint accepts a block of text containing recipes, processes it using the
    IngredientService, and returns a categorized list of ingredients. If the input
    is invalid or an error occurs during processing, an appropriate error message
    is displayed on the index page.

    Args:
        request (Request): The HTTP request object.
        recipes_text (str): The text input containing recipes, with a minimum length of
        10 characters.
        _: str: The current user, obtained from the dependency injection.
        have_at_home: (str | None): Optional text input for have at home items, which
        can be used to filter out ingredients that are already available in the pantry
        and/or fridge.

    Returns:
        HTMLResponse: A rendered HTML template displaying the categorized ingredients.

    """
    result = await ingredient_service.process_recipes(recipes_text, have_at_home)
    return templates.TemplateResponse(
        "_ingredients_partial.html.jinja",
        {
            "request": request,
            "data": result["processed_data"],
            "llm_time": result["llm_time"],
        },
    )


@app.get(
    "/weekly",
    response_class=HTMLResponse,
    dependencies=[Depends(general_rate_limit)],
)
async def weekly(request: Request, _: str = Depends(get_current_user)):
    """Render the weekly plan page.

    This endpoint retrieves the weekly meal plan and renders it using a Jinja2 template.

    Args:
        request (Request): The HTTP request object.
        _: str: The current user, obtained from the dependency injection.

    Returns:
        HTMLResponse: A rendered HTML template for the weekly meal plan page.

    """
    meal_plan = await weekly_service.get_weekly_meal_plan()
    return templates.TemplateResponse(
        "weekly.html.jinja",
        {"request": request, "data": meal_plan},
    )


@app.post("/swap-meals")
async def swap_meals(request: Request, _: str = Depends(get_current_user)):
    """Swap the positions of two meals in the weekly meal plan.

    This endpoint allows users to reorder their weekly meal plan by swapping
    the positions of two specified meals. The swap is performed by exchanging
    the meal IDs while maintaining all other meal properties.

    Args:
        request (Request): The HTTP request object containing the JSON payload.
        _: str: The current user, obtained from the dependency injection.

    Request Body:
        meal1_id (str): The ID of the first meal to swap.
        meal2_id (str): The ID of the second meal to swap.

    Returns:
        dict: A JSON response containing the operation status.

    """
    body = await request.json()
    meal1_id = body.get("meal1_id")
    meal2_id = body.get("meal2_id")

    return await weekly_service.swap_meal_positions(meal1_id, meal2_id)


@app.get("/logout", response_class=HTMLResponse)
async def logout():
    """Log out the user by clearing the authentication token.

    This endpoint redirects the user to the login page and deletes the
    authentication token cookie to terminate the session.

    Returns:
        RedirectResponse: A redirection to the login page.

    """
    response = RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    response.delete_cookie("auth_token")
    return response


app.exception_handler(status.HTTP_401_UNAUTHORIZED)(unauthorized_handler)
app.exception_handler(status.HTTP_404_NOT_FOUND)(not_found_handler)
app.exception_handler(RequestValidationError)(validation_error_handler)
app.exception_handler(status.HTTP_429_TOO_MANY_REQUESTS)(too_many_requests_handler)
app.exception_handler(status.HTTP_500_INTERNAL_SERVER_ERROR)(
    internal_server_error_handler
)
app.exception_handler(Exception)(general_exception_handler)
