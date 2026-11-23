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
from sketch2life.interfaces.http.admin_contract import ADMIN_OPERATIONS
from sketch2life.interfaces.http.app import (
    create_app,
    create_classroom_app,
    create_demo_app,
)
from sketch2life.interfaces.http.be1_runtime import get_db, get_verified_adult


@pytest.fixture(autouse=True)
def _disable_dotenv_for_composition_tests(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    monkeypatch.setitem(Settings.model_config, "env_file", None)
    monkeypatch.setitem(CoreDatabaseSettings.model_config, "env_file", None)
    monkeypatch.setenv("SKETCH2LIFE_ENV", "test")
    monkeypatch.setenv("STORYRUN_LITE_MAIN_DEMO_ENABLED", "0")
    monkeypatch.setenv("SKETCH2LIFE_DATABASE_URL", "postgresql+psycopg://localhost:9/s1at_closed")
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
    expected = {entry["path"]: sorted(entry["methods"]) for entry in expected_entries}
    expected.pop("/api/be1/v1/organizations/{organization_id}/assignments", None)
    expected.pop("/api/be1/v1/organizations/{organization_id}/assignments/{assignment_id}", None)
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
            # FEAT-066 T-2b: the Parent run drawing attach (SRS l.1664).
            "/v1/story-runs/{run_id}/assets": ["POST"],
            # FEAT-066 T-2c: the run idea, the transcript read and its confirmation (SRS l.1665).
            "/v1/story-runs/{run_id}/idea": ["POST"],
            "/v1/story-runs/{run_id}/transcript": ["GET"],
            "/v1/story-runs/{run_id}/transcript-confirmation": ["POST"],
            # FEAT-066 T-2d: the story rewrite (SRS l.1668).
            "/v1/story-runs/{run_id}/story-rewrites": ["POST"],
            # FEAT-066 T-1a: the Parent video request (SRS l.1670).
            "/v1/story-runs/{run_id}/video-generations": ["POST"],
            # FEAT-066 T-1b: the adult's decisions on a ready video (SRS l.1671-1672).
            "/v1/story-runs/{run_id}/video-unsuitable": ["POST"],
            "/v1/story-runs/{run_id}/complete": ["POST"],
            # FEAT-066 T-1c: the playback grant and the header-borne stream (SRS l.1676, l.1691).
            "/v1/story-runs/{run_id}/playback-token": ["POST"],
            "/v1/story-runs/{run_id}/playback": ["GET"],
            # FEAT-066 goal v4 T-2e-a: the Parent main activity (the list and the selection).
            "/v1/activities": ["GET"],
            "/v1/story-runs/{run_id}/activity-selection": ["POST"],
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

    # Preserve the full pre-integration route surface while allowing only the
    # reviewed classroom, Parent profile, and Lesson Library contracts.
    assert expected.items() <= actual.items()
    from sketch2life.interfaces.http.openapi_contract import FEAT083_OPERATIONS

    added_paths = {path for _, path in FEAT083_OPERATIONS}
    assert set(actual) - set(expected) == {
        # FEAT-066 T0.3: the public liveness probe (the operator probes are not in the schema).
        "/health/live",
        "/api/be1/v1/classes/{class_id}/assignments",
        "/api/be1/v1/classes/{class_id}/suspend",  # FEAT-066 T-7b
        "/api/be1/v1/classes/{class_id}/archive",  # FEAT-066 T-7b
        "/api/be1/v1/classes/{class_id}/profiles/{child_id}/move",  # FEAT-066 T-7d
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
    } | set(lesson_library_methods) | {path for _, path in ADMIN_OPERATIONS} | added_paths | {
        "/api/auth/v1/registrations",
        "/api/auth/v1/me",
        # FEAT-066 T0.4: live job poll route (runtime-only).
        "/v1/jobs/{job_id}",
        # FEAT-066 T-2a: generic upload sessions (SRS l.1654-1658), mounted with the demo off.
        "/v1/upload-sessions",
        "/v1/upload-sessions/{upload_id}",
        "/v1/upload-sessions/{upload_id}/parts/{part_no}",
        "/v1/upload-sessions/{upload_id}/complete",
        # FEAT-066 T-3a: Teacher lesson occurrences (SRS l.1652), always mounted.
        "/v1/lesson-occurrences",
        "/v1/lesson-occurrences/{occurrence_id}",
        # FEAT-066 T-3b: the occurrence source documents (SRS l.1653).
        "/v1/lesson-occurrences/{occurrence_id}/documents",
        "/v1/lesson-occurrences/{occurrence_id}/documents/{document_id}",
        "/v1/lesson-occurrences/{occurrence_id}/documents/{document_id}/revisions",
        "/v1/lesson-occurrences/{occurrence_id}/documents/{document_id}/revisions/{revision_no}",
        # FEAT-066 T-3d: the occurrence plan revisions (SRS l.1659-1660).
        "/v1/lesson-occurrences/{occurrence_id}/plan-revisions",
        "/v1/lesson-occurrences/{occurrence_id}/plan-revisions/{revision_no}",
        "/v1/lesson-occurrences/{occurrence_id}/plan-revisions/{revision_no}/confirm",
        # FEAT-066 T-4b1: the Teacher random-child selection (SRS l.341-352), always mounted.
        "/v1/lesson-occurrences/{occurrence_id}/child-selections",
        "/v1/lesson-occurrences/{occurrence_id}/child-selections/{selection_id}",
        "/v1/lesson-occurrences/{occurrence_id}/child-selections/{selection_id}/confirmation",
        # FEAT-066 T-5a: the class projection of the sample video (SRS l.1661-1662), always mounted.
        "/v1/lesson-occurrences/{occurrence_id}/projection-confirmation",
        "/v1/lesson-occurrences/{occurrence_id}/projection-playback-token",
        # FEAT-066 T-8a: the notification inbox (SRS l.1681), always mounted.
        "/v1/notifications",
        "/v1/notifications/read-all",
        "/v1/notifications/{inbox_item_id}/read",
        "/api/platform-admin/v1/accounts",
        "/api/platform-admin/v1/accounts/{account_id}",
        "/api/parent/v1/ai/sketch-guides",
        "/api/parent/v1/ai/drawing-understandings",
        "/api/parent/v1/ai/story-runs/{run_id}/story-revisions",
        "/api/teacher/v1/organizations/{organization_id}/ai/lesson-plan-suggestions",
        "/api/teacher/v1/organizations/{organization_id}/ai/sketch-decks",
        "/api/teacher/v1/organizations/{organization_id}/ai/lesson-visuals",
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


# --- T-2z: scanner and media-validator selection (TD-29) -----------------------------------


def test_default_composition_keeps_clamav_and_no_media_validator() -> None:
    from sketch2life.infrastructure.documents.clamav_scanner import ClamAvScanner

    application = create_app()

    assert isinstance(application.state.lesson_document_scanner, ClamAvScanner)
    assert application.state.upload_media_validator is None


def test_other_profiles_define_the_media_validator_state_as_none() -> None:
    assert create_classroom_app().state.upload_media_validator is None
    assert create_demo_app().state.upload_media_validator is None


def test_local_test_adapter_selection_composes_both_local_adapters(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    from sketch2life.infrastructure.documents.local_test_adapters import (
        LocalTestAllowlistScanner,
        LocalTestSignatureMediaValidator,
    )

    allowlist = tmp_path / "allowlist.json"
    allowlist.write_text(json.dumps({"sha256": ["a" * 64]}), encoding="utf-8")
    monkeypatch.setenv("SKETCH2LIFE_SCANNER_ADAPTER", "local_test_allowlist")
    monkeypatch.setenv("SKETCH2LIFE_LOCAL_SCANNER_ALLOWLIST_FILE", str(allowlist))
    get_settings.cache_clear()

    application = create_app()

    assert isinstance(application.state.lesson_document_scanner, LocalTestAllowlistScanner)
    assert isinstance(application.state.upload_media_validator, LocalTestSignatureMediaValidator)
    assert application.state.lesson_document_scanner.scanner_name == "local-test-allowlist"


def test_allowlist_file_without_the_adapter_flag_keeps_clamav(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    from sketch2life.infrastructure.documents.clamav_scanner import ClamAvScanner

    allowlist = tmp_path / "allowlist.json"
    allowlist.write_text(json.dumps({"sha256": ["a" * 64]}), encoding="utf-8")
    monkeypatch.setenv("SKETCH2LIFE_LOCAL_SCANNER_ALLOWLIST_FILE", str(allowlist))
    get_settings.cache_clear()

    application = create_app()

    assert isinstance(application.state.lesson_document_scanner, ClamAvScanner)
    assert application.state.upload_media_validator is None


def test_local_adapter_selection_with_an_unusable_allowlist_stops_startup(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    from sketch2life.infrastructure.documents.local_test_adapters import LocalAdapterRefused

    monkeypatch.setenv("SKETCH2LIFE_SCANNER_ADAPTER", "local_test_allowlist")
    monkeypatch.setenv("SKETCH2LIFE_LOCAL_SCANNER_ALLOWLIST_FILE", str(tmp_path / "absent.json"))
    get_settings.cache_clear()

    with pytest.raises(LocalAdapterRefused):
        create_app()


@pytest.mark.parametrize("env", ["staging", "production"])
def test_the_process_does_not_start_with_the_local_scanner_outside_local_and_test(
    monkeypatch: pytest.MonkeyPatch, env: str
) -> None:
    from pydantic import ValidationError

    monkeypatch.setenv("SKETCH2LIFE_ENV", env)
    monkeypatch.setenv("SKETCH2LIFE_SCANNER_ADAPTER", "local_test_allowlist")
    get_settings.cache_clear()

    with pytest.raises(ValidationError, match="local test scanner adapter"):
        create_app()
