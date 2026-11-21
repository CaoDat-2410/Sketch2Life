"""FEAT-066 T-7c: Teacher profile create with key and expected class revision on PostgreSQL.

SRS l.543 and l.1425 (profile fields, duplicate names allowed, capacity never blocks a profile
change), l.832 and l.1095-1096 (synthetic origin carries no consent; a real row needs a valid
verified authorization that no state defines yet, X-19), l.864-865 (uniform 404, 403 only inside a
known scope), l.1651 and l.1699 (expected class revision, STALE_REVISION), l.1697 (keyed commands),
l.2586 (no child data to the School Manager). Runs only against a disposable database whose name
contains ``be1_acceptance``. Principals are injected through the ``X-Test-Principal`` header; every
identity, class and text is synthetic.

The real-data success write is parked (BLOCKED_OPEN, X-19): the real branch is a refusing gate and
is tested as such, with a pending and a revoked consent and no monkeypatch of the policy.
"""

from __future__ import annotations

import os
import re
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
from sqlalchemy.orm import Session

from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.infrastructure.config.settings import get_core_database_settings, get_settings
from sketch2life.infrastructure.persistence.be1_models import (
    AdultIdentityModel,
    Be1CommandReceiptModel,
    ClassroomModel,
    ConsentRecordModel,
    EnrollmentModel,
    ManagedProfileModel,
    OrganizationAssignmentModel,
    OrganizationModel,
)
from sketch2life.infrastructure.persistence.core_models import (
    CoreAuditEntryModel,
    CoreOutboxEventModel,
)
from sketch2life.interfaces.http.app import create_app
from sketch2life.interfaces.http.be1_runtime import get_verified_adult

ISSUER = "synthetic-t7c-issuer"
PURPOSE = "classroom-learning-v1"


@dataclass
class Api:
    app: FastAPI
    client: TestClient
    token: str
    organization: str
    foreign_organization: str
    subjects: dict[str, str] = field(default_factory=dict)

    def factory(self) -> Any:
        return self.app.state.be1_runtime.session_factory

    def settings(self) -> Any:
        return self.app.state.be1_runtime.settings


def _identity(db: Any, subject: str, role: str) -> None:
    db.add(AdultIdentityModel(subject=subject, issuer=ISSUER, state="active", account_role=role))
    db.flush()


def _assign(db: Any, organization: str, subject: str, role: str, class_id: str | None) -> None:
    db.add(
        OrganizationAssignmentModel(
            assignment_id=str(uuid4()),
            organization_id=organization,
            subject=subject,
            class_id=class_id,
            role=role,
            active=True,
        )
    )


@pytest.fixture
def api(monkeypatch: pytest.MonkeyPatch, tmp_path: Any) -> Iterator[Api]:
    database_url = os.environ.get("BE1_TEST_DATABASE_URL")
    if not database_url:
        pytest.skip("set BE1_TEST_DATABASE_URL to a disposable PostgreSQL database")
    if "be1_acceptance" not in database_url.rsplit("/", 1)[-1]:
        pytest.fail("BE1_TEST_DATABASE_URL must point to a disposable *be1_acceptance database")
    monkeypatch.setenv("SKETCH2LIFE_DATABASE_URL", database_url)
    monkeypatch.setenv("SKETCH2LIFE_ENV", "test")
    monkeypatch.setenv("SKETCH2LIFE_AUTH_PROVIDER", "development")
    monkeypatch.setenv("SKETCH2LIFE_AI_PROVIDER", "disabled")
    monkeypatch.setenv("SKETCH2LIFE_SYNTHETIC_PILOT_ENABLED", "true")
    monkeypatch.setenv("SKETCH2LIFE_ROOM_CODE_HMAC_KEY", "synthetic-test-key-" + "x" * 40)
    monkeypatch.setenv("SKETCH2LIFE_BE1_ARTIFACT_ROOT", str(tmp_path / "artifacts"))
    monkeypatch.delenv("STORYRUN_LITE_MAIN_DEMO_ENABLED", raising=False)
    get_settings.cache_clear()
    get_core_database_settings.cache_clear()
    app = create_app()
    runtime = app.state.be1_runtime
    if runtime.engine is None or runtime.session_factory is None:
        pytest.fail("PostgreSQL runtime did not initialize")
    token = uuid4().hex[:8]
    organization, foreign = f"synthetic-t7c-org-{token}", f"synthetic-t7c-foreign-{token}"
    d = Api(app, TestClient(app), token, organization, foreign)

    def label(value: str) -> str:
        return f"synthetic-t7c-{value}-{token}"

    with runtime.session_factory.begin() as db:
        for org in (organization, foreign):
            db.add(OrganizationModel(organization_id=org, display_name=org, state="active"))
        db.flush()
        people: tuple[tuple[str, str, str | None, str | None], ...] = (
            ("manager", "school_manager", organization, "school_admin"),
            ("orgt", "teacher", organization, "teacher"),  # an organization-wide Teacher row
            ("parent", "parent", None, None),
            ("platform", "platform_admin", None, None),
            ("fteacher", "teacher", foreign, "teacher"),  # a Teacher of another organization
        )
        for key, role, home, assignment_role in people:
            d.subjects[key] = label(key)
            _identity(db, label(key), role)
            if home is not None and assignment_role is not None:
                _assign(db, home, label(key), assignment_role, None)

    async def verified(
        x_test_principal: str = Header(alias="X-Test-Principal"),
    ) -> VerifiedPrincipal:
        return VerifiedPrincipal(subject=x_test_principal, issuer=ISSUER, roles=frozenset())

    app.dependency_overrides[get_verified_adult] = verified
    try:
        with d.client:
            yield d
    finally:
        app.dependency_overrides.clear()
        runtime.engine.dispose()
        get_settings.cache_clear()
        get_core_database_settings.cache_clear()


# ----------------------------------------------------------------------------- helpers
def new_class(d: Api, *, state: str = "active", organization: str | None = None) -> str:
    class_id = f"synthetic-t7c-class-{uuid4().hex[:12]}"
    with d.factory().begin() as db:
        db.add(
            ClassroomModel(
                class_id=class_id,
                organization_id=organization or d.organization,
                display_name=f"Synthetic {class_id}"[:200],
                state=state,
                created_by="synthetic-t7c-seed",
            )
        )
    return class_id


def add_adult(
    d: Api, key: str, class_id: str, *, role: str = "teacher", organization: str | None = None
) -> None:
    subject = f"synthetic-t7c-{key}-{d.token}"
    d.subjects[key] = subject
    with d.factory().begin() as db:
        _identity(db, subject, "teacher")
        _assign(db, organization or d.organization, subject, role, class_id)


def url(d: Api, class_id: str, organization: str | None = None) -> str:
    return f"/api/be1/v1/organizations/{organization or d.organization}/classes/{class_id}/profiles"


def post(
    d: Api,
    who: str,
    class_id: str,
    *,
    key: str | None = None,
    if_match: str | None = '"1"',
    organization: str | None = None,
    body: dict[str, Any] | None = None,
    **headers: str,
) -> Any:
    request_headers = {"X-Test-Principal": d.subjects[who]}
    request_headers["Idempotency-Key"] = uuid4().hex if key is None else key
    if if_match is not None:
        request_headers["If-Match"] = if_match
    request_headers.update(headers)
    return d.client.post(
        url(d, class_id, organization),
        json={"display_name": "Synthetic Learner", "age_months": 60} if body is None else body,
        headers=request_headers,
    )


def shape(response: Any) -> tuple[int, dict[str, Any]]:
    body = dict(response.json())
    body.pop("request_id", None)
    body.pop("correlation_id", None)
    return response.status_code, body


def class_revision(d: Api, class_id: str) -> int:
    with d.factory()() as db:
        return int(
            db.scalar(select(ClassroomModel.revision).where(ClassroomModel.class_id == class_id))
            or 0
        )


def set_class(d: Api, class_id: str, **values: Any) -> None:
    with d.factory().begin() as db:
        row = db.get(ClassroomModel, class_id)
        assert row is not None
        for name, value in values.items():
            setattr(row, name, value)


def count(d: Api, model: Any, *where: Any) -> int:
    with d.factory()() as db:
        return int(db.scalar(select(func.count()).select_from(model).where(*where)) or 0)


def profile_count(d: Api, class_id: str) -> int:
    return count(d, ManagedProfileModel, ManagedProfileModel.class_id == class_id)


def audit_count(d: Api, action: str, decision: str, resource_id: str | None = None) -> int:
    clauses = [
        CoreAuditEntryModel.organization_id == d.organization,
        CoreAuditEntryModel.action == action,
        CoreAuditEntryModel.decision == decision,
    ]
    if resource_id is not None:
        clauses.append(CoreAuditEntryModel.resource_id == resource_id)
    return count(d, CoreAuditEntryModel, *clauses)


def pending_consent(d: Api, class_id: str, *, state: str = "pending") -> str:
    consent_id = str(uuid4())
    with d.factory().begin() as db:
        db.add(
            ConsentRecordModel(
                consent_id=consent_id,
                organization_id=d.organization,
                class_id=class_id,
                child_id=f"synthetic-client-chosen-{uuid4().hex[:8]}",
                purpose_ref=PURPOSE,
                state=state,
                recorded_by="synthetic-t7c-seed",
            )
        )
    return consent_id


# ----------------------------------------------------------------------------- the create
def test_create_writes_the_profile_the_enrollment_and_a_reference_only_receipt(api: Api) -> None:
    d = api
    class_id = new_class(d)
    add_adult(d, "t1", class_id)
    key = f"t7c-{uuid4().hex}"
    response = post(d, "t1", class_id, key=key)
    assert response.status_code == 201, response.text
    body = response.json()
    assert response.headers["ETag"] == '"1"'
    assert set(body) == {
        "contract",
        "child_id",
        "class_id",
        "enrollment_id",
        "display_name",
        "age_months",
        "data_origin",
        "class_revision",
    }
    assert body["contract"] == "Be1ManagedProfileV1"
    assert re.fullmatch(r"synthetic-[0-9a-f]{24}", body["child_id"])
    assert (body["class_id"], body["age_months"], body["class_revision"]) == (class_id, 60, 1)
    assert body["data_origin"] == "SYNTHETIC_DEV"
    with d.factory()() as db:
        profile = db.get(ManagedProfileModel, body["child_id"])
        assert profile is not None
        assert (profile.data_origin, profile.age_source, profile.age_revision) == (
            "SYNTHETIC_DEV",
            "SYNTHETIC_FIXTURE",
            1,
        )
        assert profile.consent_id is None and profile.consent_purpose_ref is None
        assert (profile.state, profile.age_months, profile.class_id) == ("active", 60, class_id)
        enrollment = db.get(EnrollmentModel, body["enrollment_id"])
        assert enrollment is not None
        assert (enrollment.child_id, enrollment.class_id, enrollment.state) == (
            body["child_id"],
            class_id,
            "active",
        )
        receipts = db.scalars(
            select(Be1CommandReceiptModel).where(Be1CommandReceiptModel.idempotency_key == key)
        ).all()
        assert len(receipts) == 1
        stored = dict(receipts[0].response_json)
        key_id = stored.pop("fp_kid")  # T-7c-fix: format version and key id, no secret, no name
        assert re.fullmatch(r"[0-9a-f]{8}", str(key_id))
        assert stored == {
            "child_id": body["child_id"],
            "enrollment_id": body["enrollment_id"],
            "class_revision": 1,
            "data_origin": "SYNTHETIC_DEV",
            "fp_v": 2,
        }
        assert "Synthetic Learner" not in str(stored)
        assert receipts[0].operation_scope == (
            f"POST /organizations/{d.organization}/classes/{class_id}/profiles"
        )
    assert class_revision(d, class_id) == 1  # create does not bump (T-7c-DEC-2)
    assert audit_count(d, "profile.enroll", "allowed", body["child_id"]) == 1
    assert (
        count(
            d,
            CoreOutboxEventModel,
            CoreOutboxEventModel.aggregate_id == body["child_id"],
            CoreOutboxEventModel.event_type == "be1.profile.enrolled.v1",
        )
        == 1
    )


def test_replay_returns_the_stored_result_and_one_profile_row(api: Api) -> None:
    d = api
    class_id = new_class(d)
    add_adult(d, "t1", class_id)
    key = f"t7c-{uuid4().hex}"
    first = post(d, "t1", class_id, key=key)
    replay = post(d, "t1", class_id, key=key)
    assert replay.status_code == 201, replay.text
    assert replay.content == first.content
    assert replay.headers["ETag"] == '"1"'
    assert profile_count(d, class_id) == 1
    assert count(d, EnrollmentModel, EnrollmentModel.class_id == class_id) == 1
    # The class moves on and is suspended: the same key and request still replay the stored answer.
    set_class(d, class_id, revision=4, state="suspended")
    late = post(d, "t1", class_id, key=key)
    assert late.status_code == 201 and late.content == first.content
    assert profile_count(d, class_id) == 1


def test_a_replay_by_a_teacher_whose_class_row_was_revoked_is_404(api: Api) -> None:
    # Review F-07a: the scope check runs before the key and the receipt, so a revoked Teacher
    # cannot read the stored answer back.
    d = api
    class_id = new_class(d)
    add_adult(d, "t1", class_id)
    key = f"t7c-{uuid4().hex}"
    assert post(d, "t1", class_id, key=key).status_code == 201
    with d.factory().begin() as db:
        rows = db.scalars(
            select(OrganizationAssignmentModel).where(
                OrganizationAssignmentModel.subject == d.subjects["t1"],
                OrganizationAssignmentModel.class_id == class_id,
            )
        ).all()
        assert len(rows) == 1
        rows[0].active = False
    status, body = shape(post(d, "t1", class_id, key=key))
    assert status == 404
    assert body["code"] == "RESOURCE_NOT_FOUND"
    assert profile_count(d, class_id) == 1


def test_the_same_key_with_another_request_is_400_invalid_idempotency_key(api: Api) -> None:
    d = api
    class_id = new_class(d)
    add_adult(d, "t1", class_id)
    key = f"t7c-{uuid4().hex}"
    assert post(d, "t1", class_id, key=key).status_code == 201
    for kwargs in (
        {"body": {"display_name": "Synthetic Other", "age_months": 60}},
        {"body": {"display_name": "Synthetic Learner", "age_months": 61}},
        {"if_match": '"2"'},
    ):
        other = post(d, "t1", class_id, key=key, **kwargs)
        assert other.status_code == 400, other.text
        assert other.json()["code"] == "INVALID_IDEMPOTENCY_KEY"
    assert profile_count(d, class_id) == 1
    # The same key in another class is a new command (scope), not a replay.
    other_class = new_class(d)
    add_adult(d, "t1b", other_class)
    assert post(d, "t1b", other_class, key=key).status_code == 201


def test_twenty_concurrent_creates_with_one_revision_all_succeed(api: Api) -> None:
    d = api
    class_id = new_class(d)
    add_adult(d, "t1", class_id)
    barrier = Barrier(20)

    def create(index: int) -> Any:
        barrier.wait(timeout=30)
        return post(
            d,
            "t1",
            class_id,
            key=f"t7c-bulk-{index}-{uuid4().hex}",
            body={"display_name": f"Synthetic Learner {index}", "age_months": 36 + index},
        )

    with ThreadPoolExecutor(max_workers=20) as executor:
        futures = [executor.submit(create, index) for index in range(20)]
        responses = [future.result(timeout=90) for future in futures]
    assert [response.status_code for response in responses] == [201] * 20
    assert len({response.json()["child_id"] for response in responses}) == 20
    assert profile_count(d, class_id) == 20
    assert count(d, EnrollmentModel, EnrollmentModel.class_id == class_id) == 20
    assert class_revision(d, class_id) == 1


def test_concurrent_requests_with_the_same_key_make_one_profile(api: Api) -> None:
    d = api
    class_id = new_class(d)
    add_adult(d, "t1", class_id)
    key = f"t7c-same-{uuid4().hex}"
    barrier = Barrier(6)

    def create() -> Any:
        barrier.wait(timeout=30)
        return post(d, "t1", class_id, key=key)

    with ThreadPoolExecutor(max_workers=6) as executor:
        futures = [executor.submit(create) for _ in range(6)]
        responses = [future.result(timeout=60) for future in futures]
    assert [response.status_code for response in responses] == [201] * 6
    assert len({response.json()["child_id"] for response in responses}) == 1
    assert len({response.content for response in responses}) == 1
    assert profile_count(d, class_id) == 1
    assert (
        count(d, Be1CommandReceiptModel, Be1CommandReceiptModel.idempotency_key == key) == 1
    )


def _hide_receipt_lookup(monkeypatch: pytest.MonkeyPatch, *, times: int) -> list[int]:
    original = Session.get
    state = [0]

    def get(self: Session, entity: Any, ident: Any, *args: Any, **kwargs: Any) -> Any:
        if entity is Be1CommandReceiptModel and state[0] < times:
            state[0] += 1
            return None
        return original(self, entity, ident, *args, **kwargs)

    monkeypatch.setattr(Session, "get", get)
    return state


def test_a_lost_receipt_race_replays_and_rolls_the_loser_back(
    api: Api, monkeypatch: pytest.MonkeyPatch
) -> None:
    d = api
    class_id = new_class(d)
    add_adult(d, "t1", class_id)
    key = f"t7c-{uuid4().hex}"
    first = post(d, "t1", class_id, key=key)
    calls = _hide_receipt_lookup(monkeypatch, times=1)
    loser = post(d, "t1", class_id, key=key)
    assert calls == [1]  # the first lookup missed, so the IntegrityError branch ran
    assert loser.status_code == 201, loser.text
    assert loser.content == first.content
    assert profile_count(d, class_id) == 1
    assert count(d, EnrollmentModel, EnrollmentModel.class_id == class_id) == 1
    assert audit_count(d, "profile.enroll", "allowed") == 1  # the loser's rows rolled back
    _hide_receipt_lookup(monkeypatch, times=2)  # the lookup and the re-read both miss
    conflict = post(d, "t1", class_id, key=key)
    assert conflict.status_code == 409 and conflict.json()["code"] == "RESOURCE_CONFLICT"
    assert profile_count(d, class_id) == 1


# ----------------------------------------------------------------------------- revision and state
def test_stale_revision_is_409_with_the_current_version_and_an_etag(api: Api) -> None:
    d = api
    class_id = new_class(d)
    add_adult(d, "t1", class_id)
    set_class(d, class_id, revision=3)
    stale = post(d, "t1", class_id, if_match='"1"')
    assert stale.status_code == 409, stale.text
    assert stale.json()["code"] == "STALE_REVISION"
    assert stale.json()["current_version"] == 3
    assert stale.headers["ETag"] == '"3"'
    assert profile_count(d, class_id) == 0
    assert post(d, "t1", class_id, if_match='"3"').status_code == 201
    assert class_revision(d, class_id) == 3


def test_a_suspension_makes_the_old_revision_stale_then_the_class_is_read_only(api: Api) -> None:
    d = api
    class_id = new_class(d)
    add_adult(d, "t1", class_id)
    manager = post_manager_suspend(d, class_id)
    assert manager.status_code == 200, manager.text
    assert manager.json()["class_revision"] == 2
    stale = post(d, "t1", class_id, if_match='"1"')
    assert stale.status_code == 409 and stale.json()["code"] == "STALE_REVISION"
    assert stale.json()["current_version"] == 2
    refused = post(d, "t1", class_id, if_match='"2"')
    assert refused.status_code == 409, refused.text
    assert refused.json()["code"] == "INVALID_STATE_TRANSITION"
    assert profile_count(d, class_id) == 0
    set_class(d, class_id, state="archived")
    archived = post(d, "t1", class_id, if_match='"2"')
    assert archived.status_code == 409 and archived.json()["code"] == "INVALID_STATE_TRANSITION"


def post_manager_suspend(d: Api, class_id: str) -> Any:
    return d.client.post(
        f"/api/be1/v1/classes/{class_id}/suspend",
        headers={
            "X-Test-Principal": d.subjects["manager"],
            "Idempotency-Key": uuid4().hex,
            "If-Match": '"1"',
        },
    )


def test_missing_or_malformed_headers_are_400(api: Api) -> None:
    d = api
    class_id = new_class(d)
    add_adult(d, "t1", class_id)
    no_match = post(d, "t1", class_id, if_match=None)
    assert no_match.status_code == 400
    assert no_match.json()["field_errors"] == [{"field": "If-Match", "code": "REQUIRED"}]
    for value in ("1", 'W/"1"', '"0"', '"x"'):
        bad = post(d, "t1", class_id, if_match=value)
        assert bad.status_code == 400, value
        assert bad.json()["field_errors"] == [{"field": "If-Match", "code": "INVALID_FORMAT"}]
    for key in ("", "has space", "k" * 129):
        assert post(d, "t1", class_id, key=key).status_code == 400, key
    no_key = d.client.post(
        url(d, class_id),
        json={"display_name": "Synthetic Learner", "age_months": 60},
        headers={"X-Test-Principal": d.subjects["t1"], "If-Match": '"1"'},
    )
    assert no_key.status_code == 400
    assert profile_count(d, class_id) == 0


# ----------------------------------------------------------------------------- scope and roles
def test_the_manager_is_403_and_the_answer_carries_no_child_data(api: Api) -> None:
    d = api
    class_id = new_class(d)
    add_adult(d, "t1", class_id)
    refused = post(d, "manager", class_id)
    assert refused.status_code == 403, refused.text
    assert refused.json()["code"] == "ACTION_NOT_ALLOWED"
    assert "Synthetic Learner" not in refused.text and "display_name" not in refused.text
    assert profile_count(d, class_id) == 0


def test_every_out_of_scope_caller_gets_one_404_body(api: Api) -> None:
    d = api
    class_id = new_class(d)
    add_adult(d, "t1", class_id)
    other_class = new_class(d)
    add_adult(d, "other_class_teacher", other_class)
    foreign_class = new_class(d, organization=d.foreign_organization)
    attempts = {
        "org-wide teacher": post(d, "orgt", class_id),
        "teacher of another class": post(d, "other_class_teacher", class_id),
        "teacher of another organization": post(d, "fteacher", class_id),
        "unknown class": post(d, "t1", f"synthetic-t7c-missing-{uuid4().hex[:8]}"),
        "class of another organization": post(d, "t1", foreign_class),
        "wrong organization in the path": post(d, "t1", class_id, organization="nowhere"),
        "parent": post(d, "parent", class_id),
        "platform admin": post(d, "platform", class_id),
    }
    shapes = {name: shape(response) for name, response in attempts.items()}
    for name, (status_code, _body) in shapes.items():
        assert status_code == 404, name
    assert len({str(body) for _status, body in shapes.values()}) == 1
    assert next(iter(shapes.values()))[1]["code"] == "RESOURCE_NOT_FOUND"
    assert profile_count(d, class_id) == 0


@pytest.mark.parametrize("role", ["guide", "observer"])
def test_a_guide_or_observer_row_is_refused_with_403(api: Api, role: str) -> None:
    d = api
    class_id = new_class(d)
    add_adult(d, "other_role", class_id, role=role)
    refused = post(d, "other_role", class_id)
    assert refused.status_code == 403, refused.text
    assert refused.json()["code"] == "ACTION_NOT_ALLOWED"
    assert profile_count(d, class_id) == 0


# ----------------------------------------------------------------------------- body rules
def test_body_rules_names_ages_and_client_fields(api: Api) -> None:
    d = api
    class_id = new_class(d)
    add_adult(d, "t1", class_id)

    def body(**overrides: Any) -> dict[str, Any]:
        return {"display_name": "Synthetic Learner", "age_months": 60, **overrides}

    for extra in ("class_id", "child_id", "purpose_ref", "data_origin", "enrollment_id"):
        rejected = post(d, "t1", class_id, body=body(**{extra: "client-value"}))
        assert rejected.status_code == 400, extra
        assert rejected.json()["code"] == "INVALID_REQUEST"
        # The envelope names no unknown field (it never echoes client-chosen names).
        assert rejected.json()["field_errors"] == [{"field": "<unknown>", "code": "UNKNOWN_FIELD"}]
    for age in (35, 121):
        assert post(d, "t1", class_id, body=body(age_months=age)).status_code == 400
    for name in ("Real Child", "Synthetic", "synthetic lower", ""):
        refused = post(d, "t1", class_id, body=body(display_name=name))
        assert refused.status_code == 400, name
        assert refused.json()["code"] == "INVALID_REQUEST"
    assert profile_count(d, class_id) == 0
    for age in (36, 120):
        assert post(d, "t1", class_id, body=body(age_months=age)).status_code == 201
    # Duplicate names are allowed (SRS l.543, l.1425): the same name and age under new keys.
    first = post(d, "t1", class_id)
    second = post(d, "t1", class_id)
    assert first.status_code == second.status_code == 201
    assert first.json()["child_id"] != second.json()["child_id"]
    assert profile_count(d, class_id) == 4


def test_the_synthetic_name_rule_holds_with_real_data_on(
    api: Api, monkeypatch: pytest.MonkeyPatch
) -> None:
    d = api
    class_id = new_class(d)
    add_adult(d, "t1", class_id)
    monkeypatch.setattr(d.settings(), "real_profile_data_enabled", True)
    # No consent_id, pilot on: the row written is SYNTHETIC_DEV, so a real-looking name is refused.
    refused = post(d, "t1", class_id, body={"display_name": "Nguyen Van A", "age_months": 60})
    assert refused.status_code == 400
    ok = post(d, "t1", class_id)
    assert ok.status_code == 201 and ok.json()["data_origin"] == "SYNTHETIC_DEV"
    assert profile_count(d, class_id) == 1


# ----------------------------------------------------------------------------- the config gate
def test_pilot_off_is_409_after_authorization_and_a_stranger_never_learns_it(
    api: Api, monkeypatch: pytest.MonkeyPatch
) -> None:
    d = api
    class_id = new_class(d)
    add_adult(d, "t1", class_id)
    monkeypatch.setattr(d.settings(), "synthetic_pilot_enabled", False)
    unavailable = post(d, "t1", class_id)
    assert unavailable.status_code == 409
    assert unavailable.json()["code"] == "SYNTHETIC_PROFILE_CREATION_UNAVAILABLE"
    stranger = post(d, "fteacher", class_id)
    assert stranger.status_code == 404  # not the pilot flag
    manager = post(d, "manager", class_id)
    assert manager.status_code == 403
    assert profile_count(d, class_id) == 0
    # With real data on and no consent_id the create has no valid origin: 400 REQUIRED consent_id.
    monkeypatch.setattr(d.settings(), "real_profile_data_enabled", True)
    required = post(d, "t1", class_id)
    assert required.status_code == 400
    assert required.json()["field_errors"] == [{"field": "consent_id", "code": "REQUIRED"}]


def test_consent_id_is_refused_while_real_data_is_off(api: Api) -> None:
    d = api
    class_id = new_class(d)
    add_adult(d, "t1", class_id)
    consent_id = pending_consent(d, class_id)
    refused = post(
        d,
        "t1",
        class_id,
        body={"display_name": "Synthetic Learner", "age_months": 60, "consent_id": consent_id},
    )
    assert refused.status_code == 400, refused.text
    assert refused.json()["field_errors"] == [{"field": "consent_id", "code": "UNKNOWN_FIELD"}]
    assert profile_count(d, class_id) == 0
    assert audit_count(d, "profile.enroll", "denied_consent_pending") == 0


@pytest.mark.parametrize("state", ["pending", "revoked"])
def test_the_real_gate_refuses_and_writes_no_profile(
    api: Api, monkeypatch: pytest.MonkeyPatch, state: str
) -> None:
    d = api
    class_id = new_class(d)
    add_adult(d, "t1", class_id)
    consent_id = pending_consent(d, class_id, state=state)
    monkeypatch.setattr(d.settings(), "real_profile_data_enabled", True)
    refused = post(
        d,
        "t1",
        class_id,
        body={"display_name": "Synthetic Learner", "age_months": 60, "consent_id": consent_id},
    )
    assert refused.status_code == 409, refused.text
    assert refused.json()["code"] == "CONSENT_NOT_EFFECTIVE"
    assert profile_count(d, class_id) == 0
    assert count(d, EnrollmentModel, EnrollmentModel.class_id == class_id) == 0
    # The client-chosen child_id of the consent row is never turned into a profile.
    assert count(d, ManagedProfileModel, ManagedProfileModel.organization_id == d.organization) == 0
    assert audit_count(d, "profile.enroll", "denied_consent_pending", consent_id) == 1
    assert (
        count(d, Be1CommandReceiptModel, Be1CommandReceiptModel.organization_id == d.organization)
        == 0
    )
    assert class_revision(d, class_id) == 1


def test_the_real_gate_for_a_consent_of_another_class_or_none_is_404(
    api: Api, monkeypatch: pytest.MonkeyPatch
) -> None:
    d = api
    class_id = new_class(d)
    other_class = new_class(d)
    add_adult(d, "t1", class_id)
    monkeypatch.setattr(d.settings(), "real_profile_data_enabled", True)
    for consent_id in (pending_consent(d, other_class), str(uuid4())):
        missing = post(
            d,
            "t1",
            class_id,
            body={"display_name": "Synthetic Learner", "age_months": 60, "consent_id": consent_id},
        )
        assert missing.status_code == 404, missing.text
        assert missing.json()["code"] == "RESOURCE_NOT_FOUND"
    assert profile_count(d, class_id) == 0


def test_the_real_gate_still_checks_the_revision_and_the_state_first(
    api: Api, monkeypatch: pytest.MonkeyPatch
) -> None:
    d = api
    class_id = new_class(d)
    add_adult(d, "t1", class_id)
    consent_id = pending_consent(d, class_id)
    monkeypatch.setattr(d.settings(), "real_profile_data_enabled", True)
    body = {"display_name": "Synthetic Learner", "age_months": 60, "consent_id": consent_id}
    stale = post(d, "t1", class_id, body=body, if_match='"9"')
    assert stale.status_code == 409 and stale.json()["code"] == "STALE_REVISION"
    set_class(d, class_id, state="suspended")
    read_only = post(d, "t1", class_id, body=body)
    assert read_only.json()["code"] == "INVALID_STATE_TRANSITION"
    assert audit_count(d, "profile.enroll", "denied_consent_pending") == 0
