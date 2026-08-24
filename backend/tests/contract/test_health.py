from fastapi.testclient import TestClient

from sketch2life.interfaces.http.app import create_app


def test_health_endpoint() -> None:
    response = TestClient(create_app()).get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "sketch2life-api"}
