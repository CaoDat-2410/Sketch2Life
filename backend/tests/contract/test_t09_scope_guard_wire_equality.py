"""FEAT-066 T0.9: a wrong-role caller and an unknown resource look the same on the wire.

SRS l.864-865 (§9.8): 403 only when the resource is known to be in the caller's scope; one 404
shape for an unknown id and an out-of-scope resource. These tests go through the real app (the
real exception handlers and envelopes) with fake stores, and compare the full response body field
by field, ignoring only the per-request ``request_id`` and ``correlation_id``.

Families covered: Teacher AI, Parent profiles, Parent StoryRuns, and the F-1 regression on the
BE1 pilot-profile lookup (an unknown session and a session the caller has no assignment for).
"""

from __future__ import annotations

from collections.abc import Iterator
from types import SimpleNamespace
from typing import Any, NoReturn

import pytest
from fastapi.testclient import TestClient

import sketch2life.interfaces.http.app as app_module
import sketch2life.interfaces.http.be1_runtime as runtime_module
import sketch2life.interfaces.http.routers.parent_story_runs as story_routes
from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.application.ports.parent_story_runs import ParentStoryRunError
from sketch2life.domain.parent_profiles import ParentProfileError
from sketch2life.infrastructure.config.settings import (
    CoreDatabaseSettings,
    Settings,
    get_core_database_settings,
    get_settings,
)
from sketch2life.interfaces.http.be1_runtime import get_db, get_runtime, get_verified_adult
from sketch2life.interfaces.http.parent_runtime import (
    get_parent_principal,
    get_parent_profile_service,
    get_parent_role_reader,
)

ISSUER = "issuer-1"
PRINCIPAL = VerifiedPrincipal("adult-1", ISSUER, frozenset())
ORG = "org-1"
RUN_ID = "22222222-2222-4222-8222-222222222222"
PROFILE_ID = "11111111-1111-4111-8111-111111111111"
UNKNOWN_ID = "00000000-0000-0000-0000-000000000000"
VOLATILE_KEYS = {"request_id", "correlation_id"}

TEACHER_LESSON_BODY = {
    "topic": "Butterfly",
    "target_age_months": 72,
    "objectives": ["Draw wings"],
    "drawing_subject": "butterfly",
    "activity_count": 1,
    "activity_kind": "indoor",
}
TEACHER_PLAN_BODY = {
    "review_confirmed": True,
    "plan_revision_ref": "plan-1",
    "topic": "Butterfly",
    "target_age_months": 72,
    "objectives": ["Draw wings"],
    "drawing_steps": [
        {"action": f"Step {index}", "placement": "centre"} for index in range(1, 4)
    ],
    "subject_knowledge": ["Butterflies have four wings"],
    "activities": [
        {
            "activity_ref": "activity-1",
            "title": "Colour wings",
            "goal": "Colour",
            "materials": "Crayons",
            "preparation": "None",
            "instructions": "Colour the wings",
            "safety_notes": "None",
        }
    ],
}
TEACHER_ROUTES = (
    ("lesson-plan-suggestions", TEACHER_LESSON_BODY),
    ("sketch-decks", TEACHER_PLAN_BODY),
    ("lesson-visuals", TEACHER_PLAN_BODY),
)


class _Scalars:
    def __init__(self, rows: list[Any]) -> None:
        self._rows = rows

    def all(self) -> list[Any]:
        return self._rows


class _Db:
    """Fake session: one identity, its assignment rows, and an optional known BE1 session."""

    def __init__(
        self,
        *,
        role: str | None,
        assignments: list[Any] | None = None,
        session: Any = None,
    ) -> None:
        self._identity = (
            None
            if role is None
            else SimpleNamespace(
                account_id="account-1", issuer=ISSUER, account_role=role, state="active"
            )
        )
        self._rows = assignments or []
        self._session = session

    def get(self, _model: object, _key: object) -> Any:
        return self._identity

    def scalars(self, _statement: object) -> _Scalars:
        return _Scalars(self._rows)

    def scalar(self, _statement: object) -> Any:
        return self._session


def _assignment(role: str) -> Any:
    return SimpleNamespace(
        organization_id=ORG,
        subject=PRINCIPAL.subject,
        class_id=None,
        role=role,
        active=True,
        assignment_id=f"assignment-{role}",
    )


class _StoryService:
    def get_run(self, **_kwargs: object) -> NoReturn:
        raise ParentStoryRunError(404, "RESOURCE_NOT_FOUND")

    def get_active_run(self, **_kwargs: object) -> None:
        return None

    def list_runs(self, **_kwargs: object) -> list[object]:
        return []

    def replay_create_run(self, **_kwargs: object) -> None:
        return None

    def create_run(self, **_kwargs: object) -> NoReturn:
        raise ParentStoryRunError(409, "ACTIVE_RUN_EXISTS")


class _ProfileService:
    def assert_profile_owned(self, **_kwargs: object) -> NoReturn:
        raise ParentProfileError(404, "PROFILE_NOT_FOUND", "Profile was not found")


class _RoleReader:
    def __init__(self, *, active: bool) -> None:
        self._active = active

    def has_active_parent_role(self, *, principal: VerifiedPrincipal) -> bool:
        del principal
        return self._active


@pytest.fixture
def app_client(monkeypatch: pytest.MonkeyPatch) -> Iterator[TestClient]:
    monkeypatch.setitem(Settings.model_config, "env_file", None)
    monkeypatch.setitem(CoreDatabaseSettings.model_config, "env_file", None)
    monkeypatch.setenv("STORYRUN_LITE_MAIN_DEMO_ENABLED", "0")
    settings = Settings(
        env="test",
        auth_provider="firebase",
        firebase_project_id="synthetic-t09-project",
        _env_file=None,  # type: ignore[call-arg]
    )
    monkeypatch.setattr(app_module, "get_settings", lambda: settings)
    monkeypatch.setattr(
        runtime_module,
        "get_core_database_settings",
        lambda: SimpleNamespace(database_url=None),
    )
    monkeypatch.setattr(story_routes, "_service", lambda _db: _StoryService())
    application = app_module.create_app()
    application.dependency_overrides[get_verified_adult] = lambda: PRINCIPAL
    application.dependency_overrides[get_parent_principal] = lambda: PRINCIPAL
    application.dependency_overrides[get_parent_profile_service] = lambda: _ProfileService()
    application.dependency_overrides[get_runtime] = lambda: SimpleNamespace(
        settings=SimpleNamespace(env="test", synthetic_pilot_enabled=True)
    )
    get_settings.cache_clear()
    get_core_database_settings.cache_clear()
    try:
        with TestClient(application, raise_server_exceptions=False) as client:
            yield client
    finally:
        application.dependency_overrides.clear()
        get_settings.cache_clear()
        get_core_database_settings.cache_clear()


def _use(client: TestClient, db: _Db, *, parent_role_active: bool = True) -> None:
    overrides = client.app.dependency_overrides  # type: ignore[attr-defined]
    overrides[get_db] = lambda: db
    overrides[get_parent_role_reader] = lambda: _RoleReader(active=parent_role_active)


def _wire(response: Any) -> tuple[int, dict[str, Any]]:
    body = response.json()
    assert isinstance(body, dict)
    return response.status_code, {k: v for k, v in body.items() if k not in VOLATILE_KEYS}


def _same(left: Any, right: Any, *, status: int, code: str) -> None:
    assert _wire(left) == _wire(right), (left.text, right.text)
    assert left.status_code == status
    assert left.json()["code"] == code


# --- Teacher AI -----------------------------------------------------------------------------


@pytest.mark.parametrize(("route", "body"), TEACHER_ROUTES)
def test_teacher_ai_wrong_role_equals_unassigned_teacher(
    app_client: TestClient, route: str, body: dict[str, Any]
) -> None:
    url = f"/api/teacher/v1/organizations/{ORG}/ai/{route}"
    # A Teacher with no active row in the organization (an unknown organization looks the same).
    _use(app_client, _Db(role="teacher", assignments=[]))
    unassigned = app_client.post(url, json=body)
    assert unassigned.status_code == 404
    for role in ("parent", "platform_admin"):
        _use(app_client, _Db(role=role, assignments=[_assignment("teacher")]))
        wrong_role = app_client.post(url, json=body)
        _same(wrong_role, unassigned, status=404, code="RESOURCE_NOT_FOUND")
    _use(app_client, _Db(role=None))
    no_identity = app_client.post(url, json=body)
    _same(no_identity, unassigned, status=404, code="RESOURCE_NOT_FOUND")


@pytest.mark.parametrize(("route", "body"), TEACHER_ROUTES)
def test_teacher_ai_assigned_non_teacher_roles_are_403(
    app_client: TestClient, route: str, body: dict[str, Any]
) -> None:
    url = f"/api/teacher/v1/organizations/{ORG}/ai/{route}"
    for role, rows in (
        ("school_manager", [_assignment("school_admin")]),
        ("teacher", [_assignment("guide")]),
        ("teacher", [_assignment("observer")]),
    ):
        _use(app_client, _Db(role=role, assignments=rows))
        response = app_client.post(url, json=body)
        assert response.status_code == 403, response.text
        assert response.json()["code"] == "ACTION_NOT_ALLOWED"


@pytest.mark.parametrize(("route", "body"), TEACHER_ROUTES)
def test_teacher_ai_invalid_body_is_400_before_the_guard(
    app_client: TestClient, route: str, body: dict[str, Any]
) -> None:
    # FastAPI validates the body first, so the 400 does not depend on the caller's scope.
    _use(app_client, _Db(role="parent"))
    response = app_client.post(
        f"/api/teacher/v1/organizations/{ORG}/ai/{route}", json={"unexpected": True}
    )
    assert response.status_code == 400, response.text


# --- Parent profiles ------------------------------------------------------------------------


def test_parent_profile_wrong_role_equals_unknown_profile(app_client: TestClient) -> None:
    headers = {"X-Request-ID": "t09-profile"}
    _use(app_client, _Db(role="parent"), parent_role_active=True)
    unknown = app_client.get(f"/v1/parent/profiles/{UNKNOWN_ID}", headers=headers)
    assert unknown.status_code == 404 and unknown.json()["code"] == "PROFILE_NOT_FOUND"

    # The ownership check runs first and answers 404 for a profile the caller cannot own; to
    # reach the role check the fake service must accept the id.
    application = app_client.app
    application.dependency_overrides[get_parent_profile_service] = (  # type: ignore[attr-defined]
        lambda: SimpleNamespace(assert_profile_owned=lambda **_kwargs: None)
    )
    _use(app_client, _Db(role="teacher"), parent_role_active=False)
    for method, path in (
        ("GET", f"/v1/parent/profiles/{PROFILE_ID}"),
        ("PATCH", f"/v1/parent/profiles/{PROFILE_ID}"),
        ("DELETE", f"/v1/parent/profiles/{PROFILE_ID}"),
        ("GET", "/v1/parent/profiles"),
        ("POST", "/v1/parent/profiles"),
    ):
        wrong_role = app_client.request(method, path, headers=headers, content="{")
        _same(wrong_role, unknown, status=404, code="PROFILE_NOT_FOUND")


# --- Parent StoryRuns -----------------------------------------------------------------------


def test_story_run_wrong_role_equals_unknown_run(app_client: TestClient) -> None:
    headers = {"X-Request-ID": "t09-story"}
    _use(app_client, _Db(role="parent"))
    unknown = app_client.get(f"/v1/story-runs/{UNKNOWN_ID}", headers=headers)
    assert unknown.status_code == 404 and unknown.json()["code"] == "RESOURCE_NOT_FOUND"

    for role in ("teacher", "school_manager", "platform_admin"):
        _use(app_client, _Db(role=role))
        for method, path, extra in (
            ("GET", f"/v1/story-runs/{RUN_ID}", {}),
            ("GET", "/v1/story-runs", {}),
            ("GET", "/v1/story-runs/active/current", {}),
            ("DELETE", f"/v1/story-runs/{RUN_ID}", {"Idempotency-Key": "t09-key-1"}),
        ):
            wrong_role = app_client.request(method, path, headers={**headers, **extra})
            _same(wrong_role, unknown, status=404, code="RESOURCE_NOT_FOUND")
        created = app_client.post(
            "/v1/story-runs",
            headers={**headers, "Idempotency-Key": "t09-key-2"},
            json={"parent_profile_id": PROFILE_ID},
        )
        _same(created, unknown, status=404, code="RESOURCE_NOT_FOUND")


# --- F-1 regression (BE1 pilot-profile lookup) ----------------------------------------------


def test_pilot_profiles_unknown_session_equals_session_without_assignment(
    app_client: TestClient,
) -> None:
    """``get_session`` runs before the assignment check; the wire body must not tell them apart."""
    url_unknown = f"/api/be1/v1/organizations/{ORG}/sessions/unknown-session/pilot-profiles"
    url_known = f"/api/be1/v1/organizations/{ORG}/sessions/known-session/pilot-profiles"
    known_session = SimpleNamespace(class_id="class-1", state="lobby", configuration={})

    # Caller has no assignment in the organization: unknown session id versus an existing one.
    _use(app_client, _Db(role="teacher", assignments=[], session=None))
    unknown = app_client.get(url_unknown)
    _use(app_client, _Db(role="teacher", assignments=[], session=known_session))
    foreign = app_client.get(url_known)
    _same(unknown, foreign, status=404, code="RESOURCE_NOT_FOUND")

    # A Parent account and a caller with no identity get the same body for an existing session.
    for db in (_Db(role="parent", session=known_session), _Db(role=None, session=known_session)):
        _use(app_client, db)
        _same(app_client.get(url_known), unknown, status=404, code="RESOURCE_NOT_FOUND")


# --- T-7a2: child-profile reads need the class's own Teacher row ------------------------------


def test_t7a2_child_profile_reads_403_body_is_one_shape_and_differs_from_the_404(
    app_client: TestClient,
) -> None:
    """R1 pilot-profiles, R2 roster, R3 portfolio: an in-scope caller without the class's own
    Teacher row gets the same 403 ``ACTION_NOT_ALLOWED`` body on the wire, never the uniform 404.
    """
    base = f"/api/be1/v1/organizations/{ORG}"
    urls = (
        f"{base}/sessions/known-session/pilot-profiles",
        f"{base}/sessions/known-session/roster",
        f"{base}/classes/class-1/profiles/child-1/portfolio",
    )
    known = SimpleNamespace(class_id="class-1", state="lobby", configuration={})
    uniform_404 = _wire(_pilot_404(app_client, urls[0]))
    assert uniform_404[1]["code"] == "RESOURCE_NOT_FOUND"
    forbidden: list[tuple[int, dict[str, Any]]] = []
    for role, rows in (
        ("teacher", [_assignment("teacher")]),  # org-wide `teacher` row (class_id None)
        ("teacher", [_assignment("guide")]),
        ("school_manager", [_assignment("school_admin")]),
    ):
        _use(app_client, _Db(role=role, assignments=rows, session=known))
        for url in urls:
            response = app_client.get(url)
            assert response.status_code == 403, (url, response.text)
            forbidden.append(_wire(response))
    assert all(wire == forbidden[0] for wire in forbidden)
    assert forbidden[0][1]["code"] == "ACTION_NOT_ALLOWED"
    assert forbidden[0] != uniform_404


def _pilot_404(client: TestClient, url: str) -> Any:
    _use(client, _Db(role="teacher", assignments=[], session=None))
    return client.get(url)
