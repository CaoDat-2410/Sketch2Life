"""OpenAPI pins for the School Manager capacity endpoints."""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

import pytest

from sketch2life.infrastructure.config.settings import (
    CoreDatabaseSettings,
    Settings,
    get_core_database_settings,
    get_settings,
)
from sketch2life.interfaces.http.app import create_app


@pytest.fixture
def capacity_openapi(monkeypatch: pytest.MonkeyPatch) -> Iterator[dict[str, Any]]:
    monkeypatch.setitem(Settings.model_config, "env_file", None)
    monkeypatch.setitem(CoreDatabaseSettings.model_config, "env_file", None)
    monkeypatch.setenv("SKETCH2LIFE_ENV", "test")
    monkeypatch.setenv("STORYRUN_LITE_MAIN_DEMO_ENABLED", "0")
    monkeypatch.setenv("SKETCH2LIFE_DATABASE_URL", "postgresql+psycopg://localhost:9/s1at_closed")
    get_settings.cache_clear()
    get_core_database_settings.cache_clear()
    app = create_app()
    runtime = getattr(app.state, "be1_runtime", None)
    try:
        app.openapi()
        yield app.state.runtime_openapi_schema
    finally:
        if runtime is not None and runtime.engine is not None:
            runtime.engine.dispose()
        get_settings.cache_clear()
        get_core_database_settings.cache_clear()


def test_manager_capacity_path_has_exact_get_and_patch_operations(
    capacity_openapi: dict[str, Any],
) -> None:
    path = "/api/be1/v1/organizations/{organization_id}/capacity"
    paths = capacity_openapi["paths"]
    assert {method for method in paths[path] if method in {"get", "patch"}} == {
        "get",
        "patch",
    }
    assert set(paths[path]) == {"get", "patch"}
    assert paths[path]["get"]["responses"]["200"]["content"]["application/json"]["schema"][
        "$ref"
    ].endswith("/Be1OrganizationCapacityV1")


def test_capacity_patch_publishes_required_version_and_idempotency_headers(
    capacity_openapi: dict[str, Any],
) -> None:
    patch = capacity_openapi["paths"][
        "/api/be1/v1/organizations/{organization_id}/capacity"
    ]["patch"]
    parameters = {
        (parameter["in"], parameter["name"]): parameter
        for parameter in patch["parameters"]
    }
    assert parameters[("header", "Idempotency-Key")]["required"] is True
    assert parameters[("header", "If-Match")]["required"] is True
    assert parameters[("path", "organization_id")]["required"] is True
    body = patch["requestBody"]["content"]["application/json"]["schema"]
    assert body["$ref"].endswith("/Be1CapacityConfigureRequest")
    component = capacity_openapi["components"]["schemas"]["Be1CapacityConfigureRequest"]
    assert set(component["properties"]) == {"action", "addon_slots", "suspend_class_refs"}
    assert component["additionalProperties"] is False
