import logging

from db.conn import supabase
from utils.constants import POSITION_MAP, Tables, WeeklyColumns
from utils.exceptions import RepositoryError, handle_repository_error
from utils.validation import (
    ValidationError,
    validate_position,
)

logger = logging.getLogger(__name__)


def _validate_position_helper(position: int) -> int:
    """Validate position values for weekly meal operations."""
    try:
        return validate_position(position)
    except ValidationError as e:
        raise RepositoryError(str(e)) from e


class WeeklyRepository:
    """Repository for all DB operations related to weekly meal planning."""

    def fetch_all(self):
        """Fetch all weekly meals ordered by position."""
        try:
            return (
                supabase.table(Tables.WEEKLY)
                .select("*")
                .order(WeeklyColumns.POSITION, desc=False)
                .execute()
            )
        except Exception as exc:
            raise handle_repository_error(exc, "fetch_all_weekly_meals") from exc

    def fetch_position(self, meal_id: str):
        """Fetch position for a specific meal."""
        try:
            return (
                supabase.table(Tables.WEEKLY)
                .select(WeeklyColumns.POSITION)
                .eq(WeeklyColumns.ID, meal_id)
                .limit(1)
                .execute()
            )
        except Exception as exc:
            raise handle_repository_error(
                exc, "fetch_meal_position", {"meal_id": meal_id}
            ) from exc

    def update_position(self, meal_id: str, position: int):
        """Update position, day_name, and meal_type for a specific meal."""
        try:
            position = _validate_position_helper(position)
            day, meal = POSITION_MAP[position]
            return (
                supabase.table(Tables.WEEKLY)
                .update(
                    {
                        WeeklyColumns.POSITION: position,
                        WeeklyColumns.DAY_NAME: day,
                        WeeklyColumns.MEAL_TYPE: meal,
                    }
                )
                .eq(WeeklyColumns.ID, meal_id)
                .execute()
            )
        except Exception as exc:
            raise handle_repository_error(
                exc, "update_meal_position", {"meal_id": meal_id, "position": position}
            ) from exc
