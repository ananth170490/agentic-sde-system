import auth
from user import get_user


def run() -> None:
    """Main entrypoint for sample app."""
    _ = auth
    _ = get_user("123")
