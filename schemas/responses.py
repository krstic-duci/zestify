from typing import Any

from pydantic import BaseModel, Field


class ErrorDetail(BaseModel):
    """Error detail structure."""

    code: str = Field(description="Error code identifier")
    message: str = Field(description="Human-readable error message")
    details: dict[str, Any] | None = Field(
        default=None, description="Additional error context"
    )


class BaseResponse(BaseModel):
    """Base response envelope."""

    status: str = Field(description="Response status: 'success' or 'error'")


class SuccessResponse(BaseResponse):
    """Success response envelope."""

    status: str = Field(default="success", pattern="^success$")
    data: dict[str, Any] = Field(description="Response payload")
    meta: dict[str, Any] | None = Field(default=None, description="Additional metadata")


class ErrorResponse(BaseResponse):
    """Error response envelope."""

    status: str = Field(default="error", pattern="^error$")
    error: ErrorDetail = Field(description="Error details")


# TODO: this needs to be refactored
class IngredientsResponse(SuccessResponse):
    """Response for ingredients processing."""

    data: dict[str, Any] = Field(
        description="Must contain 'ingredients_html' and 'llm_time'",
        examples=[
            {
                "ingredients_html": "<div><h3>Meat/Fish</h3><ul><li>500g chicken</li></ul></div>",
                "llm_time": 1.23,
            }
        ],
    )


class WeeklyPlanResponse(SuccessResponse):
    """Response for weekly meal plan."""

    data: dict[str, dict[str, dict[str, list]]] = Field(
        description="Weekly meal plan organized by day and meal type",
        examples=[
            {
                "Monday": {
                    "Lunch": [{"id": "123", "link": "https://...", "position": 0}],
                    "Dinner": [],
                },
                "Tuesday": {"Lunch": [], "Dinner": []},
            }
        ],
    )


class SwapMealsResponse(SuccessResponse):
    """Response for meal swap operation."""

    data: dict[str, Any] = Field(
        default_factory=dict,
        description="Empty data object for successful swap",
        examples=[{}],
    )


class MoveMealsResponse(SuccessResponse):
    """Response for meal move operation."""

    data: dict[str, Any] = Field(
        default_factory=dict,
        description="Empty data object for successful move",
        examples=[{}],
    )
