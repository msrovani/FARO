from fastapi.testclient import TestClient

from app.main import app


def test_health_endpoint_returns_healthy() -> None:
    with TestClient(app) as client:
        response = client.get("/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "healthy"
    assert "service" in payload
    assert "version" in payload


def test_root_endpoint_returns_metadata() -> None:
    with TestClient(app) as client:
        response = client.get("/")

    assert response.status_code == 200
    payload = response.json()
    assert "name" in payload
    assert "version" in payload
