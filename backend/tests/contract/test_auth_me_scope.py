"""FEAT-066 T0.2: ``GET /api/auth/v1/me`` returns the granted scope (SRS l.794, TD-25).

Offline: the identity row is served by a fake session and the scope loader is stubbed by
monkeypatch; the loader itself is covered with a queued fake session (caps, role gating) here
and against PostgreSQL in ``tests/integration/test_auth_me_scope_postgres.py``.
"""

from __future__ import annotations

import json
from collections.abc import Iterator
from types import SimpleNamespace
from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.infrastructure.config.settings import (
    CoreDatabaseSettings,
    Settings,
    get_core_database_settings,
    get_settings,
)
from sketch2life.infrastructure.persistence.be1_models import AdultIdentityModel
from sketch2life.interfaces.http import account_scope
from sketch2life.interfaces.http.account_scope import (
    MAX_SCOPE_CLASSES,
    MAX_SCOPE_ORGANIZATIONS,
    GrantedClass,
    GrantedOrganization,
    GrantedScope,
    load_granted_scope,
)
from sketch2life.interfaces.http.app import create_app
from sketch2life.interfaces.http.be1_runtime import get_db, get_verified_adult
from sketch2life.interfaces.http.routers import auth_registration
from sketch2life.interfaces.http.routers.auth_registration import ME_SETUP_REFUSAL_STATUS

ISSUER = "synthetic-t02-issuer"
SUBJECT = "synthetic-t02-subject-7c1d"
EMAIL_LIKE = "synthetic.t02@example.test"
ACCOUNT_ID = "00000000-0000-4000-8000-0000000000a2"
ME = "/api/auth/v1/me"


@pytest.fixture(autouse=True)
def _offline_settings(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    monkeypatch.setitem(Settings.model_config, "env_file", None)
    monkeypatch.setitem(CoreDatabaseSettings.model_config, "env_file", None)
    monkeypatch.setenv("SKETCH2LIFE_ENV", "test")
    monkeypatch.setenv("STORYRUN_LITE_MAIN_DEMO_ENABLED", "0")
    monkeypatch.setenv("SKETCH2LIFE_DATABASE_URL", "postgresql+psycopg://localhost:9/t02_closed")
    get_settings.cache_clear()
    get_core_database_settings.cache_clear()
    yield
    get_settings.cache_clear()
    get_core_database_settings.cache_clear()


class _FakeSession:
    """Only ``get`` is used by the route before the (stubbed) loader runs."""

    def __init__(self, identity: AdultIdentityModel | None) -> None:
        self._identity = identity

    def get(self, _model: object, _key: object) -> AdultIdentityModel | None:
        return self._identity


def _identity(
    *,
    role: str | None = "teacher",
    state: str = "active",
    issuer: str = ISSUER,
    revision: int = 3,
) -> AdultIdentityModel:
    return AdultIdentityModel(
        subject=SUBJECT,
        account_id=ACCOUNT_ID,
        issuer=issuer,
        state=state,
        account_role=role,
        role_revision=revision,
    )


def _app(identity: AdultIdentityModel | None) -> FastAPI:
    application = create_app()
    application.dependency_overrides[get_verified_adult] = lambda: VerifiedPrincipal(
        subject=SUBJECT, issuer=ISSUER, roles=frozenset()
    )
    application.dependency_overrides[get_db] = lambda: _FakeSession(identity)
    return application


def _stub_loader(monkeypatch: pytest.MonkeyPatch, scope: GrantedScope) -> list[str]:
    seen: list[str] = []

    def fake(_db: object, identity: AdultIdentityModel) -> GrantedScope:
        seen.append(identity.subject)
        return scope

    monkeypatch.setattr(auth_registration, "load_granted_scope", fake)
    return seen


def _scope(**overrides: Any) -> GrantedScope:
    values: dict[str, Any] = {"account_id": ACCOUNT_ID, "managed": "NONE"}
    values.update(overrides)
    return GrantedScope(**values)


def _get(application: FastAPI) -> Any:
    with TestClient(application) as client:
        return client.get(ME, headers={"Authorization": "Bearer synthetic"})


@pytest.mark.parametrize(
    ("role", "scope", "managed"),
    [
        ("parent", _scope(), "NONE"),
        ("platform_admin", _scope(managed="PLATFORM"), "PLATFORM"),
        (
            "teacher",
            _scope(
                organizations=(GrantedOrganization("org-a", "School A", ("observer", "teacher")),),
                classes=(GrantedClass("org-a", "class-1", "Lớp Mầm", "teacher", "active"),),
            ),
            "NONE",
        ),
        (
            "school_manager",
            _scope(
                organizations=(GrantedOrganization("org-a", "School A", ("school_admin",)),),
            ),
            "NONE",
        ),
    ],
)
def test_me_returns_role_and_scope_per_role(
    monkeypatch: pytest.MonkeyPatch, role: str, scope: GrantedScope, managed: str
) -> None:
    seen = _stub_loader(monkeypatch, scope)

    response = _get(_app(_identity(role=role)))

    assert response.status_code == 200
    body = response.json()
    assert body["role"] == role
    assert body["state"] == "active"
    assert body["role_revision"] == 3
    assert set(body) == {"role", "state", "role_revision", "scope"}
    assert body["scope"]["accounts"] == {"account_id": ACCOUNT_ID, "managed": managed}
    assert body["scope"]["permissions"] == []
    assert body["scope"]["truncated"] is False
    assert [item["organization_id"] for item in body["scope"]["organizations"]] == [
        item.organization_id for item in scope.organizations
    ]
    assert [item["roles"] for item in body["scope"]["organizations"]] == [
        list(item.roles) for item in scope.organizations
    ]
    assert [item["class_id"] for item in body["scope"]["classes"]] == [
        item.class_id for item in scope.classes
    ]
    assert response.headers["Cache-Control"] == "private, no-store"
    assert seen == [SUBJECT]


def test_me_scope_account_id_is_the_callers_own_and_not_the_subject(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _stub_loader(monkeypatch, _scope())

    response = _get(_app(_identity(role="parent")))

    body = response.json()
    assert body["scope"]["accounts"]["account_id"] == ACCOUNT_ID
    assert SUBJECT not in json.dumps(body)


def test_me_scope_truncated_flag_is_passed_through(monkeypatch: pytest.MonkeyPatch) -> None:
    _stub_loader(monkeypatch, _scope(truncated=True))

    assert _get(_app(_identity())).json()["scope"]["truncated"] is True


@pytest.mark.parametrize(
    "identity",
    [
        None,
        _identity(state="disabled"),
        _identity(role=None),
        _identity(issuer="another-issuer"),
    ],
    ids=["missing", "disabled", "no-role", "issuer-mismatch"],
)
def test_me_refusal_is_one_uniform_body_without_identifiers(
    monkeypatch: pytest.MonkeyPatch, identity: AdultIdentityModel | None
) -> None:
    seen = _stub_loader(monkeypatch, _scope())

    response = _get(_app(identity))

    assert response.status_code == ME_SETUP_REFUSAL_STATUS
    body = response.json()
    assert body["code"] == "ACCOUNT_SETUP_UNAVAILABLE"
    assert "scope" not in body
    assert response.headers["Cache-Control"] == "private, no-store"
    text = json.dumps(body).lower()
    for forbidden in ("subject", "uid", "email", SUBJECT, ACCOUNT_ID, "account_id", EMAIL_LIKE):
        assert forbidden.lower() not in text
    assert seen == []


def test_me_refusal_is_identical_for_the_four_causes(monkeypatch: pytest.MonkeyPatch) -> None:
    _stub_loader(monkeypatch, _scope())
    outcomes = set()
    for identity in (
        None,
        _identity(state="disabled"),
        _identity(role=None),
        _identity(issuer="another-issuer"),
    ):
        response = _get(_app(identity))
        body = response.json()
        outcomes.add(
            (
                response.status_code,
                body["code"],
                body["message"],
                json.dumps(body.get("field_errors")),
            )
        )

    assert len(outcomes) == 1


def test_me_refusal_status_keeps_403_through_one_constant() -> None:
    # TD-25: the Parent client (ParentAuth.ts) branches on 403. Changing this constant to 409
    # is the one-line backend switch; make it together with the FE change.
    assert ME_SETUP_REFUSAL_STATUS == 403


def test_openapi_declares_scope_and_the_refusal_status() -> None:
    application = create_app()
    application.openapi()
    document = application.state.runtime_openapi_schema
    operation = document["paths"][ME]["get"]
    schemas = document["components"]["schemas"]

    assert str(ME_SETUP_REFUSAL_STATUS) in operation["responses"]
    assert "401" in operation["responses"]
    assert "private, no-store" in operation["description"]
    ref = operation["responses"]["200"]["content"]["application/json"]["schema"]["$ref"]
    current = schemas[ref.rsplit("/", 1)[-1]]
    assert set(current["properties"]) == {"role", "state", "role_revision", "scope"}
    assert "scope" in current["required"]
    scope_ref = current["properties"]["scope"]["$ref"].rsplit("/", 1)[-1]
    scope = schemas[scope_ref]
    assert set(scope["properties"]) == {
        "organizations",
        "classes",
        "accounts",
        "permissions",
        "truncated",
    }
    assert {"organizations", "classes", "accounts", "truncated"} <= set(scope["required"])


class _Result:
    def __init__(self, rows: list[Any]) -> None:
        self._rows = rows

    def all(self) -> list[Any]:
        return self._rows


class _QueuedSession:
    """Serves the loader's queries in order: organizations, roles, classes."""

    def __init__(self, *results: list[Any]) -> None:
        self._results = list(results)
        self.calls = 0

    def execute(self, _statement: object) -> _Result:
        self.calls += 1
        return _Result(self._results.pop(0))


def _org_row(index: int) -> Any:
    return SimpleNamespace(organization_id=f"org-{index:04d}", display_name=f"School {index}")


def _class_row(index: int) -> Any:
    return SimpleNamespace(
        organization_id="org-0000",
        class_id=f"class-{index:04d}",
        display_name=f"Class {index}",
        role="teacher",
        state="active",
    )


@pytest.mark.parametrize("role", ["parent", "platform_admin"])
def test_loader_reads_nothing_for_roles_without_organization_scope(role: str) -> None:
    session = _QueuedSession()

    scope = load_granted_scope(session, _identity(role=role))  # type: ignore[arg-type]

    assert session.calls == 0
    assert scope.organizations == ()
    assert scope.classes == ()
    assert scope.truncated is False
    assert scope.account_id == ACCOUNT_ID
    assert scope.managed == ("PLATFORM" if role == "platform_admin" else "NONE")


def test_loader_without_organizations_stops_after_one_query() -> None:
    session = _QueuedSession([])

    scope = load_granted_scope(session, _identity())  # type: ignore[arg-type]

    assert session.calls == 1
    assert scope.organizations == ()
    assert scope.classes == ()


def test_loader_caps_organizations_and_classes_and_reports_truncated() -> None:
    organizations = [_org_row(index) for index in range(MAX_SCOPE_ORGANIZATIONS + 1)]
    roles = [
        SimpleNamespace(organization_id=row.organization_id, role=role)
        for row in organizations
        for role in ("teacher", "observer")
    ]
    classes = [_class_row(index) for index in range(MAX_SCOPE_CLASSES + 1)]
    session = _QueuedSession(organizations, roles, classes)

    scope = load_granted_scope(session, _identity())  # type: ignore[arg-type]

    assert len(scope.organizations) == MAX_SCOPE_ORGANIZATIONS
    assert len(scope.classes) == MAX_SCOPE_CLASSES
    assert scope.truncated is True
    assert scope.organizations[0].roles == ("observer", "teacher")
    assert scope.organizations[-1].organization_id == f"org-{MAX_SCOPE_ORGANIZATIONS - 1:04d}"


def test_loader_exact_cap_is_not_truncated() -> None:
    organizations = [_org_row(index) for index in range(MAX_SCOPE_ORGANIZATIONS)]
    roles = [
        SimpleNamespace(organization_id=row.organization_id, role="school_admin")
        for row in organizations
    ]
    classes = [_class_row(index) for index in range(MAX_SCOPE_CLASSES)]
    session = _QueuedSession(organizations, roles, classes)

    scope = load_granted_scope(session, _identity(role="school_manager"))  # type: ignore[arg-type]

    assert len(scope.organizations) == MAX_SCOPE_ORGANIZATIONS
    assert len(scope.classes) == MAX_SCOPE_CLASSES
    assert scope.truncated is False


def test_loader_module_exports_the_reusable_reader() -> None:
    assert account_scope.__all__.count("load_granted_scope") == 1
    assert GrantedScope(account_id="a", managed="NONE").organization_ids() == frozenset()
