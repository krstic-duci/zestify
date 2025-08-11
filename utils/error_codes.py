from enum import Enum


class ErrorCode:
    class Api(str, Enum):
        INTERNAL_ERROR = "INTERNAL_ERROR"
        NOT_FOUND = "NOT_FOUND"
        UNAUTHORIZED = "UNAUTHORIZED"
        VALIDATION_ERROR = "VALIDATION_ERROR"
        TOO_MANY_REQUESTS = "TOO_MANY_REQUESTS"
        METHOD_NOT_ALLOWED = "METHOD_NOT_ALLOWED"

    class Weekly(str, Enum):
        DB_ERROR = "WEEKLY_PLAN_DB_ERROR"
        LOAD_ERROR = "WEEKLY_PLAN_ERROR"
        SWAP_ERROR = "SWAP_ERROR"
        MOVE_ERROR = "MOVE_ERROR"

    class Ingredients(str, Enum):
        DB_ERROR = "INGREDIENTS_DB_ERROR"
        PROCESSING_ERROR = "PROCESSING_ERROR"

    class Auth(str, Enum):
        INVALID_CREDENTIALS = "INVALID_CREDENTIALS"
        TOKEN_EXPIRED = "TOKEN_EXPIRED"  # noqa: S105
        TOKEN_INVALID = "TOKEN_INVALID"  # noqa: S105

    class Generic(str, Enum):
        INVALID_INPUT = "INVALID_INPUT"
        RESOURCE_NOT_FOUND = "RESOURCE_NOT_FOUND"
        INTERNAL_SERVER_ERROR = "INTERNAL_SERVER_ERROR"

    class Client(str, Enum):
        NETWORK_ERROR = "NETWORK_ERROR"
        NON_JSON = "NON_JSON"
        SERVER_ERROR = "SERVER_ERROR"
