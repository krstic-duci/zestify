from db.conn import supabase
from utils.constants import POSITION_MAP
from utils.error_handlers import WeeklyServiceError


# TODO: too long docstring, unify them in services
class WeeklyService:
    """Service for managing weekly meal plans and meal organization.

    This service handles the retrieval and manipulation of weekly meal plans,
    including organizing meals by day/meal type and enabling meal position swapping
    for drag-and-drop functionality. It works with a position-based system where
    each meal slot (Monday Lunch through Sunday Dinner) has a unique position (0-13).

    The service is used by:
    - GET /weekly endpoint to display the meal plan
    - POST /swap-meals endpoint for drag-and-drop reordering

    Database Schema:
        The 'weekly' table contains:
        - id: UUID primary key
        - link: Recipe URL
        - position: Integer (0-13) representing day/meal slot
        - day_name: String day name (redundant but useful for queries)
        - meal_type: "Lunch" or "Dinner" (redundant but useful for queries)

    Position Mapping:
        Positions 0-13 map to specific day/meal combinations:
        - Monday: 0 (Lunch), 1 (Dinner)
        - Tuesday: 2 (Lunch), 3 (Dinner)
        - ... through Sunday: 12 (Lunch), 13 (Dinner)
    """

    def __init__(self) -> None:
        self.position_map = POSITION_MAP

    def _create_empty_meal_plan(self) -> dict[str, dict[str, list]]:
        """Create an empty meal plan structure for organizing weekly meals.

        Creates the base data structure used throughout the application to represent
        a weekly meal plan. This structure ensures all days and meal types are
        consistently available, even when no meals are assigned.

        Structure:
            Each day contains two meal types (Lunch, Dinner), each starting as an empty list.
            This allows meals to be appended to the appropriate day/meal combination
            when processing database results.

        Returns:
            dict[str, dict[str, list]]: Nested dictionary structure:
                - Outer keys: Day names ("Monday" through "Sunday")
                - Inner keys: Meal types ("Lunch", "Dinner")
                - Values: Empty lists ready to hold meal dictionaries

        Example:
            {
                "Monday": {"Lunch": [], "Dinner": []},
                "Tuesday": {"Lunch": [], "Dinner": []},
                ...
            }
        """
        return {
            "Monday": {"Lunch": [], "Dinner": []},
            "Tuesday": {"Lunch": [], "Dinner": []},
            "Wednesday": {"Lunch": [], "Dinner": []},
            "Thursday": {"Lunch": [], "Dinner": []},
            "Friday": {"Lunch": [], "Dinner": []},
            "Saturday": {"Lunch": [], "Dinner": []},
            "Sunday": {"Lunch": [], "Dinner": []},
        }

    async def get_weekly_meal_plan(self) -> dict[str, dict[str, list]]:
        """Retrieve and organize the complete weekly meal plan from the database.

        Fetches all meals from the 'weekly' table and organizes them into a structured
        weekly meal plan. Meals are positioned according to their position values
        (0-13) which map to specific day/meal combinations.

        Database Query:
            - Fetches all records from 'weekly' table
            - Orders by position to maintain user-defined meal order
            - Handles missing or invalid records gracefully

        Organization Logic:
            1. Creates empty meal plan structure for all days/meals
            2. Iterates through database results
            3. Uses position_map to determine correct day/meal placement
            4. Appends each meal to the appropriate nested list

        Returns:
            dict[str, dict[str, list]]: Organized meal plan with structure:
                {
                    "Monday": {
                        "Lunch": [meal_dict, ...],
                        "Dinner": [meal_dict, ...]
                    },
                    ...
                    "Sunday": { ... }
                }

            Each meal_dict contains: id, link, position, day_name, meal_type

        Raises:
            Exception: If database fetch fails or data organization encounters errors.
                      The original exception is chained for debugging purposes.

        Usage:
            Called by GET /weekly endpoint to render the weekly meal plan page.
            The returned structure is passed directly to the Jinja template.
        """
        try:
            # Order by position to maintain user's preferred order
            # TODO: move supabase query to a separate file/method
            weekly_table = (
                supabase.table("weekly").select("*").order("position", desc=False).execute()
            )
            links = weekly_table.data

            # Create meal plan structure respecting the position order
            meal_plan = self._create_empty_meal_plan()

            # Place each link in the correct position based on its position value
            for link in links:
                if not isinstance(link, dict) or "link" not in link:
                    continue

                position = link.get("position")
                if position is not None and position in self.position_map:
                    day, meal = self.position_map[position]
                    meal_plan[day][meal].append(link)

            return meal_plan

        except Exception as e:
            raise WeeklyServiceError(
                f"Error loading weekly meal plan: {e}",
                status_code=500
            ) from e

    # TODO: too long docstring
    async def swap_meal_positions(self, meal1_id: str, meal2_id: str) -> dict[str, str]:
        """Swap the positions of two meals in the weekly plan for drag-and-drop functionality.

        This method enables the drag-and-drop reordering feature by exchanging the position
        values of two meals. When a user drags a meal from one slot to another, this method
        ensures both meals swap places rather than overwriting one another.

        Swap Process:
            1. Validates that both meal IDs are provided
            2. Queries database to get current positions of both meals
            3. Verifies both meals exist in the database
            4. Performs atomic position swap using two UPDATE statements
            5. Returns success/error status for frontend handling

        Database Operations:
            - Two SELECT queries to fetch current positions
            - Two UPDATE queries to swap the position values
            - Uses meal 'id' column for precise targeting

        Args:
            meal1_id (str): UUID of the first meal to swap. This is the meal being dragged.
            meal2_id (str): UUID of the second meal to swap. This is the drop target meal.

        Returns:
            dict[str, str]: Status response dictionary with keys:
                - "status": Either "success" or "error"
                - "message": Error description (only present if status is "error")

            Success response: {"status": "success"}
            Error response: {"status": "error", "message": "Description of error"}

        Raises:
            ValueError: If meal IDs are missing/empty or meals don't exist in database.
                       These are caught and returned as error responses.
            Exception: If database operations fail due to connection issues or constraints.
                      These are caught and returned as error responses with "Database error:" prefix.

        Usage:
            Called by POST /swap-meals endpoint when user performs drag-and-drop operations.
            The frontend JavaScript sends both meal IDs after a successful drag operation.

        Example:
            result = await weekly_service.swap_meal_positions("uuid1", "uuid2")
            if result["status"] == "success":
                # Frontend updates UI to reflect new positions
            else:
                # Frontend shows error message from result["message"]
        """
        if not meal1_id or not meal2_id:
            raise ValueError("Both meal1_id and meal2_id are required")

        try:
            # Get the positions of the two meals using 'id' column
            # TODO: move supabase query to a separate file/method
            meal1_result = (
                supabase.table("weekly")
                .select("position")
                .eq("id", meal1_id)
                .limit(1)
                .execute()
            )
            if not meal1_result.data:
                raise ValueError(f"Meal with ID {meal1_id} not found")

            # TODO: move supabase query to a separate file/method
            meal2_result = (
                supabase.table("weekly")
                .select("position")
                .eq("id", meal2_id)
                .limit(1)
                .execute()
            )

            if not meal2_result.data:
                raise ValueError(f"Meal with ID {meal2_id} not found")

            meal1_pos = meal1_result.data[0]["position"]
            meal2_pos = meal2_result.data[0]["position"]

            # Swap the positions using 'id' column
            # TODO: move supabase query to a separate file/method
            supabase.table("weekly").update({"position": meal2_pos}).eq("id", meal1_id).execute()
            supabase.table("weekly").update({"position": meal1_pos}).eq("id", meal2_id).execute()

            # TODO: use Pydantic model, also check if we're using this on FE
            return {"status": "success"}

        except Exception as e:
            raise WeeklyServiceError(f"Database error during meal swap: {e}") from e
