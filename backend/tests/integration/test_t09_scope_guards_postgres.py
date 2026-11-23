"""FEAT-066 T0.9: scope-guard uniformity on PostgreSQL (SRS l.864-865, C-D4, OD-18b).

Runs only against a disposable database whose name contains ``be1_acceptance``. Real identity and
assignment rows; the principal is a synthetic header. One route per family: Teacher AI (organization
scope), Parent profiles and Parent StoryRuns (account role).
"""

from __future__ import annotations

import os
from collections.abc import Iterator
from dataclasses import dataclass
from typing import Any
from uuid import uuid4

import pytest
from fastapi import FastAPI, Header
from fastapi.testclient import TestClient

from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.infrastructure.config.settings import get_core_database_settings, get_settings
from sketch2life.infrastructure.persistence.be1_models import (
    AdultIdentityModel,
    ClassroomModel,
    OrganizationAssignmentModel,
    OrganizationModel,
)
from sketch2life.interfaces.http.app import create_app
from sketch2life.interfaces.http.be1_runtime import get_verified_adult
from sketch2life.interfaces.http.parent_runtime import get_parent_principal

ISSUER = "synthetic-t09-issuer"
OTHER_ISSUER = "synthetic-t09-other-issuer"
VOLATILE_KEYS = {"request_id", "correlation_id"}
TEACHER_AI_BODY = {
    "topic": "Butterfly",
    "target_age_months": 72,
    "objectives": ["Draw wings"],
    "drawing_subject": "butterfly",
    "activity_count": 1,
    "activity_kind": "indoor",
}


@dataclass
class T09Api:
    app: FastAPI
    client: TestClient
    organization_id: str
    other_organization_id: str
    users: dict[str, str]

    def session(self) -> Any:
        return self.app.state.be1_runtime.session_factory

    def headers(self, user: str) -> dict[str, str]:
        return {"X-Test-Principal": self.users[user], "X-Request-ID": f"t09-{user}"}


@pytest.fixture
def t09_api(monkeypatch: pytest.MonkeyPatch) -> Iterator[T09Api]:
    database_url = os.environ.get("BE1_TEST_DATABASE_URL")
    if not database_url:
        pytest.skip("set BE1_TEST_DATABASE_URL to a disposable PostgreSQL database")
    if "be1_acceptance" not in database_url.rsplit("/", 1)[-1]:
        pytest.fail("BE1_TEST_DATABASE_URL must point to a disposable *be1_acceptance database")
    monkeypatch.setenv("SKETCH2LIFE_DATABASE_URL", database_url)
    monkeypatch.setenv("SKETCH2LIFE_ENV", "test")
    monkeypatch.setenv("SKETCH2LIFE_AUTH_PROVIDER", "development")
    monkeypatch.setenv("SKETCH2LIFE_AI_PROVIDER", "disabled")
    get_settings.cache_clear()
    get_core_database_settings.cache_clear()
    app = create_app()
    runtime = app.state.be1_runtime
    if runtime.engine is None or runtime.session_factory is None:
        pytest.fail("PostgreSQL runtime did not initialize")
    token = uuid4().hex[:8]
    organization_id = f"synthetic-t09-org-{token}"
    other_organization_id = f"synthetic-t09-other-{token}"
    class_id = f"synthetic-t09-class-{token}"
    users = {
        name: f"synthetic-t09-{name}-{token}"
        for name in (
            "parent",
            "inactive_parent",
            "issuer_mismatch_parent",
            "teacher_class",
            "teacher_org",
            "teacher_guide",
            "teacher_unassigned",
            "teacher_other_org",
            "manager",
            "platform_admin",
            "stranger",
        )
    }
    accounts = {
        "parent": ("parent", "active"),
        "inactive_parent": ("parent", "disabled"),
        "issuer_mismatch_parent": ("parent", "active"),
        "teacher_class": ("teacher", "active"),
        "teacher_org": ("teacher", "active"),
        "teacher_guide": ("teacher", "active"),
        "teacher_unassigned": ("teacher", "active"),
        "teacher_other_org": ("teacher", "active"),
        "manager": ("school_manager", "active"),
        "platform_admin": ("platform_admin", "active"),
    }
    rows = (
        ("teacher_class", organization_id, class_id, "teacher"),
        ("teacher_org", organization_id, None, "teacher"),
        ("teacher_guide", organization_id, None, "guide"),
        ("teacher_other_org", other_organization_id, None, "teacher"),
        ("manager", organization_id, None, "school_admin"),
    )
    with runtime.session_factory.begin() as db:
        for org in (organization_id, other_organization_id):
            db.add(
                OrganizationModel(
                    organization_id=org, display_name=f"Synthetic {org}", state="active"
                )
            )
        for name, (role, state) in accounts.items():
            db.add(
                AdultIdentityModel(
                    subject=users[name],
                    issuer=OTHER_ISSUER if name == "issuer_mismatch_parent" else ISSUER,
                    state=state,
                    account_role=role,
                )
            )
        db.flush()
        db.add(
            ClassroomModel(
                class_id=class_id,
                organization_id=organization_id,
                display_name="Synthetic class",
                state="active",
                created_by=users["manager"],
            )
        )
        db.flush()
        for name, org, assigned_class, role in rows:
            db.add(
                OrganizationAssignmentModel(
                    assignment_id=str(uuid4()),
                    organization_id=org,
                    subject=users[name],
                    class_id=assigned_class,
                    role=role,
                    active=True,
                )
            )

    async def verified(
        x_test_principal: str = Header(alias="X-Test-Principal"),
    ) -> VerifiedPrincipal:
        return VerifiedPrincipal(subject=x_test_principal, issuer=ISSUER, roles=frozenset())

    app.dependency_overrides[get_verified_adult] = verified
    app.dependency_overrides[get_parent_principal] = verified
    try:
        with TestClient(app) as client:
            yield T09Api(app, client, organization_id, other_organization_id, users)
    finally:
        app.dependency_overrides.clear()
        runtime.engine.dispose()
        get_settings.cache_clear()
        get_core_database_settings.cache_clear()


def _wire(response: Any) -> tuple[int, dict[str, Any]]:
    body = response.json()
    return response.status_code, {k: v for k, v in body.items() if k not in VOLATILE_KEYS}


def _teacher_ai(api: T09Api, user: str, organization_id: str | None = None) -> Any:
    return api.client.post(
        f"/api/teacher/v1/organizations/{organization_id or api.organization_id}"
        "/ai/lesson-plan-suggestions",
        headers=api.headers(user),
        json=TEACHER_AI_BODY,
    )


def test_teacher_ai_out_of_scope_callers_get_the_same_404(t09_api: T09Api) -> None:
    api = t09_api
    reference = _teacher_ai(api, "teacher_unassigned")
    assert reference.status_code == 404, reference.text
    assert reference.json()["code"] == "RESOURCE_NOT_FOUND"
    for user in (
        "parent",
        "inactive_parent",
        "issuer_mismatch_parent",
        "platform_admin",
        "stranger",
        "teacher_other_org",
    ):
        response = _teacher_ai(api, user)
        assert _wire(response) == _wire(reference), (user, response.text)
    unknown_org = _teacher_ai(api, "teacher_class", "synthetic-t09-no-such-organization")
    assert _wire(unknown_org) == _wire(reference), unknown_org.text


def test_teacher_ai_role_refusal_inside_the_organization_is_403(t09_api: T09Api) -> None:
    api = t09_api
    for user in ("manager", "teacher_guide"):
        response = _teacher_ai(api, user)
        assert response.status_code == 403, (user, response.text)
        assert response.json()["code"] == "ACTION_NOT_ALLOWED"


def test_teacher_ai_assigned_teacher_reaches_the_provider_gate(t09_api: T09Api) -> None:
    api = t09_api
    for user in ("teacher_class", "teacher_org"):
        response = _teacher_ai(api, user)
        assert response.status_code == 503, (user, response.text)
        assert response.json()["code"] == "MODAL_AI_NOT_ENABLED"


def test_parent_profile_list_wrong_role_is_404_and_parent_is_200(t09_api: T09Api) -> None:
    api = t09_api
    allowed = api.client.get("/v1/parent/profiles", headers=api.headers("parent"))
    assert allowed.status_code == 200, allowed.text
    reference = None
    for user in (
        "teacher_class",
        "manager",
        "inactive_parent",
        "issuer_mismatch_parent",
        "platform_admin",
        "stranger",
    ):
        response = api.client.get("/v1/parent/profiles", headers=api.headers(user))
        assert response.status_code == 404, (user, response.text)
        assert response.json()["code"] == "PROFILE_NOT_FOUND"
        reference = reference or _wire(response)
        assert _wire(response) == reference


def test_story_run_routes_wrong_role_is_404_and_parent_is_200(t09_api: T09Api) -> None:
    api = t09_api
    allowed = api.client.get("/v1/story-runs", headers=api.headers("parent"))
    assert allowed.status_code == 200, allowed.text
    unknown_run = api.client.get(f"/v1/story-runs/{uuid4()}", headers=api.headers("parent"))
    assert unknown_run.status_code == 404 and unknown_run.json()["code"] == "RESOURCE_NOT_FOUND"
    for user in (
        "teacher_class",
        "manager",
        "inactive_parent",
        "issuer_mismatch_parent",
        "platform_admin",
        "stranger",
    ):
        paths = ("/v1/story-runs", "/v1/story-runs/active/current", f"/v1/story-runs/{uuid4()}")
        if user == "teacher_class":
            # T-4b2: the class Teacher reads its own active run (the Teacher lock): an empty answer
            # when it holds none; the history list and an unknown run stay the uniform 404
            active = api.client.get("/v1/story-runs/active/current", headers=api.headers(user))
            assert active.status_code == 200 and active.json()["story_run"] is None, active.text
            paths = tuple(path for path in paths if path != "/v1/story-runs/active/current")
        for path in paths:
            response = api.client.get(path, headers=api.headers(user))
            assert response.status_code == 404, (user, path, response.text)
            assert _wire(response) == _wire(unknown_run), (user, path, response.text)
