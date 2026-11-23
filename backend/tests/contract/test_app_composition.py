import json
from collections.abc import Iterator
from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine

import sketch2life.interfaces.http.app as app_module
import sketch2life.interfaces.http.be1_runtime as runtime_module
from sketch2life.infrastructure.config.settings import (
    CoreDatabaseSettings,
    Settings,
    get_core_database_settings,
    get_settings,
)
from sketch2life.infrastructure.persistence.database import CoreDatabaseConfigurationError
from sketch2life.infrastructure.vision_analysis.pilot_composition import (
    PilotVisionComposition,
)
from sketch2life.interfaces.http.app import (
    create_app,
    create_classroom_app,
    create_demo_app,
)
from sketch2life.interfaces.http.openapi_srs_v22 import (
    PARENT_EXPO_INCLUDED_OPERATIONS,
    PARENT_EXPO_OPERATION_TAG,
)
from sketch2life.interfaces.http.be1_runtime import get_db, get_verified_adult


@pytest.fixture(autouse=True)
def _disable_dotenv_for_composition_tests(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    monkeypatch.setitem(Settings.model_config, "env_file", None)
    monkeypatch.setitem(CoreDatabaseSettings.model_config, "env_file", None)
    monkeypatch.setenv("SKETCH2LIFE_ENV", "test")
    monkeypatch.setenv("STORYRUN_LITE_MAIN_DEMO_ENABLED", "0")
    monkeypatch.setenv(
        "SKETCH2LIFE_DATABASE_URL", "postgresql+psycopg://localhost:9/s1at_closed"
    )
    get_settings.cache_clear()
    get_core_database_settings.cache_clear()
    assert Settings.model_config.get("env_file") is None
    assert CoreDatabaseSettings.model_config.get("env_file") is None
    try:
        yield
    finally:
        get_settings.cache_clear()
        get_core_database_settings.cache_clear()


def _mounted_route_methods(application: FastAPI) -> dict[str, list[str]]:
    application.openapi()
    paths = application.state.runtime_openapi_schema["paths"]
    http_methods = {"get", "post", "put", "patch", "delete", "options", "head"}
    return {
        path: sorted(method.upper() for method in path_item if method.lower() in http_methods)
        for path, path_item in paths.items()
    }


def test_compatibility_app_preserves_baseline_route_surface() -> None:
    repository_root = Path(__file__).resolve().parents[3]
    baseline_path = (
        repository_root
        / "features"
        / "FEAT-059-code-structure-cleanup"
        / "evidence"
        / "metrics"
        / "baseline_routes.json"
    )
    expected_entries = json.loads(baseline_path.read_text(encoding="utf-8"))
    expected = {
        entry["path"]: sorted(entry["methods"])
        for entry in expected_entries
    }
    expected.pop("/api/be1/v1/organizations/{organization_id}/assignments", None)
    expected.pop(
        "/api/be1/v1/organizations/{organization_id}/assignments/{assignment_id}", None
    )
    expected.update(
        {
            # FEAT-081 C3b: the Parent run-history list on the same path.
            "/v1/story-runs": ["GET", "POST"],
            "/v1/story-runs/active/current": ["GET"],
            # FR-C-08 (Contract Draft 11 §3.2): the Parent delete route on the same path.
            "/v1/story-runs/{run_id}": ["DELETE", "GET"],
            "/v1/story-runs/{run_id}/cancel": ["POST"],
            "/v1/story-runs/{run_id}/context-confirmation": ["POST"],
            "/v1/story-runs/{run_id}/subject-confirmation": ["POST"],
            "/v1/story-runs/{run_id}/script-confirmation": ["POST"],
        }
    )
    application = create_app()
    unprojected_openapi = application.openapi(fe_projected=False)
    actual = {
        path: sorted(method.upper() for method in operations)
        for path, operations in unprojected_openapi["paths"].items()
    }
    # OpenAPI is an SRS projection; inspect mounted routes for the full legacy surface.
    mounted = _mounted_route_methods(application)
    assert mounted == actual
    # Frozen method/path pairs from the FEAT-063 Rev32 API purpose catalog.
    library = "/api/lesson-library/v1"
    organization = f"{library}/organizations/{{organization_id}}"
    lesson = f"{organization}/lessons/{{lesson_id}}"
    upload = f"{library}/upload-sessions/{{upload_session_id}}"
    lesson_library_methods = {
        f"{library}/me/lesson-invitations": ["GET"],
        f"{library}/me/lesson-invitations/{{access_grant_id}}/accept": ["POST"],
        f"{library}/me/lesson-invitations/{{access_grant_id}}/decline": ["POST"],
        f"{library}/me/lessons": ["GET"],
        f"{library}/me/lessons/{{lesson_id}}": ["GET"],
        f"{library}/me/lessons/{{lesson_id}}/download": ["GET"],
        f"{library}/me/parent-group-invitations": ["GET"],
        f"{library}/me/parent-group-invitations/{{membership_id}}/accept": ["POST"],
        f"{organization}/access-grants": ["GET"],
        f"{organization}/access-grants/{{access_grant_id}}/decision": ["POST"],
        f"{organization}/lessons": ["GET", "POST"],
        lesson: ["DELETE", "GET", "PATCH"],
        f"{lesson}/access-grants": ["POST"],
        f"{lesson}/access-grants/{{access_grant_id}}": ["DELETE"],
        f"{lesson}/source-documents/{{source_document_id}}": ["GET"],
        f"{lesson}/source-documents/{{source_document_id}}/revisions/{{revision_id}}": ["GET"],
        f"{lesson}/upload-sessions": ["POST"],
        f"{lesson}/versions": ["POST"],
        f"{organization}/parent-groups": ["GET", "POST"],
        f"{organization}/parent-groups/{{parent_group_id}}/invitations": ["POST"],
        f"{organization}/parent-groups/{{parent_group_id}}/members/{{membership_id}}": ["DELETE"],
        f"{library}/platform/lessons/{{lesson_id}}/moderation": ["PATCH"],
        upload: ["DELETE", "GET"],
        f"{upload}/complete": ["POST"],
        f"{upload}/parts/{{part_number}}": ["PUT"],
    }

    # Preserve the pre-integration route surface while enumerating current additions.
    assert expected.items() <= actual.items()
    assert set(actual) - set(expected) == {
        "/api/be1/v1/classes/{class_id}/assignments",
        # FEAT-066 M9-B: same-organization Teacher candidates for the first assignment.
        "/api/be1/v1/organizations/{organization_id}/teacher-candidates",
        "/api/be1/v1/device-grants/{grant_id}/join-status",
        "/api/be1/v1/organizations/{organization_id}/sessions/{session_id}/completion",
        "/api/be1/v1/organizations/{organization_id}/sessions/{session_id}/learning-stage",
        "/api/be1/v1/organizations/{organization_id}/sessions/{session_id}/learning-stage/advance",
        "/api/be1/v1/organizations/{organization_id}/sessions/{session_id}/outcome",
        "/api/be1/v1/organizations/{organization_id}/sessions/{session_id}/pilot-profiles",
        "/api/be1/v1/organizations/{organization_id}/sessions/{session_id}/room-code/rotate",
        "/api/be1/v1/organizations/{organization_id}/sessions/{session_id}/roster",
        "/api/be1/v1/room-code/join",
        "/api/be1/v1/assistance-requests",
        "/api/be1/v1/assistance-requests/{assistance_id}/cancel",
        "/api/be1/v1/organizations/{organization_id}/sessions/{session_id}/assistance-requests/{assistance_id}/status",
        "/api/be1/v1/organizations/{organization_id}/sessions/{session_id}/teacher/assistance-requests/pending",
        "/v1/parent/profiles",
        "/v1/parent/profiles/{profile_id}",
    } | set(lesson_library_methods) | {
        "/api/auth/v1/registrations",
        "/api/auth/v1/me",
        "/api/platform-admin/v1/accounts",
        "/api/platform-admin/v1/accounts/{account_id}",
        "/api/parent/v1/ai/sketch-guides",
        "/api/parent/v1/ai/drawing-understandings",
        "/api/parent/v1/ai/story-runs/{run_id}/story-revisions",
        "/api/teacher/v1/organizations/{organization_id}/ai/lesson-plan-suggestions",
        "/api/teacher/v1/organizations/{organization_id}/ai/sketch-decks",
        "/api/teacher/v1/organizations/{organization_id}/ai/lesson-visuals",
    } | {path for _method, path in PARENT_EXPO_INCLUDED_OPERATIONS} | {
        "/api/svg-catalog/v1/parent/guides",
        "/api/svg-catalog/v1/organizations/{organization_id}/assets",
        "/api/svg-catalog/v1/organizations/{organization_id}/assets/{catalog_entry_id}/guide-revisions",
        "/api/svg-catalog/v1/organizations/{organization_id}/assets/{catalog_entry_id}/guide-revisions/{guide_revision_id}/educator-reviews",
        "/api/svg-catalog/v1/organizations/{organization_id}/assets/{catalog_entry_id}/source-reviews",
        "/api/svg-catalog/v1/platform/assets",
        "/api/svg-catalog/v1/platform/assets/{catalog_entry_id}/curation",
        "/api/svg-catalog/v1/platform/assets/{catalog_entry_id}/guide-revisions",
        "/api/svg-catalog/v1/platform/assets/{catalog_entry_id}/guide-revisions/{guide_revision_id}/educator-reviews",
        "/api/svg-catalog/v1/platform/assets/{catalog_entry_id}/source-reviews",
    }
    assert {path: actual[path] for path in lesson_library_methods} == lesson_library_methods


def test_compatibility_app_keeps_be1_and_demo_services_on_app_state() -> None:
    application = create_app()

    assert application.state.be1_runtime is not None
    assert application.state.be1_runtime.pilot_vision is None
    assert application.state.session_service is not None
    assert application.state.live_image_demo_service is not None
    assert application.state.supervised_flow_service is not None


def test_legacy_parent_story_revision_requires_idempotency_and_uses_srs_error_envelope() -> None:
    application = create_app()
    application.dependency_overrides[get_verified_adult] = lambda: object()
    application.dependency_overrides[get_db] = lambda: object()

    with TestClient(application) as client:
        response = client.post(
            "/api/parent/v1/ai/story-runs/01234567-89ab-cdef-0123-456789abcdef/story-revisions",
            json={"expected_understanding_revision": 1},
        )

    assert response.status_code == 400
    body = response.json()
    assert body["code"] == "INVALID_IDEMPOTENCY_KEY"
    assert body["correlation_id"]
    assert body["retryable"] is False
    assert "detail" not in body


def test_classroom_profile_excludes_process_local_demo_routes() -> None:
    application = create_classroom_app()
    openapi = application.openapi()
    paths = set(application.state.runtime_openapi_schema["paths"])

    assert "/health" in paths
    assert "/api/be1/v1/health" in paths
    assert "/v1/parent/profiles" in paths
    assert "/v1/parent/profiles/{profile_id}" in paths
    assert "get" in openapi["paths"]["/v1/parent/profiles"]
    assert "post" in openapi["paths"]["/v1/parent/profiles"]
    assert "delete" in openapi["paths"]["/v1/parent/profiles/{profile_id}"]
    assert "/v1/sessions" not in paths
    assert "/v1/profile/preferences/classify" not in paths
    assert application.state.session_service is None
    assert application.state.live_image_demo_service is None


def test_current_parent_expo_api_operations_are_published_in_openapi() -> None:
    application = create_app()
    runtime_schema = application.openapi(fe_projected=False)
    public_schema = application.openapi()

    for method, path in PARENT_EXPO_INCLUDED_OPERATIONS:
        assert method in runtime_schema["paths"][path]
        assert method in public_schema["paths"][path]

    assert any(tag["name"] == PARENT_EXPO_OPERATION_TAG for tag in public_schema["tags"])
    assert "/api/parent/v1/ai/video-generation" not in public_schema["paths"]


def test_pilot_assistance_gate_fails_closed_when_disabled() -> None:
    application = create_classroom_app()
    settings = Settings(
        env="local",
        synthetic_pilot_enabled=False,
        _env_file=None,  # type: ignore[call-arg]
    )
    runtime = SimpleNamespace(settings=settings, pilot_vision=None)
    application.dependency_overrides[runtime_module.get_runtime] = lambda: runtime

    with TestClient(application) as client:
        response = client.post("/api/be1/v1/assistance-requests", json={})

    assert response.status_code == 503
    assert "PILOT_ASSISTANCE_DISABLED" in response.text


def test_demo_profile_excludes_durable_classroom_routes() -> None:
    application = create_demo_app()
    openapi = application.openapi()
    paths = set(application.state.runtime_openapi_schema["paths"])

    assert "/v1/sessions" in paths
    assert "/api/be1/v1/health" not in paths
    assert "/v1/parent/profiles" not in paths
    assert "/v1/parent/profiles/{profile_id}" not in paths
    assert "/v1/parent/profiles" not in openapi["paths"]
    assert "/v1/parent/profiles/{profile_id}" not in openapi["paths"]
    assert application.state.session_service is not None
    assert application.state.live_image_demo_service is not None


def test_real_app_composes_pilot_only_for_valid_local_synthetic_gate(
    monkeypatch, tmp_path: Path
) -> None:
    settings = Settings(
        env="test",
        synthetic_pilot_enabled=True,
        be1_artifact_root=tmp_path / "artifacts",
        _env_file=None,  # type: ignore[call-arg]
    )
    monkeypatch.setattr(app_module, "get_settings", lambda: settings)
    monkeypatch.setattr(
        runtime_module,
        "get_core_database_settings",
        lambda: SimpleNamespace(database_url=None),
    )

    postgres_engine = create_engine(
        "postgresql+psycopg://postgres:unused@127.0.0.1:5433/pilot_composition_test"
    )
    monkeypatch.setattr(runtime_module, "create_core_engine", lambda _url: postgres_engine)
    application = create_app()
    assert isinstance(application.state.be1_runtime.pilot_vision, PilotVisionComposition)
    postgres_engine.dispose()

    disabled_settings = settings.model_copy(update={"synthetic_pilot_enabled": False})
    monkeypatch.setattr(app_module, "get_settings", lambda: disabled_settings)
    disabled_engine = create_engine(
        "postgresql+psycopg://postgres:unused@127.0.0.1:5433/pilot_composition_test"
    )
    monkeypatch.setattr(runtime_module, "create_core_engine", lambda _url: disabled_engine)
    disabled = create_app()
    assert disabled.state.be1_runtime.pilot_vision is None
    disabled_engine.dispose()

    monkeypatch.setattr(app_module, "get_settings", lambda: settings)
    non_postgres_engine = create_engine("sqlite://")
    monkeypatch.setattr(runtime_module, "create_core_engine", lambda _url: non_postgres_engine)
    rejected = create_app()
    assert rejected.state.be1_runtime.pilot_vision is None
    non_postgres_engine.dispose()

    staging_settings = Settings(
        env="staging",
        auth_provider="firebase",
        firebase_project_id="synthetic-test-project",
        synthetic_pilot_enabled=True,
        _env_file=None,  # type: ignore[call-arg]
    )
    monkeypatch.setattr(app_module, "get_settings", lambda: staging_settings)
    staging_engine = create_engine(
        "postgresql+psycopg://postgres:unused@127.0.0.1:5433/pilot_composition_test"
    )
    monkeypatch.setattr(runtime_module, "create_core_engine", lambda _url: staging_engine)
    staging = create_app()
    assert staging.state.be1_runtime.pilot_vision is None
    staging_engine.dispose()

    monkeypatch.setattr(app_module, "get_settings", lambda: settings)
    monkeypatch.setattr(
        runtime_module,
        "create_core_engine",
        lambda _url: (_ for _ in ()).throw(
            CoreDatabaseConfigurationError("synthetic missing database configuration")
        ),
    )
    unavailable = create_app()
    assert unavailable.state.be1_runtime.engine is None
    assert unavailable.state.be1_runtime.pilot_vision is None
