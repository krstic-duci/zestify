from fastapi import Depends, FastAPI, HTTPException, Form, Request, status
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from slowapi import Limiter
from slowapi.util import get_remote_address

from dependency.get_current_user import get_current_user
from utils.constants import LOGIN_RATE_LIMIT, GENERAL_RATE_LIMIT
from services.ingredients import IngredientService
from services.auth import AuthService


app = FastAPI()
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
ingredient_service = IngredientService()
auth_service = AuthService()

templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

# TODO: gotta fix global error states for every template


@app.get("/login", response_class=HTMLResponse)
async def show_login_form(request: Request):
    response = templates.TemplateResponse("login.html.jinja", {"request": request})
    return response


@app.post("/login", response_class=HTMLResponse)
@limiter.limit(LOGIN_RATE_LIMIT)
async def login(
    request: Request,
    username: str = Form(..., min_length=2, max_length=50),
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
    """
    if not auth_service.check_user_credentials(username, password):
        return auth_service.create_error_response("Invalid username or password")

    return auth_service.create_auth_cookie(username)


@app.get("/", response_class=HTMLResponse)
@limiter.limit(GENERAL_RATE_LIMIT)
async def read_index(request: Request, _: str = Depends(get_current_user)):
    response = templates.TemplateResponse("index.html.jinja", {"request": request})
    return response


# TODO: move logic to a service, too much for route handler
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


# TODO: build services logic, too much for route handlers
# @app.get("/weekly", response_class=HTMLResponse)
# @limiter.limit(GENERAL_RATE_LIMIT)
# async def weekly(request: Request, _: str = Depends(get_current_user)):
#     try:
#         # Order by position to maintain user's preferred order
#         weekly_table = (
#             supabase.table("weekly").select("*").order("position", desc=False)
#                     .execute()
#         )
#         links = weekly_table.data

#         # Create meal plan structure directly from database data
#         meal_plan: dict[str, dict[str, list[dict]]] = {}

#         # Collect all days and meals that exist in the database
#         for link in links:
#             if not isinstance(link, dict) or "link" not in link:
#                 continue

#             day = link.get("day_name")
#             meal = link.get("meal_type")

#             if not day or not meal:
#                 continue

#             if day not in meal_plan:
#                 meal_plan[day] = {}

#             if meal not in meal_plan[day]:
#                 meal_plan[day][meal] = []

#             meal_plan[day][meal].append(link)

#         return templates.TemplateResponse(
#             "weekly.html.jinja",
#             {"request": request, "data": meal_plan},
#         )
#     except Exception as e:
#         return templates.TemplateResponse(
#             "weekly.html.jinja",
#             {
#                 "request": request,
#                 "data": {},
#                 "error": f"Error loading weekly plan: {str(e)}"
#             },
#             status_code=500
#         )


# @app.post("/update-weekly-positions")
# async def update_weekly_positions(
#     request: Request,
#     _: str = Depends(get_current_user)
# ):
#     try:
#         body = await request.json()
#         updates = body.get("updates", [])

#         for update in updates:
#             item_id = update.get("id")
#             new_position = update.get("position")
#             day = update.get("day")
#             meal = update.get("meal")

#             # Skip placeholder items
#             if not item_id or item_id in ["placeholder", "unknown"]:
#                 continue

#             # Update the position and location in database
#             supabase.table("weekly").update({
#                 "position": new_position,
#                 "day_name": day,
#                 "meal_type": meal
#             }).eq("id", item_id).execute()

#         return {"status": "success"}
#     except Exception as e:
#         return {"status": "error", "message": str(e)}


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


# TODO: add 404 and error pages
