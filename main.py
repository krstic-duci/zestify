from fastapi import Depends, FastAPI, HTTPException, Form, Request, status
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from passlib.context import CryptContext

from slowapi import Limiter
from slowapi.util import get_remote_address

from dependency.get_current_user import get_current_user
from utils.config import settings
from utils.constants import LOGIN_RATE_LIMIT, GENERAL_RATE_LIMIT
from services.ingredients import IngredientService
from utils.signed_token import serializer


app = FastAPI()
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
ingredient_service = IngredientService()

templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/login", response_class=HTMLResponse)
async def show_login_form(request: Request):
    response = templates.TemplateResponse("login.html.jinja", {"request": request})
    return response


@app.post("/login", response_class=HTMLResponse)
@limiter.limit(LOGIN_RATE_LIMIT)
async def login(
    request: Request,
    username: str = Form(..., min_length=3, max_length=50),
    password: str = Form(
        ...,
        min_length=8,
        max_length=128,
        description="Password must contain at least one uppercase letter, one lowercase"
        " letter, one digit, and one special character (@$!%*?&).",
    ),
):
    """
    Authenticate the user and establish a session.

    This endpoint verifies the provided username and password against the
    application's stored credentials. If the credentials are valid, a signed
    authentication token is generated and set as a cookie in the response.
    Otherwise, the user is redirected back to the login page with an error message.

    Args:
        request (Request): The HTTP request object.
        username (str): The username provided by the user, with a minimum length of 3
                        and a maximum length of 50 characters.
        password (str): The password provided by the user, with a minimum length of 8
                        and a maximum length of 128 characters.

    Returns:
        HTMLResponse: A redirect to the home page with a signed authentication token
                      set as a cookie if authentication is successful. Otherwise,
                      renders the login page with an error message.
    """
    if (
        not pwd_context.verify(password, settings.app_password)
        or username != settings.app_username
    ):
        # Authentication failed, return to login page with error message
        return templates.TemplateResponse(
            "login.html.jinja",
            {
                "request": request,
                "error": "Invalid username or password",
            },
        )

    # Authentication successful, redirect with cookie
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


@app.get("/", response_class=HTMLResponse)
@limiter.limit(GENERAL_RATE_LIMIT)
async def read_index(request: Request, _: str = Depends(get_current_user)):
    response = templates.TemplateResponse("index.html.jinja", {"request": request})
    return response


@app.post("/results", response_class=HTMLResponse)
@limiter.limit(GENERAL_RATE_LIMIT)
async def results(
    request: Request,
    recipes_text: str = Form(..., min_length=10),
    _: str = Depends(get_current_user),
    have_at_home: str | None = Form(None),
):
    """
    Handle the processing of recipes text input and generate categorized ingredients.

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
        HTMLResponse: A rendered HTML template displaying the categorized ingredients
        or an error message if the input is invalid or processing fails.
    """
    try:
        if not recipes_text.strip():
            return templates.TemplateResponse(
                "index.html.jinja",
                {
                    "request": request,
                    "error": "Please provide some recipes text.",
                },
            )
        print(have_at_home)
        processed_data = ingredient_service.process_recipes(recipes_text, have_at_home)

        return templates.TemplateResponse(
            "results.html.jinja",
            {"request": request, "data": processed_data},
        )
    except Exception as e:
        return templates.TemplateResponse(
            "index.html.jinja",
            {
                "request": request,
                "error": f"Error processing request: {str(e)}",
            },
        )


@app.get("/logout", response_class=HTMLResponse)
async def logout():
    response = RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    response.delete_cookie("auth_token")
    return response


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    if exc.status_code == status.HTTP_401_UNAUTHORIZED:
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    elif exc.status_code == status.HTTP_429_TOO_MANY_REQUESTS:
        return templates.TemplateResponse(
            "login.html.jinja",
            {"request": request, "error": "Too many requests. Please try again later."},
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        )
    raise exc
