"""FEAT-066 T0.2: ``GET /api/auth/v1/me`` granted scope on PostgreSQL (SRS l.794, TD-25).

Runs only against a disposable database whose name contains ``be1_acceptance``. Identities are
synthetic header principals; no network is used.
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
from sqlalchemy.orm import Session

from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.infrastructure.config.settings import get_core_database_settings, get_settings
from sketch2life.infrastructure.persistence.be1_models import (
    AdultIdentityModel,
    ClassroomModel,
    OrganizationAssignmentModel,
    OrganizationModel,
)
from sketch2life.interfaces.http.account_scope import (
    MAX_SCOPE_CLASSES,
    MAX_SCOPE_ORGANIZATIONS,
    load_granted_scope,
)
from sketch2life.interfaces.http.app import create_app
from sketch2life.interfaces.http.be1_runtime import get_verified_adult
from sketch2life.interfaces.http.routers.auth_registration import ME_SETUP_REFUSAL_STATUS

ISSUER = "synthetic-t02-issuer"
ME = "/api/auth/v1/me"


@dataclass
class T02Api:
    app: FastAPI
    client: TestClient
    token: str
    teacher: str
    manager: str
    parent: str
    platform_admin: str
    other_teacher: str
    mismatch: str
    org_a: str
    org_b: str
    org_c_suspended: str
    org_d: str

    def session(self) -> Any:
        return self.app.state.be1_runtime.session_factory

    def me(self, subject: str) -> Any:
        return self.client.get(ME, headers={"X-Test-Principal": subject})


def _assign(
    db: Session, subject: str, org: str, role: str, class_id: str | None, *, active: bool = True
) -> None:
    db.add(
        OrganizationAssignmentModel(
            assignment_id=str(uuid4()),
            organization_id=org,
            subject=subject,
            class_id=class_id,
            role=role,
            active=active,
        )
    )


def _identity(db: Session, subject: str, role: str, *, issuer: str = ISSUER) -> str:
    account_id = str(uuid4())
    db.add(
        AdultIdentityModel(
            subject=subject,
            account_id=account_id,
            issuer=issuer,
            state="active",
            account_role=role,
            role_revision=2,
        )
    )
    return account_id


@pytest.fixture
def t02_api(monkeypatch: pytest.MonkeyPatch) -> Iterator[T02Api]:
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
    org_a, org_b = f"t02-{token}-a", f"t02-{token}-b"
    org_c, org_d = f"t02-{token}-c", f"t02-{token}-d"
    teacher, manager = f"t02-{token}-teacher", f"t02-{token}-manager"
    parent, platform_admin = f"t02-{token}-parent", f"t02-{token}-platform"
    other_teacher, mismatch = f"t02-{token}-other-teacher", f"t02-{token}-mismatch"
    with runtime.session_factory.begin() as db:
        db.add_all(
            [
                OrganizationModel(organization_id=org_a, display_name="School A", state="active"),
                OrganizationModel(organization_id=org_b, display_name="School B", state="active"),
                OrganizationModel(
                    organization_id=org_c, display_name="School C", state="suspended"
                ),
                OrganizationModel(organization_id=org_d, display_name="School D", state="active"),
            ]
        )
        _identity(db, teacher, "teacher")
        _identity(db, manager, "school_manager")
        _identity(db, parent, "parent")
        _identity(db, platform_admin, "platform_admin")
        _identity(db, other_teacher, "teacher")
        _identity(db, mismatch, "teacher", issuer="another-issuer")
        db.flush()
        for class_id, org, name, state in (
            (f"{token}-a1", org_a, "A one", "active"),
            (f"{token}-a2", org_a, "A two locked", "locked"),
            (f"{token}-a3", org_a, "A three archived", "archived"),
            (f"{token}-b1", org_b, "B one", "active"),
            (f"{token}-c1", org_c, "C one", "active"),
            (f"{token}-d1", org_d, "D one", "active"),
        ):
            db.add(
                ClassroomModel(
                    class_id=class_id,
                    organization_id=org,
                    display_name=name,
                    state=state,
                    created_by="synthetic",
                )
            )
        db.flush()
        # Teacher: class-bound, locked/archived (dropped), dangling and cross-organization
        # class ids (dropped), an org-wide observer, two roles on one class, an inactive
        # organization, an inactive assignment and an assignment in a tenant of no interest.
        _assign(db, teacher, org_a, "teacher", f"{token}-a1")
        _assign(db, teacher, org_a, "teacher", f"{token}-a2")
        _assign(db, teacher, org_a, "teacher", f"{token}-a3")
        _assign(db, teacher, org_a, "teacher", f"{token}-ghost")
        _assign(db, teacher, org_a, "teacher", f"{token}-b1")  # class of another organization
        _assign(db, teacher, org_a, "observer", None)
        _assign(db, teacher, org_a, "guide", f"{token}-a1", active=False)
        _assign(db, teacher, org_b, "teacher", f"{token}-b1")
        _assign(db, teacher, org_b, "observer", f"{token}-b1")
        _assign(db, teacher, org_c, "teacher", f"{token}-c1")
        _assign(db, teacher, org_d, "teacher", f"{token}-d1", active=False)
        # Manager: organization-wide in two organizations; never enumerates classes.
        _assign(db, manager, org_a, "school_admin", None)
        _assign(db, manager, org_b, "school_admin", None)
        # Another subject's rows must never appear for the teacher.
        _assign(db, other_teacher, org_a, "teacher", f"{token}-a1")
        _assign(db, other_teacher, org_d, "teacher", f"{token}-d1")
        # Stray rows on roles without organization scope.
        _assign(db, parent, org_a, "teacher", f"{token}-a1")
        _assign(db, platform_admin, org_a, "school_admin", None)
        _assign(db, mismatch, org_a, "teacher", f"{token}-a1")

    async def verified(
        x_test_principal: str = Header(alias="X-Test-Principal"),
    ) -> VerifiedPrincipal:
        return VerifiedPrincipal(subject=x_test_principal, issuer=ISSUER, roles=frozenset())

    app.dependency_overrides[get_verified_adult] = verified
    try:
        with TestClient(app) as client:
            yield T02Api(
                app,
                client,
                token,
                teacher,
                manager,
                parent,
                platform_admin,
                other_teacher,
                mismatch,
                org_a,
                org_b,
                org_c,
                org_d,
            )
    finally:
        app.dependency_overrides.clear()
        runtime.engine.dispose()
        get_settings.cache_clear()
        get_core_database_settings.cache_clear()


def test_teacher_scope_filters_orders_and_does_not_leak(t02_api: T02Api) -> None:
    api = t02_api

    response = api.me(api.teacher)

    assert response.status_code == 200
    assert response.headers["Cache-Control"] == "private, no-store"
    body = response.json()
    assert body["role"] == "teacher"
    assert body["role_revision"] == 2
    scope = body["scope"]
    # Active organizations only (C is suspended; D holds an inactive assignment), by id.
    assert [(item["organization_id"], item["roles"]) for item in scope["organizations"]] == [
        (api.org_a, ["observer", "teacher"]),
        (api.org_b, ["observer", "teacher"]),
    ]
    assert [item["display_name"] for item in scope["organizations"]] == ["School A", "School B"]
    # Only active classrooms of the assignment's own organization, one entry per held role.
    assert [
        (item["organization_id"], item["class_id"], item["role"], item["state"])
        for item in scope["classes"]
    ] == [
        (api.org_a, f"{api.token}-a1", "teacher", "active"),
        (api.org_b, f"{api.token}-b1", "observer", "active"),
        (api.org_b, f"{api.token}-b1", "teacher", "active"),
    ]
    assert scope["truncated"] is False
    assert scope["permissions"] == []
    assert scope["accounts"]["managed"] == "NONE"
    text = response.text
    for foreign in (api.org_c_suspended, api.org_d, f"{api.token}-d1", api.other_teacher):
        assert foreign not in text
    # The dropped class ids never surface.
    for dropped in ("a2", "a3", "ghost"):
        assert f"{api.token}-{dropped}" not in text


def test_manager_scope_lists_organization_wide_roles_without_classes(t02_api: T02Api) -> None:
    api = t02_api

    scope = api.me(api.manager).json()["scope"]

    assert [(item["organization_id"], item["roles"]) for item in scope["organizations"]] == [
        (api.org_a, ["school_admin"]),
        (api.org_b, ["school_admin"]),
    ]
    assert scope["classes"] == []
    assert scope["truncated"] is False


def test_other_subject_sees_only_its_own_rows(t02_api: T02Api) -> None:
    api = t02_api

    scope = api.me(api.other_teacher).json()["scope"]

    assert [item["organization_id"] for item in scope["organizations"]] == [api.org_a, api.org_d]
    assert [item["class_id"] for item in scope["classes"]] == [
        f"{api.token}-a1",
        f"{api.token}-d1",
    ]


def test_parent_and_platform_admin_get_empty_lists_and_the_managed_flag(t02_api: T02Api) -> None:
    api = t02_api

    parent = api.me(api.parent)
    platform = api.me(api.platform_admin)

    assert parent.status_code == platform.status_code == 200
    for response, managed in ((parent, "NONE"), (platform, "PLATFORM")):
        scope = response.json()["scope"]
        assert scope["organizations"] == []
        assert scope["classes"] == []
        assert scope["permissions"] == []
        assert scope["truncated"] is False
        assert scope["accounts"]["managed"] == managed


def test_account_id_is_the_callers_own_and_the_refusal_has_none(t02_api: T02Api) -> None:
    api = t02_api
    with api.session()() as db:
        teacher_account = db.get(AdultIdentityModel, api.teacher).account_id
        other_account = db.get(AdultIdentityModel, api.other_teacher).account_id

    own = api.me(api.teacher).json()
    refused = api.me(f"unknown-{api.token}")

    assert own["scope"]["accounts"]["account_id"] == teacher_account
    assert teacher_account != other_account
    assert api.teacher not in api.me(api.teacher).text
    assert refused.status_code == ME_SETUP_REFUSAL_STATUS
    assert refused.headers["Cache-Control"] == "private, no-store"
    assert "scope" not in refused.json()
    assert "account_id" not in refused.text
    assert f"unknown-{api.token}" not in refused.text


def test_refusal_is_identical_for_unknown_and_issuer_mismatch(t02_api: T02Api) -> None:
    api = t02_api
    with api.session()() as db:
        db.get(AdultIdentityModel, api.parent).state = "disabled"
        db.get(AdultIdentityModel, api.manager).account_role = None
        db.commit()

    outcomes = set()
    for subject in (f"unknown-{api.token}", api.mismatch, api.parent, api.manager):
        response = api.me(subject)
        body = response.json()
        outcomes.add((response.status_code, body["code"], body["message"]))
        assert subject not in response.text

    assert len(outcomes) == 1
    assert next(iter(outcomes))[:2] == (ME_SETUP_REFUSAL_STATUS, "ACCOUNT_SETUP_UNAVAILABLE")


def test_loader_is_reusable_with_a_plain_session(t02_api: T02Api) -> None:
    api = t02_api
    with api.session()() as db:
        scope = load_granted_scope(db, db.get(AdultIdentityModel, api.teacher))

    assert scope.organization_ids() == frozenset({api.org_a, api.org_b})
    assert scope.managed == "NONE"


def test_organization_cap_sets_truncated(t02_api: T02Api) -> None:
    api = t02_api
    subject = f"t02-{api.token}-many-orgs"
    with api.session().begin() as db:
        _identity(db, subject, "school_manager")
        for index in range(MAX_SCOPE_ORGANIZATIONS + 1):
            org = f"t02-{api.token}-m{index:03d}"
            db.add(
                OrganizationModel(organization_id=org, display_name=f"Many {index}", state="active")
            )
        db.flush()
        for index in range(MAX_SCOPE_ORGANIZATIONS + 1):
            _assign(db, subject, f"t02-{api.token}-m{index:03d}", "school_admin", None)

    scope = api.me(subject).json()["scope"]

    assert len(scope["organizations"]) == MAX_SCOPE_ORGANIZATIONS
    assert scope["truncated"] is True
    assert scope["organizations"][0]["organization_id"] == f"t02-{api.token}-m000"
    assert scope["organizations"][-1]["organization_id"] == (
        f"t02-{api.token}-m{MAX_SCOPE_ORGANIZATIONS - 1:03d}"
    )


def test_class_cap_sets_truncated(t02_api: T02Api) -> None:
    api = t02_api
    subject = f"t02-{api.token}-many-classes"
    org = f"t02-{api.token}-classes"
    with api.session().begin() as db:
        _identity(db, subject, "teacher")
        db.add(OrganizationModel(organization_id=org, display_name="Classes", state="active"))
        db.flush()
        for index in range(MAX_SCOPE_CLASSES + 1):
            db.add(
                ClassroomModel(
                    class_id=f"{api.token}-k{index:03d}",
                    organization_id=org,
                    display_name=f"Class {index}",
                    state="active",
                    created_by="synthetic",
                )
            )
        db.flush()
        for index in range(MAX_SCOPE_CLASSES + 1):
            _assign(db, subject, org, "teacher", f"{api.token}-k{index:03d}")

    scope = api.me(subject).json()["scope"]

    assert len(scope["organizations"]) == 1
    assert len(scope["classes"]) == MAX_SCOPE_CLASSES
    assert scope["truncated"] is True
    assert scope["classes"][0]["class_id"] == f"{api.token}-k000"
