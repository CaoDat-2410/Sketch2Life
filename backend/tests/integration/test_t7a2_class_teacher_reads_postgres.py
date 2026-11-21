"""T-7a2 PostgreSQL acceptance: child-profile reads need the class's own Teacher row.

SRS l.541 (one Teacher per class), l.2586 and l.2602 (Teacher profile and roster access needs the
class assignment), l.553 (access follows the current Teacher), l.864-865 (403 only inside a known
scope; one 404 otherwise). Routes: R1 ``GET .../sessions/{id}/pilot-profiles``, R2
``GET .../sessions/{id}/roster``, R3 ``GET .../classes/{id}/profiles/{child}/portfolio``.
Set BE1_TEST_DATABASE_URL to a disposable database whose name contains ``be1_acceptance``; every
test builds its own organizations. Only the external token boundary is substituted: a test header
names the acting adult, and every route, scope query and transaction is real.
"""

from __future__ import annotations

import os
from collections.abc import Iterator
from dataclasses import dataclass, field
from typing import Any
from uuid import uuid4

import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
from sqlalchemy import update

from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.infrastructure.config.settings import get_core_database_settings, get_settings
from sketch2life.infrastructure.persistence.be1_models import (
    AdultIdentityModel,
    ClassroomModel,
    ClassroomSessionModel,
    ConsentRecordModel,
    ManagedProfileModel,
    OrganizationAssignmentModel,
    OrganizationModel,
)
from sketch2life.interfaces.http.app import create_app
from sketch2life.interfaces.http.be1_runtime import get_verified_adult

ISSUER = "synthetic-test-issuer"
ACTOR_HEADER = "X-T7a2-Actor"
# (actor, account role, assignment role, scope, active). Scopes: "org" (class_id NULL), "class",
# "other" (the other class of the organization), "foreign" (another organization, org-wide).
# An actor named twice holds several rows.
ACTORS: tuple[tuple[str, str, str, str, bool], ...] = (
    ("manager", "school_manager", "school_admin", "org", True),
    ("scoped_teacher", "teacher", "teacher", "class", True),
    ("orgwide_teacher", "teacher", "teacher", "org", True),
    ("orgwide_and_scoped_teacher", "teacher", "teacher", "org", True),
    ("orgwide_and_scoped_teacher", "teacher", "teacher", "class", True),
    ("orgwide_guide", "teacher", "guide", "org", True),
    ("class_guide", "teacher", "guide", "class", True),
    ("orgwide_observer", "teacher", "observer", "org", True),
    ("class_observer", "teacher", "observer", "class", True),
    ("guide_and_other_class_teacher", "teacher", "guide", "class", True),
    ("guide_and_other_class_teacher", "teacher", "teacher", "other", True),
    ("other_class_teacher", "teacher", "teacher", "other", True),
    ("revoked_teacher", "teacher", "teacher", "class", False),
    ("foreign_teacher", "teacher", "teacher", "foreign", True),
    ("foreign_manager", "school_manager", "school_admin", "foreign", True),
    ("parent", "parent", "teacher", "class", True),
    ("platform_admin", "platform_admin", "school_admin", "org", True),
)
# Every actor of a row in scope that is NOT the class's own Teacher: 403 on R1, R2 and R3.
FORBIDDEN = (
    "manager",
    "orgwide_teacher",
    "orgwide_guide",
    "class_guide",
    "orgwide_observer",
    "class_observer",
    "guide_and_other_class_teacher",
)
# No covering row (or no usable identity): the uniform 404 on R1, R2 and R3.
OUT_OF_SCOPE = (
    "other_class_teacher",
    "revoked_teacher",
    "foreign_teacher",
    "foreign_manager",
    "parent",
    "platform_admin",
)
ASSIGNED = ("scoped_teacher", "orgwide_and_scoped_teacher")


@dataclass
class T7a2:
    app: FastAPI
    client: TestClient
    organization_id: str
    foreign_organization_id: str
    class_id: str
    other_class_id: str
    session_id: str
    child_id: str
    subjects: dict[str, str] = field(default_factory=dict)

    @property
    def factory(self) -> Any:
        return self.app.state.be1_runtime.session_factory

    def get(self, actor: str, path: str) -> Any:
        return self.client.get(path, headers={ACTOR_HEADER: actor})

    def org(self, suffix: str = "", organization_id: str | None = None) -> str:
        return f"/api/be1/v1/organizations/{organization_id or self.organization_id}{suffix}"

    @property
    def pilot(self) -> str:
        return self.org(f"/sessions/{self.session_id}/pilot-profiles")

    @property
    def roster(self) -> str:
        return self.org(f"/sessions/{self.session_id}/roster")

    def portfolio(self, child_id: str | None = None, class_id: str | None = None) -> str:
        return self.org(
            f"/classes/{class_id or self.class_id}/profiles/{child_id or self.child_id}/portfolio"
        )

    def routes(self) -> dict[str, str]:
        return {"R1": self.pilot, "R2": self.roster, "R3": self.portfolio()}


@pytest.fixture
def t7a2(monkeypatch: pytest.MonkeyPatch, tmp_path: Any) -> Iterator[T7a2]:
    database_url = os.environ.get("BE1_TEST_DATABASE_URL")
    if not database_url:
        pytest.skip("set BE1_TEST_DATABASE_URL to run PostgreSQL-backed T-7a2 acceptance tests")
    if "be1_acceptance" not in database_url.rsplit("/", 1)[-1]:
        pytest.fail("BE1_TEST_DATABASE_URL must point to a disposable *be1_acceptance database")
    monkeypatch.setenv("SKETCH2LIFE_DATABASE_URL", database_url)
    monkeypatch.setenv("SKETCH2LIFE_AUTH_PROVIDER", "development")
    monkeypatch.setenv("SKETCH2LIFE_ENV", "test")
    monkeypatch.setenv("SKETCH2LIFE_SYNTHETIC_PILOT_ENABLED", "true")
    monkeypatch.setenv("SKETCH2LIFE_ROOM_CODE_HMAC_KEY", "synthetic-test-key-" + "x" * 40)
    monkeypatch.setenv("SKETCH2LIFE_BE1_ARTIFACT_ROOT", str(tmp_path / "artifacts"))
    get_settings.cache_clear()
    get_core_database_settings.cache_clear()

    app = create_app()
    runtime = app.state.be1_runtime
    if runtime.engine is None or runtime.session_factory is None:
        pytest.fail("BE1 PostgreSQL runtime did not initialize")

    run = uuid4().hex[:10]
    organization_id = f"synthetic-t7a2-{run}-org"
    foreign_organization_id = f"synthetic-t7a2-{run}-foreign"
    class_id = f"synthetic-t7a2-{run}-class-a"
    other_class_id = f"synthetic-t7a2-{run}-class-b"
    foreign_class_id = f"synthetic-t7a2-{run}-foreign-class"
    session_id = f"synthetic-t7a2-{run}-session"
    child_id = f"synthetic-{uuid4().hex[:24]}"
    consent_id = str(uuid4())
    purpose_ref = f"synthetic-purpose-{uuid4().hex[:8]}"
    names = sorted({row[0] for row in ACTORS})
    subjects = {name: f"synthetic-t7a2-{run}-{name}" for name in names}
    principals = {
        subject: VerifiedPrincipal(
            subject=subject, issuer=ISSUER, roles=frozenset(), token_id=f"synthetic-t7a2-{n}"
        )
        for n, subject in enumerate(subjects.values())
    }
    account_roles = {row[0]: row[1] for row in ACTORS}

    with runtime.session_factory.begin() as db:
        db.add_all(
            [
                OrganizationModel(
                    organization_id=organization_id,
                    display_name="Synthetic T7a2 org",
                    state="active",
                ),
                OrganizationModel(
                    organization_id=foreign_organization_id,
                    display_name="Synthetic T7a2 foreign org",
                    state="active",
                ),
            ]
        )
        db.flush()
        db.add_all(
            [
                ClassroomModel(
                    class_id=cid,
                    organization_id=oid,
                    display_name=f"Synthetic {cid}"[:200],
                    state="active",
                    created_by="synthetic-t7a2-seed",
                )
                for cid, oid in (
                    (class_id, organization_id),
                    (other_class_id, organization_id),
                    (foreign_class_id, foreign_organization_id),
                )
            ]
        )
        db.add_all(
            [
                AdultIdentityModel(
                    subject=subjects[name],
                    issuer=ISSUER,
                    state="active",
                    account_role=account_roles[name],
                )
                for name in names
            ]
        )
        db.flush()
        scope_org = {
            "org": (organization_id, None),
            "class": (organization_id, class_id),
            "other": (organization_id, other_class_id),
            "foreign": (foreign_organization_id, None),
        }
        db.add_all(
            [
                OrganizationAssignmentModel(
                    assignment_id=str(uuid4()),
                    organization_id=scope_org[scope][0],
                    subject=subjects[name],
                    class_id=scope_org[scope][1],
                    role=role,
                    active=active,
                )
                for name, _account_role, role, scope, active in ACTORS
            ]
        )
        # A lobby session (no purpose, so the pilot list is empty) and one profile for R3.
        db.add(
            ClassroomSessionModel(
                session_id=session_id,
                organization_id=organization_id,
                class_id=class_id,
                created_by=subjects["manager"],
                state="lobby",
                revision=1,
                configuration={},
            )
        )
        db.add(
            ConsentRecordModel(
                consent_id=consent_id,
                organization_id=organization_id,
                class_id=class_id,
                child_id=child_id,
                purpose_ref=purpose_ref,
                state="pending",
                recorded_by=subjects["manager"],
            )
        )
        db.flush()
        db.add(
            ManagedProfileModel(
                child_id=child_id,
                organization_id=organization_id,
                class_id=class_id,
                display_name="Synthetic Hidden Child",
                age_months=72,
                age_revision=1,
                age_source="ADULT_DECLARED",
                consent_id=consent_id,
                consent_purpose_ref=purpose_ref,
                state="active",
                created_by=subjects["manager"],
            )
        )

    async def verified_actor(request: Request) -> VerifiedPrincipal:
        return principals[subjects[request.headers[ACTOR_HEADER]]]

    app.dependency_overrides[get_verified_adult] = verified_actor
    with TestClient(app, client=("10.7.7.8", 12345)) as client:
        yield T7a2(
            app=app,
            client=client,
            organization_id=organization_id,
            foreign_organization_id=foreign_organization_id,
            class_id=class_id,
            other_class_id=other_class_id,
            session_id=session_id,
            child_id=child_id,
            subjects=subjects,
        )
    app.dependency_overrides.clear()
    runtime.engine.dispose()
    get_settings.cache_clear()
    get_core_database_settings.cache_clear()


def _core(response: Any) -> dict[str, Any]:
    body = response.json()
    return {"code": body["code"], "message": body["message"]}


# --- the assigned Teacher ---------------------------------------------------------------------


@pytest.mark.parametrize("actor", ASSIGNED)
def test_assigned_teacher_reaches_all_three_reads(t7a2: T7a2, actor: str) -> None:
    pilot = t7a2.get(actor, t7a2.pilot)
    assert pilot.status_code == 200, pilot.text
    assert pilot.json() == {"contract": "Be1PilotProfileListV1", "items": []}
    roster = t7a2.get(actor, t7a2.roster)
    assert roster.status_code == 200, roster.text
    assert roster.json()["contract"] == "Be1SessionRosterV1"
    portfolio = t7a2.get(actor, t7a2.portfolio())
    assert portfolio.status_code == 409, portfolio.text
    assert portfolio.json()["code"] == "CONSENT_NOT_EFFECTIVE"
    unknown_child = t7a2.get(actor, t7a2.portfolio(child_id="synthetic-missing"))
    assert unknown_child.status_code == 404
    # The wire maps every 404 to the uniform body (T0.9), so the profile code is not visible.
    assert unknown_child.json()["code"] == "RESOURCE_NOT_FOUND"


# --- in scope but not the class's own Teacher: 403 --------------------------------------------


@pytest.mark.parametrize("actor", FORBIDDEN)
def test_in_scope_caller_without_the_class_teacher_row_is_403(t7a2: T7a2, actor: str) -> None:
    for name, path in t7a2.routes().items():
        response = t7a2.get(actor, path)
        assert response.status_code == 403, (actor, name, response.text)
        assert _core(response)["code"] == "ACTION_NOT_ALLOWED"
        for forbidden in ("items", "members", "Synthetic Hidden Child", t7a2.child_id):
            assert forbidden not in response.text, (actor, name, forbidden)


def test_all_403_bodies_are_one_body_and_differ_from_the_uniform_404(t7a2: T7a2) -> None:
    bodies = {
        _core(t7a2.get(actor, path)).__repr__()
        for actor in FORBIDDEN
        for path in t7a2.routes().values()
    }
    assert len(bodies) == 1
    not_found = _core(t7a2.get("foreign_teacher", t7a2.pilot))
    assert not_found["code"] == "RESOURCE_NOT_FOUND"
    assert repr(not_found) not in bodies


def test_the_manager_cannot_tell_a_known_child_from_an_unknown_one(t7a2: T7a2) -> None:
    known = t7a2.get("manager", t7a2.portfolio())
    unknown = t7a2.get("manager", t7a2.portfolio(child_id="synthetic-missing"))
    assert known.status_code == unknown.status_code == 403
    assert _core(known) == _core(unknown)


# --- out of scope: the uniform 404 ------------------------------------------------------------


def test_out_of_scope_callers_get_one_uniform_404_body(t7a2: T7a2) -> None:
    seen: list[dict[str, Any]] = []
    for actor in OUT_OF_SCOPE:
        for name, path in t7a2.routes().items():
            response = t7a2.get(actor, path)
            assert response.status_code == 404, (actor, name, response.text)
            seen.append(_core(response))
    assert seen[0]["code"] == "RESOURCE_NOT_FOUND"
    assert all(body == seen[0] for body in seen)


def test_unknown_organization_session_class_and_child_are_404_for_every_caller(
    t7a2: T7a2,
) -> None:
    missing = f"missing-{uuid4().hex[:8]}"
    for actor in (*ASSIGNED, *FORBIDDEN, *OUT_OF_SCOPE):
        unknown_org = t7a2.org(f"/sessions/{t7a2.session_id}/roster", missing)
        paths = (
            t7a2.org(f"/sessions/{missing}/pilot-profiles"),
            t7a2.org(f"/sessions/{missing}/roster"),
            t7a2.org(f"/classes/{missing}/profiles/{t7a2.child_id}/portfolio"),
            unknown_org,
            t7a2.org(f"/sessions/{t7a2.session_id}/pilot-profiles", missing),
            t7a2.org(f"/classes/{t7a2.class_id}/profiles/{t7a2.child_id}/portfolio", missing),
        )
        for path in paths:
            response = t7a2.get(actor, path)
            assert response.status_code == 404, (actor, path, response.text)
    # A Teacher of the foreign organization reading the real ids: the same uniform body as an
    # unknown session, so the 403 never tells a foreign caller that the session exists.
    unknown_session = t7a2.get("foreign_teacher", t7a2.org(f"/sessions/{missing}/roster"))
    real_session = t7a2.get("foreign_teacher", t7a2.roster)
    assert _core(unknown_session) == _core(real_session)


# --- D2: "current" is read on every request ---------------------------------------------------


def test_deactivating_the_assigned_row_cuts_the_next_read(t7a2: T7a2) -> None:
    assert t7a2.get("scoped_teacher", t7a2.roster).status_code == 200
    assert t7a2.get("scoped_teacher", t7a2.pilot).status_code == 200
    with t7a2.factory.begin() as db:
        db.execute(
            update(OrganizationAssignmentModel)
            .where(
                OrganizationAssignmentModel.subject == t7a2.subjects["scoped_teacher"],
                OrganizationAssignmentModel.organization_id == t7a2.organization_id,
            )
            .values(active=False)
        )
    for name, path in t7a2.routes().items():
        response = t7a2.get("scoped_teacher", path)
        assert response.status_code == 404, (name, response.text)
        assert _core(response)["code"] == "RESOURCE_NOT_FOUND"
