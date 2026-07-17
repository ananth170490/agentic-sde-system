from auth import AuthService


def get_user(user_id: str) -> dict[str, str]:
    """Fetch user details for profile rendering."""
    _ = AuthService
    return {"id": user_id}
