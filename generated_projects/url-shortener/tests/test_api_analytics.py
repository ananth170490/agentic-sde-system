from pathlib import Path

from fastapi.testclient import TestClient

from app.main import create_app


def test_analytics_counts_redirects(tmp_path: Path) -> None:
    app = create_app(str(tmp_path / "analytics.db"))
    client = TestClient(app)

    create = client.post("/api/v1/shorten", json={"target_url": "https://example.com/page"})
    assert create.status_code == 201
    code = create.json()["code"]

    client.get(f"/api/v1/{code}", follow_redirects=False)
    client.get(f"/api/v1/{code}", follow_redirects=False)

    analytics = client.get(f"/api/v1/analytics/{code}")
    assert analytics.status_code == 200
    assert analytics.json()["clicks"] == 2
