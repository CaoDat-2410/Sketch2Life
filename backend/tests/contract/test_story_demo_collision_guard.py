"""FEAT-066 T0.5: the StoryRun-lite main demo must not replace real routes silently (TD-18)."""

from __future__ import annotations

import logging
from collections.abc import Iterator

import pytest
from fastapi import APIRouter

import sketch2life.interfaces.http.app as app_module
from sketch2life.infrastructure.config.settings import (
    CoreDatabaseSettings,
    Settings,
    get_core_database_settings,
    get_settings,
)
from sketch2life.interfaces.http.app import create_app, create_classroom_app
from sketch2life.interfaces.http.router_composition import story_demo_replaced_routers
from sketch2life.interfaces.http.routers.parent_story_runs import router as parent_story_runs_router
from sketch2life.interfaces.http.routers.story_run_lite import router as story_run_lite_router
from sketch2life.interfaces.http.routers.upload_sessions import router as upload_sessions_router
from sketch2life.interfaces.http.story_demo_guard import (
    ACKNOWLEDGEMENT_ENV,
    normalise_path,
    paths_overlap,
    read_replacement_acknowledgement,
    route_labels,
    shadowed_routes,
)

FLAG = "STORYRUN_LITE_MAIN_DEMO_ENABLED"
DATABASE_URL_SENTINEL = "postgresql+psycopg://sentinel_user:sentinel_pw@localhost:9/sentinel_db"
EXPECTED_COLLISIONS = {
    "POST /v1/story-runs",
    "GET /v1/story-runs/{run_id}",
    "POST /v1/story-runs/{run_id}/cancel",
    "POST /v1/story-runs/{run_id}/subject-confirmation",
    # FEAT-066 T-2a: the generic upload sessions answer the same literal paths as the demo.
    "POST /v1/upload-sessions",
    "GET /v1/upload-sessions/{upload_id}",
    "PUT /v1/upload-sessions/{upload_id}/parts/{part_no}",
    "POST /v1/upload-sessions/{upload_id}/complete",
    "DELETE /v1/upload-sessions/{upload_id}",
}
EXPECTED_UNMOUNTED_COUNT = len(parent_story_runs_router.routes) + len(
    upload_sessions_router.routes
)  # derived, not hard-coded


@pytest.fixture(autouse=True)
def _environment(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    monkeypatch.setitem(Settings.model_config, "env_file", None)
    monkeypatch.setitem(CoreDatabaseSettings.model_config, "env_file", None)
    monkeypatch.setenv("SKETCH2LIFE_ENV", "test")
    monkeypatch.setenv("SKETCH2LIFE_DATABASE_URL", DATABASE_URL_SENTINEL)
    monkeypatch.delenv(FLAG, raising=False)
    monkeypatch.delenv(ACKNOWLEDGEMENT_ENV, raising=False)
    get_settings.cache_clear()
    get_core_database_settings.cache_clear()
    try:
        yield
    finally:
        get_settings.cache_clear()
        get_core_database_settings.cache_clear()


def _route_paths(application) -> set[str]:
    """Paths of the app and of every included router (FastAPI wraps included routers)."""
    paths: set[str] = set()
    for route in application.routes:
        router = getattr(route, "original_router", None)
        candidates = router.routes if router is not None else [route]
        paths.update(getattr(candidate, "path", "") for candidate in candidates)
    return paths


class _ApiLogCapture(logging.Handler):
    """Attached straight to the logger: other tests may change propagation, so not `caplog`."""

    def __init__(self) -> None:
        super().__init__(logging.DEBUG)
        self.records: list[logging.LogRecord] = []

    def emit(self, record: logging.LogRecord) -> None:
        self.records.append(record)


@pytest.fixture
def api_log() -> Iterator[_ApiLogCapture]:
    logger = logging.getLogger("sketch2life.api")
    capture = _ApiLogCapture()
    previous_level, previous_disabled = logger.level, logger.disabled
    logger.addHandler(capture)
    logger.setLevel(logging.DEBUG)
    logger.disabled = False
    try:
        yield capture
    finally:
        logger.removeHandler(capture)
        logger.setLevel(previous_level)
        logger.disabled = previous_disabled


def _app_route_labels(application) -> set[tuple[str, str]]:
    labels: set[tuple[str, str]] = set()
    for route in application.routes:
        router = getattr(route, "original_router", None)
        labels.update(route_labels(router.routes if router is not None else [route]))
    return labels


def _guard_records(capture: _ApiLogCapture) -> list[logging.LogRecord]:
    return [
        record
        for record in capture.records
        if "storyrun_lite_main_demo_replaces_real_routes" in record.getMessage()
    ]


def test_flag_on_without_acknowledgement_refuses_to_start(monkeypatch):
    monkeypatch.setenv(FLAG, "1")
    with pytest.raises(ValueError) as raised:
        create_app()
    message = str(raised.value)
    assert ACKNOWLEDGEMENT_ENV in message
    assert f"collides={len(EXPECTED_COLLISIONS)}" in message
    assert f"real_routes_unmounted={EXPECTED_UNMOUNTED_COUNT}" in message
    assert "POST /v1/story-runs" in message
    assert message.count(" /v1/") <= 3  # at most three route examples
    assert "sentinel" not in message
    assert "postgresql" not in message


def test_flag_on_with_acknowledgement_zero_refuses_to_start(monkeypatch):
    monkeypatch.setenv(FLAG, "1")
    monkeypatch.setenv(ACKNOWLEDGEMENT_ENV, "0")
    with pytest.raises(ValueError, match=ACKNOWLEDGEMENT_ENV):
        create_app()


def test_acknowledged_demo_builds_warns_once_and_records_replacement(monkeypatch, api_log):
    monkeypatch.setenv(FLAG, "1")
    monkeypatch.setenv(ACKNOWLEDGEMENT_ENV, "1")
    application = create_app()
    records = _guard_records(api_log)
    assert len(records) == 1
    assert records[0].levelno == logging.WARNING
    text = records[0].getMessage()
    assert f"collides={len(EXPECTED_COLLISIONS)}" in text
    assert f"real_routes_unmounted={EXPECTED_UNMOUNTED_COUNT}" in text
    assert "parent_router_mounted=false" in text
    assert "env=test" in text
    assert "sentinel" not in text
    assert "postgresql" not in text
    assert set(application.state.story_demo_replaces_real_routes) == EXPECTED_COLLISIONS
    assert len(application.state.story_demo_unmounted_real_routes) == EXPECTED_UNMOUNTED_COUNT
    paths = _route_paths(application)
    assert "/v1/story-runs/{run_ref}" in paths  # demo router answers
    assert "/v1/story-runs/{run_id}" not in paths  # real Parent router is not mounted


def test_acknowledged_demo_openapi_names_the_replacement(monkeypatch):
    # Demo-mode OpenAPI generation fails at HEAD because the unmounted Parent router leaves
    # `ParentStoryRunEnvelopeV1` out of the components (base failure
    # `test_main_demo_openapi_uses_pinned_route_contract`). Stub the projection so the sentence
    # that this task adds is exercised without depending on that defect.
    monkeypatch.setenv(FLAG, "1")
    monkeypatch.setenv(ACKNOWLEDGEMENT_ENV, "1")
    application = create_app()
    assert "replace the real Parent story-run routes" in application.description
    monkeypatch.setattr(
        app_module,
        "project_srs_v22_openapi",
        lambda _schema: {"paths": {}, "components": {}, "info": {"description": "base"}},
    )
    monkeypatch.setattr(app_module, "add_story_run_lite_contract", lambda _schema: None)
    monkeypatch.setattr(app_module, "_story_run_lite_path", lambda _path: False)
    monkeypatch.setattr(
        application.state, "runtime_openapi_schema", {"paths": {}, "components": {}}, raising=False
    )
    description = application.openapi()["info"]["description"]
    assert description.startswith("base")
    assert description.count("replace the real Parent story-run routes") == 1


@pytest.mark.parametrize("flag", [None, "0"])
def test_flag_off_is_unchanged_and_silent(monkeypatch, api_log, flag):
    if flag is not None:
        monkeypatch.setenv(FLAG, flag)
    application = create_app()
    assert _guard_records(api_log) == []
    assert not hasattr(application.state, "story_demo_replaces_real_routes")
    paths = _route_paths(application)
    assert "/v1/story-runs/{run_id}" in paths
    assert "/v1/story-runs/{run_ref}" not in paths
    assert "replace the real Parent story-run routes" not in application.description
    description = application.openapi()["info"]["description"]
    assert "replace the real Parent story-run routes" not in description


@pytest.mark.parametrize("acknowledgement", ["1", "banana"])
def test_acknowledgement_alone_is_ignored_when_flag_is_off(monkeypatch, api_log, acknowledgement):
    monkeypatch.setenv(FLAG, "0")
    monkeypatch.setenv(ACKNOWLEDGEMENT_ENV, acknowledgement)
    application = create_app()
    assert _guard_records(api_log) == []
    assert "/v1/story-runs/{run_id}" in _route_paths(application)


@pytest.mark.parametrize("value", ["2", "true", "banana", ""])
def test_invalid_acknowledgement_value_with_flag_on_is_rejected_without_echo(monkeypatch, value):
    monkeypatch.setenv(FLAG, "1")
    monkeypatch.setenv(ACKNOWLEDGEMENT_ENV, value)
    with pytest.raises(ValueError, match="must be 0 or 1") as raised:
        create_app()
    assert ACKNOWLEDGEMENT_ENV in str(raised.value)
    if value:
        assert value not in str(raised.value).replace(ACKNOWLEDGEMENT_ENV, "")


def test_invalid_main_flag_value_keeps_its_own_error(monkeypatch):
    monkeypatch.setenv(FLAG, "banana")
    monkeypatch.setenv(ACKNOWLEDGEMENT_ENV, "1")
    with pytest.raises(ValueError, match="main demo flag must be 0 or 1"):
        create_app()


def test_profile_and_environment_errors_come_before_the_acknowledgement(monkeypatch):
    monkeypatch.setenv(FLAG, "1")  # acknowledgement deliberately unset
    with pytest.raises(ValueError, match="combined local/test"):
        create_classroom_app()
    monkeypatch.setenv("SKETCH2LIFE_ENV", "staging")
    monkeypatch.setenv("SKETCH2LIFE_AUTH_PROVIDER", "firebase")
    monkeypatch.setenv("SKETCH2LIFE_FIREBASE_PROJECT_ID", "synthetic")
    get_settings.cache_clear()
    with pytest.raises(ValueError, match="combined local/test"):
        create_app()


def test_collision_set_comes_from_the_real_route_tables():
    routes = [route for router in story_demo_replaced_routers() for route in router.routes]
    replacement = shadowed_routes(routes, story_run_lite_router.routes)
    assert set(replacement.collides) == EXPECTED_COLLISIONS
    assert len(replacement.collides) == len(EXPECTED_COLLISIONS)
    assert len(replacement.unmounted) == EXPECTED_UNMOUNTED_COUNT
    assert set(replacement.collides) <= set(replacement.unmounted)


def _router(*routes: tuple[str, str]) -> APIRouter:
    router = APIRouter()
    for method, path in routes:

        def endpoint() -> None:
            return None

        router.add_api_route(path, endpoint, methods=[method])
    return router


def test_helper_ignores_parameter_names_and_matches_literal_against_parameter():
    assert normalise_path("/v1/story-runs/{run_ref}/cancel") == "/v1/story-runs/{}/cancel"
    assert paths_overlap("/v1/story-runs/{run_id}", "/v1/story-runs/{run_ref}")
    assert paths_overlap("/v1/story-runs/{run_id}", "/v1/story-runs/readiness")
    assert not paths_overlap("/v1/story-runs/{run_id}", "/v1/story-runs/{a}/cancel")
    assert not paths_overlap("/v1/story-runs/active/current", "/v1/story-runs/{a}/cancel")


def test_helper_reports_a_real_router_on_the_upload_session_path():
    real = _router(
        ("POST", "/v1/upload-sessions"),
        ("PUT", "/v1/upload-sessions/{session_id}/parts/{part_number}"),
        ("GET", "/v1/other"),
    )
    demo = _router(
        ("POST", "/v1/upload-sessions"),
        ("PUT", "/v1/upload-sessions/{upload_ref}/parts/{part_no}"),
        ("DELETE", "/v1/upload-sessions/{upload_ref}"),
    )
    replacement = shadowed_routes(real.routes, demo.routes)
    assert replacement.collides == (
        "POST /v1/upload-sessions",
        "PUT /v1/upload-sessions/{session_id}/parts/{part_number}",
    )
    assert len(replacement.unmounted) == 3
    assert replacement.replaces_real_routes


def test_helper_does_not_report_other_methods_or_paths():
    real = _router(("GET", "/v1/story-runs"), ("POST", "/v1/elsewhere"))
    demo = _router(("POST", "/v1/story-runs"))
    replacement = shadowed_routes(real.routes, demo.routes)
    assert replacement.collides == ()
    assert len(replacement.unmounted) == 2


def test_read_acknowledgement_accepts_only_zero_or_one():
    assert read_replacement_acknowledgement({}) is False
    assert read_replacement_acknowledgement({ACKNOWLEDGEMENT_ENV: "0"}) is False
    assert read_replacement_acknowledgement({ACKNOWLEDGEMENT_ENV: "1"}) is True
    with pytest.raises(ValueError):
        read_replacement_acknowledgement({ACKNOWLEDGEMENT_ENV: "yes"})


def test_registry_matches_what_the_mount_flag_leaves_out(monkeypatch):
    """`story_demo_replaced_routers()` and `include_parent_story_runs` must agree."""
    registry = {
        label
        for router in story_demo_replaced_routers()
        for label in route_labels(router.routes)
    }
    demo_owned = set(route_labels(story_run_lite_router.routes))
    monkeypatch.setenv(FLAG, "0")
    assert registry <= _app_route_labels(create_app())  # mounted when the demo is off
    monkeypatch.setenv(FLAG, "1")
    monkeypatch.setenv(ACKNOWLEDGEMENT_ENV, "1")
    # With the demo on, only a label that the demo router itself serves may remain.
    assert (registry & _app_route_labels(create_app())) <= demo_owned
