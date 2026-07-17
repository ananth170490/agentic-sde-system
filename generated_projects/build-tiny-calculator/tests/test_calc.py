from app.calc import add


def test_add() -> None:
    assert add(1, 1) == 2
