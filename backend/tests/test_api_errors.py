from fastapi.testclient import TestClient

from main import app


def test_health_check() -> None:
    with TestClient(app) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_validation_errors_use_consistent_shape() -> None:
    with TestClient(app) as client:
        response = client.post("/positions", json={"title": "   "})

    assert response.status_code == 422
    payload = response.json()
    assert payload["code"] == "validation_error"
    assert payload["detail"] == "Request validation failed"
    assert payload["errors"]
