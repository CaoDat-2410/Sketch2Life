from fastapi import FastAPI
from fastapi.testclient import TestClient

from sketch2life.interfaces.http.app import _configure_local_web_cors


def _cors_test_client(environment: str) -> TestClient:
    application = FastAPI()
    application.get("/api/auth/v1/me")(lambda: {"role": "teacher"})
    _configure_local_web_cors(application, environment)
    return TestClient(application)


def test_loopback_web_origin_can_preflight_authenticated_get() -> None:
    response = _cors_test_client("local").options(
        "/api/auth/v1/me",
        headers={
            "Origin": "http://127.0.0.1:5174",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "accept,authorization",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://127.0.0.1:5174"
    assert response.headers["access-control-allow-credentials"] == "true"
    assert "authorization" in response.headers["access-control-allow-headers"].lower()

    parent_command = _cors_test_client("local").options(
        "/api/parent/v1/story-runs/example/cancel",
        headers={
            "Origin": "http://localhost:8082",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": (
                "authorization,content-type,idempotency-key,x-request-id"
            ),
        },
    )
    assert parent_command.status_code == 200
    assert "idempotency-key" in parent_command.headers[
        "access-control-allow-headers"
    ].lower()


def test_non_loopback_origin_receives_no_cors_grant() -> None:
    response = _cors_test_client("test").options(
        "/api/auth/v1/me",
        headers={
            "Origin": "https://example.invalid",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "authorization",
        },
    )

    assert response.status_code == 400
    assert "access-control-allow-origin" not in response.headers


def test_deployed_environment_does_not_enable_local_web_cors() -> None:
    response = _cors_test_client("production").options(
        "/api/auth/v1/me",
        headers={
            "Origin": "http://127.0.0.1:5174",
            "Access-Control-Request-Method": "GET",
        },
    )

    assert "access-control-allow-origin" not in response.headers
