from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import JSONResponse

from dependency.get_current_user import get_current_user
from dependency.ingredients import get_ingredient_service
from dependency.limiter import general_rate_limit
from dependency.weekly import get_weekly_service
from schemas.ingredients import IngredientsRequest
from schemas.responses import (
    ErrorResponse,
    IngredientsResponse,
    MoveMealsResponse,
    SwapMealsResponse,
)
from schemas.weekly import MoveMealRequest, SwapMealsRequest
from services.ingredients import IngredientService
from services.weekly import WeeklyService
from utils.error_codes import ErrorCode
from utils.templates import render_template_to_string

router = APIRouter()


# TODO: no business logic should be here. also why am I returning HTML as string?
# It reeks of wrong, I probably want JSON DTO as below and with JS to build the DOM?!?
# {
#   "status": "success",
#   "data": {
#     "ingredients": [
#       {"category": "Meat/Fish", "items": ["900g kalkonfärs", "300g fläskkotlett"]},
#       {"category": "Veggies", "items": ["400g potatis", "300g vitkål", ...]},
#       ...
#     ],
#     "llm_time": 2.72
#   }
@router.post(
    "/ingredients",
    response_class=JSONResponse,
    dependencies=[Depends(general_rate_limit)],
    responses={
        status.HTTP_200_OK: {
            "model": IngredientsResponse,
            "description": "Successfully processed ingredients",
        },
        status.HTTP_422_UNPROCESSABLE_ENTITY: {
            "model": ErrorResponse,
            "description": "Validation error",
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "model": ErrorResponse,
            "description": "Processing error",
        },
    },
)
async def ingredients(
    _request: Request,
    ingredients_request: IngredientsRequest,
    _: str = Depends(get_current_user),
    ingredient_service: IngredientService = Depends(get_ingredient_service),
):
    try:
        result, status_code = await ingredient_service.handle_ingredients_request(
            ingredients_request
        )
        if result.get("status") == "success" and "ingredients_content" in result.get(
            "data", {}
        ):
            data = result["data"]
            rendered_html = render_template_to_string(
                "_ingredients_partial.html.jinja",
                {"data": data["ingredients_content"], "llm_time": data["llm_time"]},
            )
            result["data"]["ingredients_html"] = rendered_html
            del result["data"]["ingredients_content"]
        return JSONResponse(result, status_code=status_code)
    except Exception as exc:
        return JSONResponse(
            {
                "status": "error",
                "error": {
                    "code": ErrorCode.Api.INTERNAL_ERROR,
                    "message": str(exc),
                },
            },
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@router.post(
    "/swap-meals",
    response_class=JSONResponse,
    responses={
        status.HTTP_200_OK: {
            "model": SwapMealsResponse,
            "description": "Successfully swapped meals",
        },
        status.HTTP_422_UNPROCESSABLE_ENTITY: {
            "model": ErrorResponse,
            "description": "Validation error",
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "model": ErrorResponse,
            "description": "Swap operation error",
        },
    },
)
async def swap_meals(
    request: SwapMealsRequest,
    _: str = Depends(get_current_user),
    weekly_service: WeeklyService = Depends(get_weekly_service),
):
    """
    Swap the positions of two meals in the weekly plan.

    This endpoint handles the drag-and-drop functionality by delegating
    to the WeeklyService and returning the service response unchanged.
    All business logic (validation, DB operations, error handling)
    is handled by the service layer.

    Args:
        request (SwapMealsRequest): The request body containing meal IDs.
        _ (str): The current authenticated user.
        weekly_service: The WeeklyService instance.

    Returns:
        JSONResponse: A JSON response indicating the status of the swap.
    """
    try:
        result, status_code = await weekly_service.handle_swap_meals_request(request)
        return JSONResponse(result, status_code=status_code)
    except Exception as exc:
        return JSONResponse(
            {
                "status": "error",
                "error": {
                    "code": ErrorCode.Api.INTERNAL_ERROR,
                    "message": str(exc),
                },
            },
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@router.post(
    "/move-meal",
    response_class=JSONResponse,
    responses={
        status.HTTP_200_OK: {
            "model": MoveMealsResponse,
            "description": "Successfully moved meal",
        },
        status.HTTP_422_UNPROCESSABLE_ENTITY: {
            "model": ErrorResponse,
            "description": "Validation error",
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "model": ErrorResponse,
            "description": "Move operation error",
        },
    },
)
async def move_meal(
    request: MoveMealRequest,
    _: str = Depends(get_current_user),
    weekly_service: WeeklyService = Depends(get_weekly_service),
):
    """
    Move a meal to a specific position in the weekly plan.

    This endpoint handles moving a meal to an empty position or specific slot.
    Used when dragging to empty containers where no swap is needed.

    Args:
        request (MoveMealRequest): The request body containing meal ID and target position.
        _ (str): The current authenticated user.
        weekly_service: The WeeklyService instance.

    Returns:
        JSONResponse: A JSON response indicating the status of the move.
    """
    try:
        result, status_code = await weekly_service.handle_move_meal_request(request)
        return JSONResponse(result, status_code=status_code)
    except Exception as exc:
        return JSONResponse(
            {
                "status": "error",
                "error": {
                    "code": ErrorCode.Api.INTERNAL_ERROR,
                    "message": str(exc),
                },
            },
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@router.get("/healthz", response_class=JSONResponse)
async def health_check():
    """Health check endpoint."""
    return {"status": "ok"}
