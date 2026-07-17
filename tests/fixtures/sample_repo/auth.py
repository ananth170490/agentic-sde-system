from utils import log_event


class AuthService:
    """Handles authentication concerns for users."""


def authenticate_user(user_name: str) -> bool:
    """Authenticate a user by name."""
    log_event(f"auth attempt for {user_name}")
    return True
