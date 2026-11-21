"""CONV-1 contract tests through `create_app` (FEAT-066 D-066-68, D-066-71). Owner-run.

They need a TestClient (loopback sockets), so they run in the owner's terminal. No database:
the database and identity dependencies are overridden, and every case fails before a query.
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

import pytest
from fastapi import FastAPI, Response
from fastapi.testclient import TestClient

from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.interfaces.http.admin_contract import ADMIN_OPERATIONS
from sketch2life.interfaces.http.app import create_app
from sketch2life.interfaces.http.be1_runtime import get_db, get_verified_adult
from sketch2life.interfaces.http.error_envelope import MESSAGES
from sketch2life.interfaces.http.openapi_contract_amendments import (
    BE1_KEPT_422_OPERATIONS,
    LESSON_LIBRARY_KEPT_422_OPERATIONS,
)
from sketch2life.interfaces.http.routers.lesson_library import get_lesson_library_service

SIX_FIELDS = {
    "code",
    "message",
    "correlation_id",
    "retryable",
    "retry_after_seconds",
    "field_errors",
}
PRINCIPAL = VerifiedPrincipal(
    subject="conv1-synthetic-adult", issuer="https://issuer.example.test", roles=frozenset()
)


class _NoDb:
    """A stand-in session; any use means a case reached the database by mistake."""

    def __getattr__(self, name: str) -> Any:
        raise AssertionError(f"database used: {name}")


@pytest.fixture
def app() -> FastAPI:
    application = create_app()
    application.dependency_overrides[get_verified_adult] = lambda: PRINCIPAL

    def _db() -> Iterator[Any]:
        yield _NoDb()

    application.dependency_overrides[get_db] = _db
    application.dependency_overrides[get_lesson_library_service] = lambda: object()
    return application


@pytest.fixture
def client(app: FastAPI) -> TestClient:
    return TestClient(app, raise_server_exceptions=False)


def _assert_envelope(response: Any, status: int, code: str) -> dict[str, Any]:
    assert response.status_code == status, response.text
    body = response.json()
    assert set(body) >= SIX_FIELDS
    assert body["code"] == code
    assert body["request_id"] == body["correlation_id"] == response.headers["X-Request-ID"]
    return body


def test_be1_validation_is_400_with_non_echoing_field_errors(client: TestClient) -> None:
    response = client.post(
        "/api/be1/v1/organizations/conv1-org/classes",
        json={"display_name": "Synthetic class", "role": "school_admin-forged-value"},
        headers={"X-Request-ID": "conv1-req-1"},
    )
    body = _assert_envelope(response, 400, "INVALID_REQUEST")
    assert body["correlation_id"] == "conv1-req-1"
    assert body["message"] == MESSAGES["INVALID_REQUEST"]
    assert body["field_errors"]
    assert "forged-value" not in response.text


def test_lesson_library_limit_above_100_is_400(client: TestClient) -> None:
    response = client.get(
        "/api/lesson-library/v1/organizations/conv1-org/parent-groups",
        params={"limit": 101},
    )
    body = _assert_envelope(response, 400, "INVALID_REQUEST")
    assert {"field": "limit", "code": "OUT_OF_RANGE"} in body["field_errors"]


def test_unknown_conv1_route_is_uniform_404(client: TestClient) -> None:
    response = client.get("/api/be1/v1/no-such-resource")
    _assert_envelope(response, 404, "RESOURCE_NOT_FOUND")


def test_unhandled_error_is_500_envelope_with_header(app: FastAPI, client: TestClient) -> None:
    def _broken_db() -> Iterator[Any]:
        raise RuntimeError("synthetic failure with a local path C:/secret")
        yield  # pragma: no cover

    app.dependency_overrides[get_db] = _broken_db
    response = client.get("/api/be1/v1/organizations/conv1-org/classes")
    body = _assert_envelope(response, 500, "INTERNAL_SERVER_ERROR")
    assert "secret" not in response.text
    assert body["retryable"] is False


def test_lesson_library_part_over_limit_is_413_envelope(client: TestClient) -> None:
    response = client.put(
        "/api/lesson-library/v1/upload-sessions/conv1-upload/parts/1",
        content=b"x" * (4 * 1024 * 1024 + 1),
        headers={"X-Request-ID": "conv1-req-413", "Content-Type": "application/octet-stream"},
    )
    body = _assert_envelope(response, 413, "LESSON_FILE_TOO_LARGE")
    assert body["correlation_id"] == "conv1-req-413"


def test_every_response_carries_x_request_id_and_route_header_is_kept(app: FastAPI) -> None:
    def _route_sets_header() -> Response:
        return Response("ok", headers={"X-Request-ID": "route-set-id"})

    app.add_api_route("/conv1-route-sets-header", _route_sets_header)
    client = TestClient(app, raise_server_exceptions=False)
    assert client.get("/conv1-route-sets-header").headers["X-Request-ID"] == "route-set-id"
    legacy = client.get("/health")
    assert legacy.headers.get("X-Request-ID")


def test_parent_ai_family_keeps_its_detail_body(client: TestClient) -> None:
    """CV-1: `/api/parent/v1/ai` is not in CONV-1; its 4xx bodies keep `{"detail": ...}`."""
    response = client.get("/api/parent/v1/ai/conv1-unknown-route")
    assert response.status_code == 404
    assert "detail" in response.json()
    assert "correlation_id" not in response.json()


def test_openapi_shows_400_envelope_for_catalogued_families(client: TestClient) -> None:
    """The published (FE-projected) spec shows 400, and 422 only on the kept-422 operations."""
    spec = client.get("/openapi.json").json()
    kept = BE1_KEPT_422_OPERATIONS | LESSON_LIBRARY_KEPT_422_OPERATIONS
    checked = 0
    for path, path_item in spec["paths"].items():
        if not path.startswith(("/api/be1/v1/", "/api/lesson-library/v1/")):
            continue
        for method, operation in path_item.items():
            responses = operation.get("responses", {})
            if (method, path) in ADMIN_OPERATIONS:
                # FEAT-072 Admin additions (lesson feedback) are published as implemented.
                continue
            if (method, path) not in kept:
                assert "422" not in responses, (method, path)
            checked += 1
    assert checked > 0
    create_class = spec["paths"]["/api/be1/v1/organizations/{organization_id}/classes"]["post"]
    assert "400" in create_class["responses"]
