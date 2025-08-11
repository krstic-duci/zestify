# --- Business Logic Constants ---
# Monday=0-1, Tuesday=2-3, Wednesday=4-5, Thursday=6-7, Friday=8-9, Saturday=10-11, Sunday=12-13
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
MEAL_TYPES = ["Lunch", "Dinner"]


# --- DB Table & Column Names ---
class Tables:
    WEEKLY = "weekly"


class WeeklyColumns:
    ID = "id"
    LINK = "link"
    POSITION = "position"
    DAY_NAME = "day_name"
    MEAL_TYPE = "meal_type"
    CREATED_AT = "created_at"
    UPDATED_AT = "updated_at"


# --- DB Query & Operation Constants ---
class Operations:
    SELECT_ALL = "*"
    ORDER_ASC = False
    ORDER_DESC = True
    GT_NEGATIVE_ONE = -1  # Used for "delete all" operations
