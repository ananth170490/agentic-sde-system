from pathlib import Path

from fastapi.testclient import TestClient

from app.main import create_app


def test_shorten_and_resolve(tmp_path: Path) -> None:
    app = create_app(str(tmp_path / "core.db"))
    client = TestClient(app)

    create = client.post("/api/v1/shorten", json={"target_url": "https://example.com/docs"})
    assert create.status_code == 201
    code = create.json()["code"]

    resolve = client.get(f"/api/v1/{code}", follow_redirects=False)
    assert resolve.status_code == 307
    assert resolve.headers["location"] == "https://example.com/docs"


def test_resolve_missing_code(tmp_path: Path) -> None:
    app = create_app(str(tmp_path / "core.db"))
    client = TestClient(app)

    response = client.get("/api/v1/does-not-exist")
    assert response.status_code == 404
