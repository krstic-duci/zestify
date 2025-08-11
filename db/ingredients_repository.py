import logging

from db.conn import supabase
from utils.constants import Operations, Tables, WeeklyColumns
from utils.exceptions import RepositoryError, handle_repository_error
from utils.validation import (
    ValidationError,
    validate_position,
    validate_url,
)

logger = logging.getLogger(__name__)


def _validate_url(url: str, field_name: str) -> str:
    """Validate and sanitize URLs for database insertion."""
    try:
        return validate_url(url, field_name)
    except ValidationError as e:
        raise RepositoryError(str(e)) from e


class IngredientsRepository:
    """Repository for all DB operations related to ingredients and weekly meal setup."""

    def delete_all_weekly(self):
        """Delete all weekly meals (for ingredients processing setup)."""
        try:
            return (
                supabase.table(Tables.WEEKLY)
                .delete()
                .gt(WeeklyColumns.POSITION, Operations.GT_NEGATIVE_ONE)
                .execute()
            )
        except Exception as exc:
            raise handle_repository_error(
                exc, "delete_all_weekly_for_ingredients"
            ) from exc

    def insert_weekly_meal(self, url, position, day_name, meal_type):
        """Insert a weekly meal during ingredients processing."""
        try:
            url = _validate_url(url, "url") if url else None
            if position is not None:
                position = validate_position(position)

            logger.info(f"Inserting weekly meal at position {position}")
            return (
                supabase.table(Tables.WEEKLY)
                .insert(
                    {
                        WeeklyColumns.LINK: url,
                        WeeklyColumns.POSITION: position,
                        WeeklyColumns.DAY_NAME: day_name,
                        WeeklyColumns.MEAL_TYPE: meal_type,
                    }
                )
                .execute()
            )
        except ValidationError as e:
            raise RepositoryError(str(e)) from e
        except Exception as exc:
            raise handle_repository_error(
                exc,
                f"insert_weekly_meal_at_position_{position}",
                {"position": position},
            ) from exc
