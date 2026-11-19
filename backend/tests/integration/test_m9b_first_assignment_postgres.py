"""FEAT-066 C6 M9-B: Teacher candidates and the first class assignment on PostgreSQL.

Runs only against a disposable database whose name contains ``be1_acceptance``. The identity
provider is a synthetic in-memory fake; no network is used.
"""

from __future__ import annotations

import os
from collections.abc import Iterator
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from threading import Barrier
from typing import Any
from uuid import uuid4

import pytest
from fastapi import FastAPI, Header
from fastapi.testclient import TestClient
from sqlalchemy import func, select

from sketch2life.application.ports.identity import (
    IdentityAccountProfile,
    IdentityAccountProvisioningUnavailable,
    ProvisionedIdentity,
    VerifiedPrincipal,
)
from sketch2life.infrastructure.config.settings import get_core_database_settings, get_settings
from sketch2life.infrastructure.persistence.be1_models import (
    AdultIdentityModel,
    ClassroomModel,
    OrganizationAssignmentModel,
    OrganizationModel,
)
from sketch2life.interfaces.http.app import create_app
from sketch2life.interfaces.http.be1_runtime import get_verified_adult

ISSUER = "synthetic-m9b-issuer"


@dataclass
class FakeProvisioner:
    profiles: dict[str, IdentityAccountProfile] = field(default_factory=dict)
    down: bool = False

    def create_password_account(self, *, email: str, password: str) -> ProvisionedIdentity:
        raise AssertionError("not used")

    def create_account(self, *, email: str, display_name: str | None = None) -> ProvisionedIdentity:
        raise AssertionError("not used")

    def delete_account(self, subject: str) -> None:
        raise AssertionError("not used")

    def set_account_disabled(self, subject: str, disabled: bool) -> None:
        raise AssertionError("not used")

    def get_account_profiles(self, subjects: list[str]) -> dict[str, IdentityAccountProfile]:
        if self.down:
            raise IdentityAccountProvisioningUnavailable("down")
        return {subject: self.profiles[subject] for subject in subjects if subject in self.profiles}

    def find_account_by_email(self, email: str) -> ProvisionedIdentity | None:
        return None


@dataclass
class M9bApi:
    app: FastAPI
    client: TestClient
    provisioner: FakeProvisioner
    organization_id: str
    other_organization_id: str
    manager: str
    other_manager: str
    token: str

    def session(self) -> Any:
        return self.app.state.be1_runtime.session_factory


@pytest.fixture
def m9b_api(monkeypatch: pytest.MonkeyPatch) -> Iterator[M9bApi]:
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
    provisioner = FakeProvisioner()
    app = create_app(identity_account_provisioner=provisioner)
    runtime = app.state.be1_runtime
    if runtime.engine is None or runtime.session_factory is None:
        pytest.fail("PostgreSQL runtime did not initialize")
    token = uuid4().hex[:8]
    organization_id = f"synthetic-m9b-org-{token}"
    other_organization_id = f"synthetic-m9b-other-{token}"
    manager = f"synthetic-m9b-manager-{token}"
    other_manager = f"synthetic-m9b-other-manager-{token}"
    with runtime.session_factory.begin() as db:
        for org in (organization_id, other_organization_id):
            db.add(
                OrganizationModel(
                    organization_id=org, display_name=f"Synthetic {org}", state="active"
                )
            )
        for subject in (manager, other_manager):
            db.add(
                AdultIdentityModel(
                    subject=subject, issuer=ISSUER, state="active", account_role="school_manager"
                )
            )
        db.flush()
        for subject, org in ((manager, organization_id), (other_manager, other_organization_id)):
            db.add(
                OrganizationAssignmentModel(
                    assignment_id=str(uuid4()),
                    organization_id=org,
                    subject=subject,
                    class_id=None,
                    role="school_admin",
                    active=True,
                )
            )

    async def verified(
        x_test_principal: str = Header(alias="X-Test-Principal"),
    ) -> VerifiedPrincipal:
        return VerifiedPrincipal(subject=x_test_principal, issuer=ISSUER, roles=frozenset())

    app.dependency_overrides[get_verified_adult] = verified
    try:
        with TestClient(app) as client:
            yield M9bApi(
                app,
                client,
                provisioner,
                organization_id,
                other_organization_id,
                manager,
                other_manager,
                token,
            )
    finally:
        app.dependency_overrides.clear()
        runtime.engine.dispose()
        get_settings.cache_clear()
        get_core_database_settings.cache_clear()


def _h(subject: str, **extra: str) -> dict[str, str]:
    return {"X-Test-Principal": subject, **extra}


def _identity(
    api: M9bApi,
    name: str,
    *,
    role: str = "teacher",
    state: str = "active",
    rows: tuple[tuple[str, str | None], ...] = (),
    display_name: str | None = "Giáo viên",
) -> tuple[str, str]:
    """Create an identity with assignment rows ((org, class_id) pairs); return (subject, ref)."""
    subject = f"synthetic-m9b-{name}-{api.token}"
    with api.session().begin() as db:
        db.add(AdultIdentityModel(subject=subject, issuer=ISSUER, state=state, account_role=role))
        db.flush()
        for org, class_id in rows:
            db.add(
                OrganizationAssignmentModel(
                    assignment_id=str(uuid4()),
                    organization_id=org,
                    subject=subject,
                    class_id=class_id,
                    role="teacher",
                    active=True,
                )
            )
    if display_name is not None:
        api.provisioner.profiles[subject] = IdentityAccountProfile(subject, None, display_name)
    with api.session()() as db:
        ref = db.scalar(
            select(AdultIdentityModel.account_id).where(AdultIdentityModel.subject == subject)
        )
    return subject, str(ref)


def _class(api: M9bApi, name: str, organization_id: str | None = None) -> str:
    class_id = f"synthetic-m9b-class-{name}-{api.token}"
    with api.session().begin() as db:
        db.add(
            ClassroomModel(
                class_id=class_id,
                organization_id=organization_id or api.organization_id,
                display_name=f"Lớp {name}",
                state="active",
                created_by=api.manager,
            )
        )
    return class_id


def _assign(api: M9bApi, class_id: str, ref: str, revision: int | None, key: str | None) -> Any:
    headers: dict[str, str] = {}
    if revision is not None:
        headers["If-Match"] = f'"{revision}"'
    if key is not None:
        headers["Idempotency-Key"] = key
    return api.client.post(
        f"/api/be1/v1/classes/{class_id}/assignments",
        json={"candidate_ref": ref},
        headers=_h(api.manager, **headers),
    )


def _candidates(api: M9bApi, query: str = "", subject: str | None = None) -> Any:
    return api.client.get(
        f"/api/be1/v1/organizations/{api.organization_id}/teacher-candidates{query}",
        headers=_h(subject or api.manager),
    )


def test_m9b_candidates_are_same_org_active_teachers_listed_once(m9b_api: M9bApi) -> None:
    api = m9b_api
    home = _class(api, "home")
    _, twice = _identity(
        api, "twice", rows=((api.organization_id, None), (api.organization_id, home))
    )
    _, nameless = _identity(api, "nameless", rows=((api.organization_id, None),), display_name=None)
    _, foreign = _identity(api, "foreign", rows=((api.other_organization_id, None),))
    _, parent = _identity(api, "parent", role="parent", rows=((api.organization_id, None),))
    _, disabled = _identity(api, "disabled", state="disabled", rows=((api.organization_id, None),))
    _, rowless = _identity(api, "rowless")

    page = _candidates(api)
    assert page.status_code == 200, page.text
    refs = [item["candidate_ref"] for item in page.json()["items"]]
    assert refs.count(twice) == 1
    assert nameless in refs
    assert {foreign, parent, disabled, rowless}.isdisjoint(refs)
    names = {item["candidate_ref"]: item["display_name"] for item in page.json()["items"]}
    assert names[nameless] is None
    assert set(page.json()["items"][0]) == {"candidate_ref", "display_name"}
    assert page.json()["contract"] == "Be1TeacherCandidatePageV1"

    walked: list[str] = []
    cursor: str | None = None
    while True:
        response = _candidates(api, f"?limit=1{'&cursor=' + cursor if cursor else ''}")
        assert response.status_code == 200, response.text
        walked += [item["candidate_ref"] for item in response.json()["items"]]
        cursor = response.json()["next_cursor"]
        if cursor is None:
            break
    assert walked == refs
    assert _candidates(api, "?limit=101").status_code == 400
    bad = _candidates(api, "?cursor=not-a-cursor")
    assert bad.status_code == 400
    assert bad.json()["field_errors"] == [{"field": "cursor", "code": "INVALID_FORMAT"}]
    teacher_subject, _ = _identity(api, "caller", rows=((api.organization_id, None),))
    assert _candidates(api, subject=teacher_subject).status_code == 403
    assert _candidates(api, subject=api.other_manager).status_code == 404
    api.provisioner.down = True
    assert _candidates(api).status_code == 503
    api.provisioner.down = False


def test_m9b_assignment_headers_revision_replay_and_conflicts(m9b_api: M9bApi) -> None:
    api = m9b_api
    class_id = _class(api, "target")
    _, first = _identity(api, "first", rows=((api.organization_id, None),))
    _, second = _identity(api, "second", rows=((api.organization_id, None),))

    listing = api.client.get(
        f"/api/be1/v1/organizations/{api.organization_id}/classes", headers=_h(api.manager)
    )
    item = next(row for row in listing.json()["items"] if row["class_id"] == class_id)
    assert item["assignment_revision"] == 1 and item["has_active_teacher"] is False

    no_key = _assign(api, class_id, first, 1, None)
    assert no_key.status_code == 400, no_key.text
    assert {"field": "Idempotency-Key", "code": "REQUIRED"} in no_key.json()["field_errors"]
    no_match = _assign(api, class_id, first, None, f"m9b-{uuid4()}")
    assert no_match.status_code == 400
    assert no_match.json()["field_errors"] == [{"field": "If-Match", "code": "REQUIRED"}]
    malformed = api.client.post(
        f"/api/be1/v1/classes/{class_id}/assignments",
        json={"candidate_ref": first},
        headers=_h(api.manager, **{"Idempotency-Key": f"m9b-{uuid4()}", "If-Match": "W/1"}),
    )
    assert malformed.status_code == 400
    assert malformed.json()["field_errors"] == [{"field": "If-Match", "code": "INVALID_FORMAT"}]
    legacy = api.client.post(
        f"/api/be1/v1/classes/{class_id}/assignments",
        json={"subject": "synthetic-raw-subject"},
        headers=_h(api.manager, **{"Idempotency-Key": f"m9b-{uuid4()}", "If-Match": '"1"'}),
    )
    assert legacy.status_code == 400
    stale = _assign(api, class_id, first, 5, f"m9b-{uuid4()}")
    assert stale.status_code == 409, stale.text
    assert stale.json()["code"] == "STALE_REVISION"
    assert stale.json()["current_version"] == 1
    assert stale.headers["ETag"] == '"1"'

    key = f"m9b-assign-{uuid4()}"
    done = _assign(api, class_id, first, 1, key)
    assert done.status_code == 200, done.text
    assert done.json()["assignment_revision"] == 2
    assert done.headers["ETag"] == '"2"'
    listing = api.client.get(
        f"/api/be1/v1/organizations/{api.organization_id}/classes", headers=_h(api.manager)
    )
    item = next(row for row in listing.json()["items"] if row["class_id"] == class_id)
    assert item["assignment_revision"] == 2 and item["has_active_teacher"] is True
    teacher_caller, _ = _identity(api, "poster", rows=((api.organization_id, None),))
    refused = api.client.post(
        f"/api/be1/v1/classes/{class_id}/assignments",
        json={"candidate_ref": second},
        headers=_h(teacher_caller, **{"Idempotency-Key": f"m9b-{uuid4()}", "If-Match": '"2"'}),
    )
    assert refused.status_code == 403, refused.text
    assert "subject" not in done.json()
    replay = _assign(api, class_id, first, 1, key)
    assert replay.status_code == 200, replay.text
    assert replay.json() == done.json()
    other = _assign(api, class_id, second, 1, key)
    assert other.status_code == 400
    assert other.json()["code"] == "INVALID_IDEMPOTENCY_KEY"
    taken = _assign(api, class_id, second, 2, f"m9b-{uuid4()}")
    assert taken.status_code == 409
    assert taken.json()["code"] == "CLASS_TEACHER_EXISTS"
    with api.session()() as db:
        rows = db.scalar(
            select(func.count())
            .select_from(OrganizationAssignmentModel)
            .where(
                OrganizationAssignmentModel.class_id == class_id,
                OrganizationAssignmentModel.role == "teacher",
            )
        )
    assert rows == 1

    # Deactivation (for example by a Platform Admin role change) leaves the revision unchanged.
    with api.session().begin() as db:
        row = db.scalar(
            select(OrganizationAssignmentModel).where(
                OrganizationAssignmentModel.class_id == class_id,
                OrganizationAssignmentModel.role == "teacher",
            )
        )
        assert row is not None
        row.active = False
    listing = api.client.get(
        f"/api/be1/v1/organizations/{api.organization_id}/classes", headers=_h(api.manager)
    )
    item = next(row for row in listing.json()["items"] if row["class_id"] == class_id)
    assert item["assignment_revision"] == 2 and item["has_active_teacher"] is False
    # The same Teacher again: the earlier inactive row makes it a conflict (reassignment is UC-12).
    again = _assign(api, class_id, first, 2, f"m9b-{uuid4()}")
    assert again.status_code == 409, again.text
    assert again.json()["code"] == "RESOURCE_CONFLICT"
    fresh = _assign(api, class_id, second, 2, f"m9b-{uuid4()}")
    assert fresh.status_code == 200, fresh.text
    assert fresh.json()["assignment_revision"] == 3


def test_m9b_ineligible_candidates_are_404_and_create_nothing(m9b_api: M9bApi) -> None:
    api = m9b_api
    class_id = _class(api, "guarded")
    _, foreign = _identity(api, "foreign2", rows=((api.other_organization_id, None),))
    _, parent = _identity(api, "parent2", role="parent", rows=((api.organization_id, None),))
    _, disabled = _identity(api, "disabled2", state="disabled", rows=((api.organization_id, None),))
    with api.session()() as db:
        identities_before = db.scalar(select(func.count()).select_from(AdultIdentityModel))
    for ref in (foreign, parent, disabled, str(uuid4())):
        response = _assign(api, class_id, ref, 1, f"m9b-{uuid4()}")
        assert response.status_code == 404, response.text
        assert response.json()["code"] == "RESOURCE_NOT_FOUND"
    with api.session()() as db:
        assert db.scalar(select(func.count()).select_from(AdultIdentityModel)) == identities_before
        assert (
            db.scalar(
                select(func.count())
                .select_from(OrganizationAssignmentModel)
                .where(OrganizationAssignmentModel.class_id == class_id)
            )
            == 0
        )
    other_class = _class(api, "elsewhere", api.other_organization_id)
    _, mine = _identity(api, "mine", rows=((api.organization_id, None),))
    assert _assign(api, other_class, mine, 1, f"m9b-{uuid4()}").status_code == 404


def test_m9b_two_concurrent_commands_give_one_assignment(m9b_api: M9bApi) -> None:
    api = m9b_api
    class_id = _class(api, "race")
    _, first = _identity(api, "race-a", rows=((api.organization_id, None),))
    _, second = _identity(api, "race-b", rows=((api.organization_id, None),))
    gate = Barrier(2)

    def raced(target: str, ref: str, key: str) -> Any:
        gate.wait(timeout=15)
        return _assign(api, target, ref, 1, key)

    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [
            executor.submit(raced, class_id, ref, f"m9b-race-{ref}") for ref in (first, second)
        ]
        results = [future.result() for future in futures]
    assert sorted(response.status_code for response in results) == [200, 409]
    loser = next(response for response in results if response.status_code == 409)
    assert loser.json()["code"] == "STALE_REVISION"
    key = f"m9b-same-{uuid4()}"
    other_class = _class(api, "race-same")
    with ThreadPoolExecutor(max_workers=2) as executor:
        same = [
            future.result()
            for future in [executor.submit(raced, other_class, first, key) for _ in range(2)]
        ]
    assert [response.status_code for response in same] == [200, 200]
    assert same[0].json() == same[1].json()
