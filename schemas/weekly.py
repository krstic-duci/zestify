from pydantic import BaseModel, ConfigDict, Field


class SwapMealsRequest(BaseModel):
    """Request payload for swapping two meal positions.

    Both IDs are required and trimmed; empty strings are rejected.
    """

    model_config = ConfigDict(str_strip_whitespace=True)

    meal1_id: str = Field(min_length=1, description="Dragged meal id")
    meal2_id: str = Field(min_length=1, description="Drop-target meal id")


class MoveMealRequest(BaseModel):
    """Request payload for moving a meal to a specific position."""

    model_config = ConfigDict(str_strip_whitespace=True)

    meal_id: str = Field(min_length=1, description="Meal ID to move")
    target_position: int = Field(ge=0, le=13, description="Target position (0-13)")
