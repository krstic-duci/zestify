"""Position mapping utilities for weekly meal planning.

This module provides shared position mapping logic that can be used across
different services without creating dependencies between them.
"""

# Position mapping for 14 individual meal slots (0-13)
# Monday=0-1, Tuesday=2-3, Wednesday=4-5, Thursday=6-7,
# Friday=8-9, Saturday=10-11, Sunday=12-13
POSITION_MAP = {
    0: ("Monday", "Lunch"),
    1: ("Monday", "Dinner"),
    2: ("Tuesday", "Lunch"),
    3: ("Tuesday", "Dinner"),
    4: ("Wednesday", "Lunch"),
    5: ("Wednesday", "Dinner"),
    6: ("Thursday", "Lunch"),
    7: ("Thursday", "Dinner"),
    8: ("Friday", "Lunch"),
    9: ("Friday", "Dinner"),
    10: ("Saturday", "Lunch"),
    11: ("Saturday", "Dinner"),
    12: ("Sunday", "Lunch"),
    13: ("Sunday", "Dinner"),
}


def get_day_and_meal(position: int) -> tuple[str, str]:
    """Get day and meal type for a given position.

    Args:
        position (int): Position index (0-13)

    Returns:
        tuple[str, str]: (day_name, meal_type)

    Raises:
        ValueError: If position is out of valid range
    """
    if position not in POSITION_MAP:
        raise ValueError(f"Invalid position {position}. Must be 0-13.")

    return POSITION_MAP[position]


def normalize_position(position: int) -> int:
    """Normalize position to valid range (0-13) by wrapping.

    Args:
        position (int): Any position index

    Returns:
        int: Normalized position (0-13)
    """
    return position % len(POSITION_MAP)
