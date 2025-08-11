from services.auth import AuthService


def get_auth_service() -> AuthService:
    return AuthService()
