"""FEAT-066 T-4a1: every StoryRun route has an explicit actor decision (inventory, not a hand list).

The test walks the routes the real application mounts under ``/v1/story-runs`` and compares them
with the declared decisions. A route that has no decision fails the test, and a decision whose
route is gone fails too, so a route added by a later task cannot silently be Parent-only or
silently open to a Teacher. The decision is also checked in the handler source: a Teacher-guarded
handler resolves ``require_story_run_actor`` and never ``_require_parent``; every other handler
keeps ``_require_parent`` (a Teacher gets the uniform 404 there).

Decisions (plan T-4a1, Draft 2 re-baselined on the committed tree after T-1a..T-1d1-fix):

* TEACHER_GUARDED: the actor of a run may be the Parent owner or the Teacher currently assigned to
  the child's class (SRS l.553, l.1664-1676).
* PARENT_ONLY: no Teacher creation path exists before T-4b2; the Teacher gets the uniform 404.
* HANDED_OVER: the route keeps the Parent guard NOW and is handed over to T-4b2 (Teacher run
  creation with the occurrence and plan pins, the Teacher lock, the Teacher producers) and T-5a
  (video quota and playback of the sample). OWNER-VISIBLE deviation from the program task row of
  T-4a1 (coordinator ruling on review finding T4A1-I-01): nothing is reachable meanwhile, because
  no Teacher can create a run before T-4b2. The Teacher gets the uniform 404.
"""

from __future__ import annotations

import inspect
from collections.abc import Iterator
from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from fastapi.routing import APIRoute
from fastapi.testclient import TestClient

import sketch2life.infrastructure.uploads.resolvers as resolvers_module
import sketch2life.interfaces.http.app as app_module
import sketch2life.interfaces.http.be1_runtime as runtime_module
from sketch2life.infrastructure.config.settings import (
    CoreDatabaseSettings,
    Settings,
    get_core_database_settings,
    get_settings,
)
from sketch2life.infrastructure.story_video import job_projection

TEACHER_GUARDED = "TEACHER_GUARDED"
PARENT_ONLY = "PARENT_ONLY"
HANDED_OVER = "PARENT_GUARD_NOW_HANDED_OVER_TO_T-4b2/T-5a"

DECISIONS: dict[tuple[str, str], str] = {
    ("GET", "/v1/story-runs/{run_id}"): TEACHER_GUARDED,
    ("POST", "/v1/story-runs/{run_id}/context-confirmation"): TEACHER_GUARDED,
    ("POST", "/v1/story-runs/{run_id}/subject-confirmation"): TEACHER_GUARDED,
    ("POST", "/v1/story-runs/{run_id}/script-confirmation"): TEACHER_GUARDED,
    # create, list and the active run: no Teacher creation path before T-4b2
    ("POST", "/v1/story-runs"): PARENT_ONLY,
    ("GET", "/v1/story-runs"): PARENT_ONLY,
    ("GET", "/v1/story-runs/active/current"): PARENT_ONLY,
    # cancel and delete: the Parent owner or the current class Teacher (T-13a, FR-C-08)
    ("POST", "/v1/story-runs/{run_id}/cancel"): TEACHER_GUARDED,
    ("DELETE", "/v1/story-runs/{run_id}"): TEACHER_GUARDED,
    # inputs: the artwork resolver and writer stay Parent-scoped (D10); the idea, the transcript
    # and the rewrite run on Parent-scoped job ports: handed over to T-4b2
    ("POST", "/v1/story-runs/{run_id}/assets"): HANDED_OVER,
    ("POST", "/v1/story-runs/{run_id}/idea"): HANDED_OVER,
    ("GET", "/v1/story-runs/{run_id}/transcript"): HANDED_OVER,
    ("POST", "/v1/story-runs/{run_id}/transcript-confirmation"): HANDED_OVER,
    ("POST", "/v1/story-runs/{run_id}/story-rewrites"): HANDED_OVER,
    # video: admission needs the quota and the Teacher lock (T-5a, T-4b2); the decisions on a ready
    # video release the lock (T-4b2); the playback token and the stream bind the Parent owner
    # scope (T-5a plays the sample)
    ("POST", "/v1/story-runs/{run_id}/video-generations"): HANDED_OVER,
    ("POST", "/v1/story-runs/{run_id}/video-unsuitable"): HANDED_OVER,
    ("POST", "/v1/story-runs/{run_id}/complete"): HANDED_OVER,
    ("POST", "/v1/story-runs/{run_id}/playback-token"): HANDED_OVER,
    ("GET", "/v1/story-runs/{run_id}/playback"): HANDED_OVER,
}

# The ten routes handed over to the named tasks (coordinator ruling on T4A1-I-01).
HANDED_OVER_TO: dict[tuple[str, str], str] = {
    ("POST", "/v1/story-runs/{run_id}/assets"): "T-4b2",
    ("POST", "/v1/story-runs/{run_id}/idea"): "T-4b2",
    ("GET", "/v1/story-runs/{run_id}/transcript"): "T-4b2",
    ("POST", "/v1/story-runs/{run_id}/transcript-confirmation"): "T-4b2",
    ("POST", "/v1/story-runs/{run_id}/story-rewrites"): "T-4b2",
    ("POST", "/v1/story-runs/{run_id}/video-generations"): "T-4b2/T-5a",
    ("POST", "/v1/story-runs/{run_id}/video-unsuitable"): "T-4b2",
    ("POST", "/v1/story-runs/{run_id}/complete"): "T-4b2",
    ("POST", "/v1/story-runs/{run_id}/playback-token"): "T-4b2/T-5a",
    ("GET", "/v1/story-runs/{run_id}/playback"): "T-5a",
}


def _story_run_routes(application: FastAPI) -> list[APIRoute]:
    """Every ``/v1/story-runs`` route (FastAPI wraps an included router: its routes carry the
    full prefix)."""

    found: list[APIRoute] = []
    for route in application.routes:
        original = getattr(route, "original_router", None)
        for candidate in original.routes if original is not None else [route]:
            if isinstance(candidate, APIRoute) and candidate.path.startswith("/v1/story-runs"):
                found.append(candidate)
    return found


@pytest.fixture
def mounted_routes(monkeypatch: pytest.MonkeyPatch) -> Iterator[list[APIRoute]]:
    monkeypatch.setitem(Settings.model_config, "env_file", None)
    monkeypatch.setitem(CoreDatabaseSettings.model_config, "env_file", None)
    monkeypatch.setenv("STORYRUN_LITE_MAIN_DEMO_ENABLED", "0")
    settings = Settings(
        env="test",
        auth_provider="firebase",
        firebase_project_id="synthetic-t4a1-project",
        _env_file=None,  # type: ignore[call-arg]
    )
    monkeypatch.setattr(app_module, "get_settings", lambda: settings)
    monkeypatch.setattr(
        runtime_module, "get_core_database_settings", lambda: SimpleNamespace(database_url=None)
    )
    get_settings.cache_clear()
    get_core_database_settings.cache_clear()
    try:
        application = app_module.create_app()
        with TestClient(application, raise_server_exceptions=False):
            yield _story_run_routes(application)
    finally:
        get_settings.cache_clear()
        get_core_database_settings.cache_clear()


def _operations(routes: list[APIRoute]) -> dict[tuple[str, str], APIRoute]:
    return {
        (method, route.path): route
        for route in routes
        for method in sorted((route.methods or set()) - {"HEAD", "OPTIONS"})
    }


def test_every_mounted_story_run_route_has_a_declared_decision(
    mounted_routes: list[APIRoute],
) -> None:
    mounted = set(_operations(mounted_routes))
    assert mounted - set(DECISIONS) == set(), "a new StoryRun route needs an actor decision"
    assert set(DECISIONS) - mounted == set(), "a declared decision has no route"


def test_the_handler_of_each_route_uses_the_guard_its_decision_names(
    mounted_routes: list[APIRoute],
) -> None:
    for operation, route in _operations(mounted_routes).items():
        source = inspect.getsource(route.endpoint)
        decision = DECISIONS[operation]
        if decision == TEACHER_GUARDED:
            assert "require_story_run_actor(" in source, operation
            assert "_require_parent(" not in source, operation
        else:
            assert "_require_parent(" in source, operation
            assert "require_story_run_actor(" not in source, operation


def test_every_handed_over_route_names_the_task_that_takes_it() -> None:
    handed = {operation for operation, decision in DECISIONS.items() if decision == HANDED_OVER}
    assert handed == set(HANDED_OVER_TO)
    assert all(owner.startswith(("T-4b2", "T-5a")) for owner in HANDED_OVER_TO.values())


def test_the_route_table_is_the_expected_size(mounted_routes: list[APIRoute]) -> None:
    # No route was added or removed by T-4a1 (plan section 3): 19 operations at the tip.
    assert len(_operations(mounted_routes)) == len(DECISIONS) == 19


def test_the_upload_resolver_and_the_job_projection_stay_parent_scoped() -> None:
    """Plan D10: the artwork resolver, the artwork writer and ``/v1/jobs`` stay fail-closed."""

    resolver_source = inspect.getsource(resolvers_module.ParentRunArtworkResolver.resolve)
    assert "PARENT_ACCOUNT_SCOPE" in resolver_source
    assert 'f"parent/{canonical}/"' in resolver_source
    assert "ORGANIZATION" not in resolver_source
    jobs_source = inspect.getsource(job_projection.SqlParentVideoJobs.owned_job)
    assert '_RUNS.c.actor_scope_kind == "PARENT_ACCOUNT"' in jobs_source
    assert "ORGANIZATION" not in jobs_source
