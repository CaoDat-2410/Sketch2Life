"""FEAT-066 T-4a1: every StoryRun route has an explicit actor decision (inventory, not a hand list).

The test walks the routes the real application mounts under ``/v1/story-runs`` and compares them
with the declared decisions. A route that has no decision fails the test, and a decision whose
route is gone fails too, so a route added by a later task cannot silently be Parent-only or
silently open to a Teacher. The decision is also checked in the handler source: a Teacher-guarded
handler resolves ``require_story_run_actor`` and never ``_require_parent``; every other handler
keeps ``_require_parent`` (a Teacher gets the uniform 404 there).

Decisions (plan T-4a1, Draft 2 re-baselined on the committed tree after T-1a..T-1d1-fix):

* TEACHER_GUARDED: the actor of a run may be the Parent owner or the Teacher currently assigned to
  the child's class (SRS l.553, l.1664-1676); a run with an occurrence pin follows the pin (T-4b2).
* TEACHER_DISPATCHED (T-4b2): ``POST /v1/story-runs`` is one route with two bodies. The route class
  hands a Teacher-shaped body from an active Teacher to a Teacher endpoint; every other request is
  answered by the unchanged Parent handler, which keeps its ``_require_parent`` guard.
* PARENT_ONLY: the history list has no Teacher meaning in v3 (a Teacher finds a run through the
  occurrence and the active-run read); the Teacher gets the uniform 404.
* HANDED_OVER: no route is handed over any more. T-4b3b (the Teacher video routes and the owner-view
  playback: coordinator ruling OPEN-1) moved the five video routes to ``TEACHER_GUARDED``, so
  ``HANDED_OVER`` and ``HANDED_OVER_TO`` are empty (T-5a adds the projection routes and the
  sample claim, not these five).
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
from sketch2life.interfaces.http.routers import story_run_create_dispatch as dispatch_module

TEACHER_GUARDED = "TEACHER_GUARDED"
TEACHER_DISPATCHED = "TEACHER_DISPATCHED"
PARENT_ONLY = "PARENT_ONLY"
HANDED_OVER = "PARENT_GUARD_NOW_HANDED_OVER"

DECISIONS: dict[tuple[str, str], str] = {
    ("GET", "/v1/story-runs/{run_id}"): TEACHER_GUARDED,
    ("POST", "/v1/story-runs/{run_id}/context-confirmation"): TEACHER_GUARDED,
    ("POST", "/v1/story-runs/{run_id}/subject-confirmation"): TEACHER_GUARDED,
    ("POST", "/v1/story-runs/{run_id}/script-confirmation"): TEACHER_GUARDED,
    # create: one route, two bodies (T-4b2 D1); the history list stays Parent-only; the active run
    # is the Parent's or the one run a Teacher holds through the Teacher lock
    ("POST", "/v1/story-runs"): TEACHER_DISPATCHED,
    ("GET", "/v1/story-runs"): PARENT_ONLY,
    ("GET", "/v1/story-runs/active/current"): TEACHER_GUARDED,
    # cancel and delete: the Parent owner or the current class Teacher (T-13a, FR-C-08)
    ("POST", "/v1/story-runs/{run_id}/cancel"): TEACHER_GUARDED,
    ("DELETE", "/v1/story-runs/{run_id}"): TEACHER_GUARDED,
    # inputs (T-4b3a): the five input routes admit the Teacher of a PINNED run; the repository
    # carries the actor, the upload resolvers dispatch on the role and the producers run
    # job-side (a fixture run without an occurrence pin stays the uniform 404)
    ("POST", "/v1/story-runs/{run_id}/assets"): TEACHER_GUARDED,
    ("POST", "/v1/story-runs/{run_id}/idea"): TEACHER_GUARDED,
    ("GET", "/v1/story-runs/{run_id}/transcript"): TEACHER_GUARDED,
    ("POST", "/v1/story-runs/{run_id}/transcript-confirmation"): TEACHER_GUARDED,
    ("POST", "/v1/story-runs/{run_id}/story-rewrites"): TEACHER_GUARDED,
    # video (T-4b3b): the request goes through the local/test adapter pair only (no quota, billing
    # or capacity code), the two decisions on a ready video release the Teacher lock, and the
    # owner-view token and stream bind the digest of the calling Teacher (coordinator ruling
    # OPEN-1: T-5a rebases on this)
    ("POST", "/v1/story-runs/{run_id}/video-generations"): TEACHER_GUARDED,
    ("POST", "/v1/story-runs/{run_id}/video-unsuitable"): TEACHER_GUARDED,
    ("POST", "/v1/story-runs/{run_id}/complete"): TEACHER_GUARDED,
    ("POST", "/v1/story-runs/{run_id}/playback-token"): TEACHER_GUARDED,
    ("GET", "/v1/story-runs/{run_id}/playback"): TEACHER_GUARDED,
}

# No route is handed over any more (T-4b3b emptied the table).
HANDED_OVER_TO: dict[tuple[str, str], str] = {}


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
        elif decision == TEACHER_DISPATCHED:
            # the unchanged Parent handler keeps its guard; the route class carries the Teacher
            # endpoint, which answers only an active Teacher and steps aside for everyone else
            assert "_require_parent(" in source, operation
            assert isinstance(route, dispatch_module.RoleDispatchedCreateRoute), operation
            teacher_source = inspect.getsource(route._teacher_route.endpoint)
            assert 'identity.account_role != "teacher"' in teacher_source, operation
            assert "_FallThroughToParent" in teacher_source, operation
            assert "_require_parent(" not in teacher_source, operation
        else:
            assert "_require_parent(" in source, operation
            assert "require_story_run_actor(" not in source, operation


def test_no_route_is_handed_over_any_more() -> None:
    handed = {operation for operation, decision in DECISIONS.items() if decision == HANDED_OVER}
    assert handed == set(HANDED_OVER_TO) == set()


def test_the_route_table_is_the_expected_size(mounted_routes: list[APIRoute]) -> None:
    # No route was added or removed by T-4a1, T-4b2 or T-4b3b (plan section 3): 19 operations.
    assert len(_operations(mounted_routes)) == len(DECISIONS) == 19


def test_the_parent_resolver_stays_parent_scoped_and_each_job_port_has_its_own_owner() -> None:
    """T-4b3a D4: the Parent resolver is unchanged (a Teacher gets the role-dispatched resolver
    on a pinned run). T-4b3b D14: the Parent job port stays Parent-scoped; the Teacher job port
    is a separate class behind the shared occurrence-pin predicate."""

    resolver_source = inspect.getsource(resolvers_module.ParentRunArtworkResolver.resolve)
    assert "PARENT_ACCOUNT_SCOPE" in resolver_source
    assert 'f"parent/{canonical}/"' in resolver_source
    assert "ORGANIZATION" not in resolver_source
    factories = resolvers_module.default_resolver_factories()
    assert factories["RUN_ARTWORK"] is resolvers_module.RunArtworkResolver
    assert factories["RUN_AUDIO"] is resolvers_module.RunAudioResolver
    teacher_source = inspect.getsource(resolvers_module.RunArtworkResolver.resolve)
    assert "occurrence_ref.is_not(None)" in teacher_source
    assert "owner_scope_ref=organization_id" in teacher_source
    assert 'object_prefix=f"parent/{canonical}/"' in teacher_source
    jobs_source = inspect.getsource(job_projection.SqlParentVideoJobs.owned_job)
    assert '_RUNS.c.actor_scope_kind == "PARENT_ACCOUNT"' in jobs_source
    assert "ORGANIZATION" not in jobs_source
    teacher_jobs_source = inspect.getsource(job_projection.SqlTeacherVideoJobs.owned_job)
    assert "occurrence_pin_select(" in teacher_jobs_source
    assert "PARENT_ACCOUNT" not in teacher_jobs_source
