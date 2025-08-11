import logging

from fastapi import status

from db.weekly_repository import WeeklyRepository
from schemas.weekly import MoveMealRequest, SwapMealsRequest
from utils.constants import MEAL_TYPES, POSITION_MAP
from utils.error_codes import ErrorCode


class WeeklyService:
    """
    Service for weekly meal plan management and organization.

    Responsibilities:
        - Retrieve and organize weekly meal plans.
        - Swap and move meal positions for drag-and-drop functionality.
        - Map meal slots to days and meal types.

    Methods:
        _create_empty_meal_plan(): Create an empty meal plan structure.
        get_weekly_meal_plan(): Fetch and organize all weekly meals.
        swap_meal_positions(meal1_id, meal2_id): Swap two meals' positions.
        handle_swap_meals_request(request): Format swap response for API.
        move_meal_to_position(meal_id, target_position): Move a meal to a specific slot.
        handle_move_meal_request(request): Format move response for API.
    """

    def __init__(self, weekly_repository: WeeklyRepository | None = None) -> None:
        self.position_map = POSITION_MAP
        self.weekly_repository = weekly_repository or WeeklyRepository()

    def _create_empty_meal_plan(self) -> dict[str, dict[str, list]]:
        """
        Create an empty weekly meal plan structure.

        Returns:
            dict[str, dict[str, list]]: Days mapped to meal types with empty lists.
        """
        days_of_week = [
            "Monday",
            "Tuesday",
            "Wednesday",
            "Thursday",
            "Friday",
            "Saturday",
            "Sunday",
        ]
        return {day: {meal: [] for meal in MEAL_TYPES} for day in days_of_week}

    async def get_weekly_meal_plan(self) -> dict:
        """
        Fetch and organize all weekly meals from the database.

        Returns:
            dict: Envelope with status and organized meal plan data or error.
        """
        try:
            meal_plan = self._create_empty_meal_plan()
            weekly_table = self.weekly_repository.fetch_all().data

            # Place each row in the correct position based on its position value
            for row in weekly_table:
                position = row.get("position")
                if position is not None and position in self.position_map:
                    day, meal = self.position_map[position]
                    meal_plan[day][meal].append(row)
            return {"status": "success", "data": meal_plan}

        except Exception as exc:
            logging.exception("Failed to load weekly meal plan: %s", exc)
            return {
                "status": "error",
                "error": {
                    "code": ErrorCode.Weekly.LOAD_ERROR,
                    "message": "Error loading weekly meal plan.",
                    "details": {"error_type": type(exc).__name__},
                },
            }

    async def swap_meal_positions(self, meal1_id: str, meal2_id: str) -> dict:
        """
        Swap the positions of two meals in the weekly plan.

        Args:
            meal1_id (str): ID of the first meal.
            meal2_id (str): ID of the second meal.

        Returns:
            dict: Envelope with status and error if any.
        """
        if not meal1_id or not meal2_id:
            return {
                "status": "error",
                "error": {
                    "code": ErrorCode.Generic.INVALID_INPUT,
                    "message": "Both meal1_id and meal2_id are required",
                },
            }

        try:
            meal1_result = self.weekly_repository.fetch_position(str(meal1_id)).data
            if not meal1_result:
                return {
                    "status": "error",
                    "error": {
                        "code": ErrorCode.Api.NOT_FOUND,
                        "message": f"Meal with ID {meal1_id} not found",
                    },
                }

            meal2_result = self.weekly_repository.fetch_position(str(meal2_id)).data
            if not meal2_result:
                return {
                    "status": "error",
                    "error": {
                        "code": ErrorCode.Api.NOT_FOUND,
                        "message": f"Meal with ID {meal2_id} not found",
                    },
                }

            print("HERERER")
            meal1_pos = meal1_result[0]["position"]
            meal2_pos = meal2_result[0]["position"]

            print(meal1_pos, meal2_pos)

            self.weekly_repository.update_position(str(meal1_id), meal2_pos)
            self.weekly_repository.update_position(str(meal2_id), meal1_pos)

            return {"status": "success", "data": {}}
        except Exception as exc:
            logging.exception(
                "Failed to swap meal positions for %s <-> %s: %s",
                meal1_id,
                meal2_id,
                exc,
            )
            return {
                "status": "error",
                "error": {
                    "code": ErrorCode.Weekly.SWAP_ERROR,
                    "message": "A database error occurred while swapping meals.",
                    "details": {
                        "error_type": type(exc).__name__,
                        "meal1_id": meal1_id,
                        "meal2_id": meal2_id,
                    },
                },
            }

    async def handle_swap_meals_request(
        self, request: SwapMealsRequest
    ) -> tuple[dict, int]:
        """
        Format swap response for /swap-meals API route.

        Args:
            request (SwapMealsRequest): Request body with meal IDs.

        Returns:
            tuple[dict, int]: Envelope with status and HTTP status code.
        """
        result = await self.swap_meal_positions(request.meal1_id, request.meal2_id)

        # TODO: WTH is this?
        if result.get("status") == "error":
            error_code = result.get("error", {}).get("code", "")
            if error_code in (ErrorCode.Generic.INVALID_INPUT, ErrorCode.Api.NOT_FOUND):
                status_code = status.HTTP_400_BAD_REQUEST
            elif error_code in (ErrorCode.Weekly.SWAP_ERROR, ErrorCode.Weekly.DB_ERROR):
                status_code = status.HTTP_503_SERVICE_UNAVAILABLE
            else:
                status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        else:
            status_code = status.HTTP_200_OK

        return result, status_code

    async def move_meal_to_position(self, meal_id: str, target_position: int) -> dict:
        """
        Move a meal to a specific position in the weekly plan.

        Args:
            meal_id (str): ID of the meal to move.
            target_position (int): Target position (0-13).

        Returns:
            dict: Envelope with status and data or error.
        """
        if not meal_id:
            return {
                "status": "error",
                "error": {
                    "code": ErrorCode.Generic.INVALID_INPUT,
                    "message": "meal_id is required",
                },
            }

        if target_position < 0 or target_position > 13:
            return {
                "status": "error",
                "error": {
                    "code": ErrorCode.Generic.INVALID_INPUT,
                    "message": "target_position must be between 0 and 13",
                },
            }

        try:
            meal_result = self.weekly_repository.fetch_position(str(meal_id))
            if not meal_result.data:
                return {
                    "status": "error",
                    "error": {
                        "code": ErrorCode.Api.NOT_FOUND,
                        "message": f"Meal with ID {meal_id} not found",
                    },
                }

            self.weekly_repository.update_position(str(meal_id), target_position)

            return {"status": "success", "data": {"message": "Meal moved successfully"}}
        except Exception as exc:
            logging.exception("Failed to move meal: %s", exc)
            return {
                "status": "error",
                "error": {
                    "code": ErrorCode.Weekly.MOVE_ERROR,
                    "message": f"An error occurred while moving the meal. {exc!s}",
                },
            }

    async def handle_move_meal_request(
        self, request: MoveMealRequest
    ) -> tuple[dict, int]:
        """
        Format move response for /move-meal API route.

        Args:
            request (MoveMealRequest): Request body with meal ID and target position.

        Returns:
            tuple[dict, int]: Envelope with status and HTTP status code.
        """
        result = await self.move_meal_to_position(
            request.meal_id, request.target_position
        )

        # TODO: WTH is this?
        if result.get("status") == "error":
            error_code = result.get("error", {}).get("code", "")
            if error_code in (ErrorCode.Generic.INVALID_INPUT, ErrorCode.Api.NOT_FOUND):
                status_code = status.HTTP_400_BAD_REQUEST
            elif error_code in (ErrorCode.Weekly.MOVE_ERROR, ErrorCode.Weekly.DB_ERROR):
                status_code = status.HTTP_503_SERVICE_UNAVAILABLE
            else:
                status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        else:
            status_code = status.HTTP_200_OK

        return result, status_code
